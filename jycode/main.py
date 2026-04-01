import numpy as np
import cv2
from astropy.io import fits
from astropy.wcs import WCS
from astropy.stats import sigma_clipped_stats
from astropy.time import Time
from astropy.convolution import convolve, Gaussian2DKernel
from skimage.transform import radon, iradon
from tkinter import Tk, filedialog
import os
import requests
import time
import tempfile

# ASTRiDE 샘플 이미지 로드 (테스트용)
try:
    from astride.datasets import load_long
    ASTRIDE_SAMPLE = load_long()
except ImportError:
    ASTRIDE_SAMPLE = None

# =====================================================
# IDLE에서 여기만 수정하면 됩니다
# MODE = "sample"  -> ASTRiDE 샘플 이미지로 테스트
# MODE = "file"    -> 파일 탐색기로 직접 선택
MODE = "file"
# 샘플 모드일 때 노출 시간 (초)
SAMPLE_EXPOSURE_TIME = 60.0

# --- streak 검출 파라미터 ---
# 별 streak 방향 (도, 0~180). None이면 WCS로 자동 추정
STAR_ANGLE_MANUAL = 152.0
# 별 방향 마스킹 범위 ± (도). 넓힐수록 별 제거 강함
STAR_ANGLE_TOL = 30.0
# Radon threshold (낮을수록 희미한 streak 검출, 노이즈 증가)
RADON_THRESHOLD_SIGMA = 2.0
# 최소 streak 길이 (이미지 대각선 대비 비율)
MIN_LENGTH_FRAC = 0.03
# 최종 반환할 위성 후보 최대 개수
MAX_SATELLITE_STREAKS = 5
# 별 방향 자동 감지: STAR_ANGLE_MANUAL = None 으로 설정
# =====================================================


# =========================
# 파일 선택 (GUI)
# =========================
def select_fits_files():
    """
    파일 탐색기를 열어 FITS 파일을 복수 선택한다.
    선택된 파일은 파일명(시간) 순으로 정렬된다.
    """
    root = Tk()
    root.withdraw()
    files = filedialog.askopenfilenames(
        title="FITS 파일 선택 (시간 순서대로 선택)",
        filetypes=[("FITS files", "*.fits *.fit *.fts"), ("All files", "*.*")]
    )
    root.destroy()

    if not files:
        raise ValueError("파일이 선택되지 않았습니다.")

    # 파일명 기준 정렬 (시간 순서 가정)
    return sorted(list(files), key=os.path.basename)


# =========================
# FITS 처리
# =========================
def load_fits(file_path: str):
    with fits.open(file_path) as hdul:
        data = hdul[0].data.astype(np.float32)
        header = hdul[0].header
    return data, header


def get_wcs(header):
    wcs = WCS(header)
    if not wcs.has_celestial:
        raise ValueError("WCS 정보가 없거나 불완전합니다.")
    return wcs


# =========================
# Astrometry.net Plate Solving
# =========================
ASTROMETRY_API_URL = "https://nova.astrometry.net/api/"

def astrometry_login(api_key: str) -> str:
    """API 키로 로그인 후 session key 반환"""
    r = requests.post(
        ASTROMETRY_API_URL + "login",
        data={"request-json": f'{{"apikey": "{api_key}"}}'}
    )
    r.raise_for_status()
    result = r.json()
    if result.get("status") != "success":
        raise ValueError(f"Astrometry.net 로그인 실패: {result}")
    return result["session"]


def astrometry_upload(session: str, fits_path: str) -> int:
    """FITS 파일 업로드 후 submission ID 반환"""
    with open(fits_path, "rb") as f:
        r = requests.post(
            ASTROMETRY_API_URL + "upload",
            files={"file": f},
            data={"request-json": f'{{"session": "{session}", "allow_commercial_use": "n", "publicly_visible": "n"}}'}
        )
    r.raise_for_status()
    result = r.json()
    if result.get("status") != "success":
        raise ValueError(f"업로드 실패: {result}")
    return result["subid"]


def astrometry_wait_for_job(subid: int, timeout: int = 300) -> int:
    """submission이 완료될 때까지 대기 후 job ID 반환"""
    print(f"  Plate solving 대기 중 (submission {subid})...", end="", flush=True)
    start = time.time()
    while time.time() - start < timeout:
        r = requests.get(ASTROMETRY_API_URL + f"submissions/{subid}")
        r.raise_for_status()
        data = r.json()
        jobs = data.get("jobs", [])
        if jobs and jobs[0] is not None:
            job_id = jobs[0]
            # job 상태 확인
            jr = requests.get(ASTROMETRY_API_URL + f"jobs/{job_id}")
            jr.raise_for_status()
            status = jr.json().get("status")
            if status == "success":
                print(" 완료!")
                return job_id
            elif status == "failure":
                raise ValueError(f"Plate solving 실패 (job {job_id})")
        print(".", end="", flush=True)
        time.sleep(5)
    raise TimeoutError(f"Plate solving 시간 초과 ({timeout}초)")


def astrometry_get_wcs(job_id: int) -> WCS:
    """job ID로부터 WCS FITS 헤더 다운로드 후 WCS 반환"""
    r = requests.get(f"https://nova.astrometry.net/wcs_file/{job_id}")
    r.raise_for_status()

    with tempfile.NamedTemporaryFile(suffix=".fits", delete=False) as tmp:
        tmp.write(r.content)
        tmp_path = tmp.name

    with fits.open(tmp_path) as hdul:
        wcs_header = hdul[0].header
    os.unlink(tmp_path)

    return WCS(wcs_header)


def plate_solve(fits_path: str, api_key: str) -> WCS:
    """
    Astrometry.net API로 plate solving 수행 후 WCS 반환.
    ASIAIR WCS가 불완전할 때 이 함수로 대체한다.
    """
    print(f"  [{os.path.basename(fits_path)}] Plate solving 시작...")
    session = astrometry_login(api_key)
    subid = astrometry_upload(session, fits_path)
    job_id = astrometry_wait_for_job(subid)
    wcs = astrometry_get_wcs(job_id)
    return wcs


def get_timestamp(header):
    """
    FITS 헤더에서 관측 시각(UTC)을 읽는다.
    DATE-OBS, DATE_OBS, MJD-OBS 순으로 시도한다.
    """
    for key in ["DATE-OBS", "DATE_OBS"]:
        if key in header:
            return Time(header[key], format="isot", scale="utc")
    if "MJD-OBS" in header:
        return Time(header["MJD-OBS"], format="mjd", scale="utc")
    raise ValueError("FITS 헤더에서 관측 시각을 찾을 수 없습니다. (DATE-OBS, MJD-OBS 없음)")


# =========================
# 전처리
# =========================
def preprocess_image(image_data):

    image = np.nan_to_num(image_data)

    # Background 제거
    _, median, _ = sigma_clipped_stats(image)
    image = image - median

    # 정규화
    image = image - np.min(image)
    if np.max(image) != 0:
        image = image / np.max(image)

    image = (image * 255).astype(np.uint8)

    # Blur
    image = cv2.GaussianBlur(image, (5, 5), 0)

    return image


# =========================
# 별 streak 방향 추정
# =========================
def estimate_star_streak_angle(wcs, image_shape):
    """
    일주운동 방향을 WCS 기반으로 추정한다.
    적경 방향(RA 증가 방향)이 이미지에서 어느 각도인지 계산.

    Returns:
        angle_deg: 이미지 좌표계 기준 별 streak 방향 (도, 0~180)
    """
    h, w = image_shape
    cx, cy = w / 2, h / 2

    # 중심과 RA +1도 위치의 픽셀 차이로 방향 추정
    try:
        from astropy.coordinates import SkyCoord
        import astropy.units as u
        center_sky = wcs.pixel_to_world(cx, cy)
        ra0, dec0 = center_sky.ra.deg, center_sky.dec.deg
        shifted = SkyCoord(ra=ra0 + 1.0, dec=dec0, unit=u.deg)
        px, py = wcs.world_to_pixel(shifted)
        angle = np.degrees(np.arctan2(py - cy, px - cx)) % 180
        return angle
    except Exception:
        # WCS 실패 시 수평 방향(0도) 기본값
        return 0.0


# =========================
# Radon 기반 streak 검출 (자동 별 방향 제거)
# =========================
def detect_streaks_radon(image_data, wcs=None,
                          star_angle_manual=None,
                          star_angle_tol=30.0,
                          min_length_frac=0.03,
                          radon_threshold_sigma=2.0,
                          max_satellite_streaks=5):
    """
    Radon Transform으로 streak을 검출한다.
    1. 각도 히스토그램으로 별 streak 방향을 자동 감지하여 제거
    2. 남은 streak 중 긴 것만 위성 후보로 반환

    Parameters:
        image_data            : 원본 float32 이미지
        wcs                   : WCS 객체 (별 방향 추정용, 없으면 자동)
        star_angle_manual     : 별 방향 수동 지정 (None이면 자동)
        star_angle_tol        : 별 방향 마스킹 범위 ± (도)
        min_length_frac       : 최소 streak 길이 (대각선 대비)
        radon_threshold_sigma : 검출 임계값 (sigma 배수)
        max_satellite_streaks : 최종 반환할 위성 후보 최대 개수

    Returns:
        list of (x1, y1, x2, y2, length_px)
    """
    image = np.nan_to_num(image_data).astype(np.float32)

    # 2D 배경 제거 (gradient 보정)
    _, median, std = sigma_clipped_stats(image)
    blur = cv2.GaussianBlur(image, (101, 101), 0)
    image = image - blur
    image = np.clip(image, 0, None)

    h, w = image.shape
    diag = np.sqrt(h**2 + w**2)
    min_length_px = diag * min_length_frac

    # --- Radon Transform ---
    theta = np.arange(0, 180, 1.0)
    sinogram = radon(image, theta=theta, circle=False)

    # --- 1단계: 별 방향 자동 감지 ---
    if star_angle_manual is not None:
        star_angle = star_angle_manual
        print(f"  별 streak 수동 설정: {star_angle:.1f}°")
    else:
        # 각도별 sinogram 합계 → 가장 강한 방향 = 별 streak
        angle_sum = np.sum(sinogram, axis=0)
        star_angle_idx = np.argmax(angle_sum)
        star_angle = theta[star_angle_idx]
        print(f"  별 streak 자동 감지: {star_angle:.1f}° (sinogram 합계 최대)")

    # --- 2단계: 별 방향 마스킹 ---
    mask = np.abs(theta - star_angle) < star_angle_tol
    mask |= np.abs(theta - star_angle + 180) < star_angle_tol
    mask |= np.abs(theta - star_angle - 180) < star_angle_tol
    sinogram_masked = sinogram.copy()
    sinogram_masked[:, mask] = 0
    print(f"  마스킹 범위: {star_angle - star_angle_tol:.0f}~{star_angle + star_angle_tol:.0f}도")

    # --- 3단계: 마스킹 후 남은 신호에서 peak 검출 ---
    valid = sinogram_masked[sinogram_masked > 0]
    if len(valid) == 0:
        print("  마스킹 후 신호 없음")
        return []

    sino_mean = np.mean(valid)
    sino_std  = np.std(valid)
    threshold = sino_mean + radon_threshold_sigma * sino_std
    print(f"  검출 임계값: {threshold:.1f} (mean={sino_mean:.1f}, std={sino_std:.1f})")

    peaks = np.argwhere(sinogram_masked > threshold)
    print(f"  원시 peak 수: {len(peaks)}")
    if len(peaks) == 0:
        return []

    # --- 4단계: peak 클러스터링 ---
    peaks_clustered = cluster_radon_peaks(peaks, sinogram_masked, radius=5)
    print(f"  클러스터링 후 peak 수: {len(peaks_clustered)}")

    # --- 5단계: 이미지 좌표로 변환 ---
    streaks = radon_peaks_to_segments(peaks_clustered, theta, image.shape, min_length_px)

    # --- 6단계: 길이 기준 정렬 후 상위 N개만 반환 ---
    streaks.sort(key=lambda s: s[4], reverse=True)
    if len(streaks) > max_satellite_streaks:
        print(f"  streak {len(streaks)}개 중 상위 {max_satellite_streaks}개만 반환")
        streaks = streaks[:max_satellite_streaks]

    return streaks


def cluster_radon_peaks(peaks, sinogram, radius=5):
    """Radon 공간에서 가까운 peak를 클러스터링하여 대표 peak만 반환"""
    used = [False] * len(peaks)
    clustered = []

    for i, (r, t) in enumerate(peaks):
        if used[i]:
            continue
        group = [(r, t)]
        used[i] = True
        for j, (r2, t2) in enumerate(peaks):
            if used[j]:
                continue
            if abs(r - r2) < radius and abs(t - t2) < radius:
                group.append((r2, t2))
                used[j] = True
        # 그룹에서 sinogram 값이 가장 큰 peak 선택
        best = max(group, key=lambda p: sinogram[p[0], p[1]])
        clustered.append(best)

    return clustered


def radon_peaks_to_segments(peaks, theta, image_shape, min_length_px):
    """
    Radon peak (rho_idx, theta_idx) → 이미지 내 선분 끝점 변환.
    선분이 이미지 경계와 만나는 두 점을 끝점으로 사용.
    """
    h, w = image_shape
    cx, cy = w / 2, h / 2
    n_rho = int(np.ceil(np.sqrt(h**2 + w**2)))

    streaks = []

    for (rho_idx, theta_idx) in peaks:
        angle = theta[theta_idx]
        rho = rho_idx - n_rho  # Radon rho는 중심 기준

        angle_rad = np.radians(angle)
        cos_a = np.cos(angle_rad)
        sin_a = np.sin(angle_rad)

        # 선의 방정식: x*cos(a) + y*sin(a) = rho (중심 기준)
        # 이미지 경계 4면과의 교점 계산
        pts = []

        # x = 0
        if abs(sin_a) > 1e-6:
            y = (rho - (-cx) * cos_a) / sin_a + cy
            if 0 <= y <= h:
                pts.append((0, int(y)))

        # x = w-1
        if abs(sin_a) > 1e-6:
            y = (rho - (w - 1 - cx) * cos_a) / sin_a + cy
            if 0 <= y <= h:
                pts.append((w - 1, int(y)))

        # y = 0
        if abs(cos_a) > 1e-6:
            x = (rho - (-cy) * sin_a) / cos_a + cx
            if 0 <= x <= w:
                pts.append((int(x), 0))

        # y = h-1
        if abs(cos_a) > 1e-6:
            x = (rho - (h - 1 - cy) * sin_a) / cos_a + cx
            if 0 <= x <= w:
                pts.append((int(x), h - 1))

        if len(pts) < 2:
            continue

        # 가장 먼 두 점 선택
        best_d = 0
        best_pair = (pts[0], pts[1])
        for i in range(len(pts)):
            for j in range(i + 1, len(pts)):
                d = np.sqrt((pts[i][0] - pts[j][0])**2 + (pts[i][1] - pts[j][1])**2)
                if d > best_d:
                    best_d = d
                    best_pair = (pts[i], pts[j])

        if best_d < min_length_px:
            continue

        (x1, y1), (x2, y2) = best_pair
        streaks.append((x1, y1, x2, y2, best_d))

    return streaks


# =========================
# 좌표 계산
# =========================
def pixel_to_skycoord(x, y, wcs):
    sky = wcs.pixel_to_world(x, y)
    return sky.ra.deg, sky.dec.deg


def angular_distance(ra1, dec1, ra2, dec2):
    ra1, dec1, ra2, dec2 = map(np.radians, [ra1, dec1, ra2, dec2])
    cos_theta = (
        np.sin(dec1) * np.sin(dec2)
        + np.cos(dec1) * np.cos(dec2) * np.cos(ra1 - ra2)
    )
    return np.degrees(np.arccos(np.clip(cos_theta, -1, 1)))


# =========================
# 메인 파이프라인
# =========================
def process_image(file_path, api_key: str = None):
    image_data, header = load_fits(file_path)
    timestamp = get_timestamp(header)

    # WCS: FITS 헤더 우선, 불완전하면 Astrometry.net 사용
    try:
        wcs = get_wcs(header)
        print(f"  [{os.path.basename(file_path)}] FITS 헤더 WCS 사용")
    except ValueError:
        if api_key is None:
            raise ValueError("WCS가 없고 API 키도 없습니다.")
        wcs = plate_solve(file_path, api_key)

    image = preprocess_image(image_data)
    streaks = detect_streaks_radon(
        image_data, wcs=wcs,
        star_angle_manual=STAR_ANGLE_MANUAL,
        star_angle_tol=STAR_ANGLE_TOL,
        min_length_frac=MIN_LENGTH_FRAC,
        radon_threshold_sigma=RADON_THRESHOLD_SIGMA,
        max_satellite_streaks=MAX_SATELLITE_STREAKS
    )

    results = []
    for (x1, y1, x2, y2, length_px) in streaks:
        ra_s, dec_s = pixel_to_skycoord(x1, y1, wcs)
        ra_e, dec_e = pixel_to_skycoord(x2, y2, wcs)
        xm, ym = (x1 + x2) / 2, (y1 + y2) / 2
        ra_m, dec_m = pixel_to_skycoord(xm, ym, wcs)
        ang_len = angular_distance(ra_s, dec_s, ra_e, dec_e)

        results.append({
            "start_pixel": (x1, y1),
            "end_pixel": (x2, y2),
            "length_pixel": length_px,
            "start_sky": (ra_s, dec_s),
            "end_sky": (ra_e, dec_e),
            "mid_sky": (ra_m, dec_m),
            "angular_length_deg": ang_len,
            "timestamp": timestamp,
        })

    return results, os.path.basename(file_path)


# =========================
# 전체 실행
# =========================
def main():

    # =========================
    # 샘플 모드 / 실제 모드 선택
    # =========================
    if MODE == "sample" and ASTRIDE_SAMPLE:
        files = [ASTRIDE_SAMPLE]
        print(f"\nASTRiDE 샘플 이미지 사용: {ASTRIDE_SAMPLE}")
        api_key = None
        exposure_time = SAMPLE_EXPOSURE_TIME
        print(f"노출 시간: {exposure_time}초\n")
    else:
        print("FITS 파일을 선택하세요 (여러 개 선택 가능, 시간 순서):")
        files = select_fits_files()
        print(f"\n선택된 파일 {len(files)}개:")
        for f in files:
            print(f"  {os.path.basename(f)}")
        api_key = input("\nAstrometry.net API 키 (WCS가 있으면 Enter 스킵): ").strip()
        if not api_key:
            api_key = None
        exposure_time = float(input("노출 시간 (초): "))

    print("\n처리 중...\n")

    all_results = []
    for f in files:
        try:
            results, fname = process_image(f, api_key=api_key)
            all_results.append((fname, results))
            print(f"[{fname}] streak {len(results)}개 검출")
        except Exception as e:
            print(f"[{os.path.basename(f)}] 오류: {e}")

    # =========================
    # 결과 출력
    # =========================
    print("\n" + "="*60)
    print("상세 결과")
    print("="*60)

    for fname, results in all_results:
        print(f"\n[{fname}]")
        if not results:
            print("  streak 없음")
            continue
        for i, r in enumerate(results):
            print(f"  Streak #{i+1}")
            print(f"    시작점 픽셀:  {r['start_pixel']}")
            print(f"    끝점 픽셀:    {r['end_pixel']}")
            print(f"    길이 (px):    {r['length_pixel']:.1f}")
            print(f"    시작점 (RA, Dec): ({r['start_sky'][0]:.6f}°, {r['start_sky'][1]:.6f}°)")
            print(f"    끝점   (RA, Dec): ({r['end_sky'][0]:.6f}°, {r['end_sky'][1]:.6f}°)")
            print(f"    각거리:       {r['angular_length_deg']:.6f}°")
            print(f"    각속도:       {r['angular_length_deg'] / exposure_time:.6f}°/s")
            print(f"    관측 시각:    {r['timestamp'].isot}")

    # =========================
    # 파일 간 위성 매칭 및 각속도
    # =========================
    if len(all_results) >= 2:
        print("\n" + "="*60)
        print("파일 간 위성 매칭 및 각속도")
        print("="*60)

        for i in range(len(all_results) - 1):
            fname1, res1 = all_results[i]
            fname2, res2 = all_results[i + 1]

            if not res1 or not res2:
                continue

            t1 = res1[0]["timestamp"]
            t2 = res2[0]["timestamp"]
            delta_t = (t2 - t1).to_value("sec")

            print(f"\n  {fname1} → {fname2}  (간격 {delta_t:.2f}초)")

            # 모든 streak 쌍 매칭
            best_match = None
            best_score = float("inf")

            for a, r1 in enumerate(res1):
                mx1 = (r1["start_pixel"][0] + r1["end_pixel"][0]) / 2
                my1 = (r1["start_pixel"][1] + r1["end_pixel"][1]) / 2
                ang1 = np.degrees(np.arctan2(
                    r1["end_pixel"][1] - r1["start_pixel"][1],
                    r1["end_pixel"][0] - r1["start_pixel"][0]
                )) % 180

                for b, r2 in enumerate(res2):
                    mx2 = (r2["start_pixel"][0] + r2["end_pixel"][0]) / 2
                    my2 = (r2["start_pixel"][1] + r2["end_pixel"][1]) / 2
                    ang2 = np.degrees(np.arctan2(
                        r2["end_pixel"][1] - r2["start_pixel"][1],
                        r2["end_pixel"][0] - r2["start_pixel"][0]
                    )) % 180

                    # 각도 차이 (wrap-around 처리)
                    angle_diff = abs(ang1 - ang2)
                    if angle_diff > 90:
                        angle_diff = 180 - angle_diff

                    # 중심점 이동 거리 (픽셀)
                    move_px = np.sqrt((mx2 - mx1)**2 + (my2 - my1)**2)

                    # 이동 방향이 streak 방향과 일치하는지 확인
                    move_angle = np.degrees(np.arctan2(my2 - my1, mx2 - mx1)) % 180
                    move_angle_diff = abs(move_angle - ang1)
                    if move_angle_diff > 90:
                        move_angle_diff = 180 - move_angle_diff

                    # 점수: 각도 차이 + 이동 방향 차이 (둘 다 작을수록 좋음)
                    score = angle_diff + move_angle_diff

                    if score < best_score:
                        best_score = score
                        best_match = (a, b, r1, r2, move_px, angle_diff)

            if best_match is None:
                print("  매칭 실패")
                continue

            a, b, r1, r2, move_px, angle_diff = best_match
            print(f"  매칭: 프레임1 Streak#{a+1} ↔ 프레임2 Streak#{b+1}  (각도 차이 {angle_diff:.1f}°)")
            print(f"  중심점 이동: {move_px:.1f}px")

            d = angular_distance(
                *r1["mid_sky"],
                *r2["mid_sky"]
            )
            print(f"  이동 각거리: {d:.6f}°")
            print(f"  각속도:     {d / delta_t:.6f}°/s")


if __name__ == "__main__":
    main()

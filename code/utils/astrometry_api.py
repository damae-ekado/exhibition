import requests
import json
import time
from typing import Optional


API_KEY = "hvjbdvsgctupslac"
BASE_URL = "http://nova.astrometry.net/api/"

session_requests = requests.Session()


def login() -> Optional[str]:

    url = BASE_URL + "login"
    data = {"apikey": API_KEY}

    try:
        response = session_requests.post(
            url,
            data={"request-json": json.dumps(data)}
        )

        result = response.json()
        return result.get("session")

    except Exception:
        return None


def upload_file(session: str, file_path: str) -> Optional[int]:
    """
    FITS 파일 업로드 → submission id 반환
    """
    url = BASE_URL + "upload"

    data = {
        "session": session,
        "publicly_visible": "n",
        "allow_modifications": "d",
        "allow_commercial_use": "d"
    }

    try:
        with open(file_path, "rb") as f:
            files = {"file": f}

            response = session_requests.post(
                url,
                data={"request-json": json.dumps(data)},
                files=files
            )

        result = response.json()
        return result.get("subid")

    except Exception:
        return None


def check_status(subid: int):
    """
    submission 상태 확인
    """
    url = BASE_URL + f"submissions/{subid}"

    try:
        response = session_requests.get(url)
        result = response.json()
        return result.get("jobs")

    except Exception:
        return None


def check_job_status(job_id: int):
    """
    job의 solve 상태 확인
    """
    url = BASE_URL + f"jobs/{job_id}"

    try:
        response = session_requests.get(url)
        result = response.json()
        return result.get("status")

    except Exception:
        return None


def wait_for_result(subid: int, timeout: int = 180) -> Optional[int]:
    """
    job 완료될 때까지 polling (수정 버전)
    """

    start_time = time.time()

    while True:
        jobs = check_status(subid)

        if jobs and jobs[0] is not None:
            job_id = jobs[0]

            # ⭐ 핵심: solve 상태 확인
            status = check_job_status(job_id)
            print("job status:", status)

            if status == "success":
                return job_id

            elif status == "failure":
                print("Astrometry solve failed (server-side)")
                return None

        if time.time() - start_time > timeout:
            print("Timeout waiting for astrometry result")
            return None

        time.sleep(5)


def download_wcs(job_id: int, output_path: str) -> bool:
    """
    WCS 포함 FITS 다운로드 (수정 버전)
    """

    # ⭐ endpoint 변경
    url = f"http://nova.astrometry.net/new_fits_file/{job_id}"

    try:
        response = session_requests.get(url)

        # 상태 코드 확인
        if response.status_code != 200:
            print("Download failed:", response.status_code)
            return False

        # ⭐ FITS 파일 검증 (핵심)
        if not response.content.startswith(b"SIMPLE"):
            print("Invalid FITS file")
            print(response.content[:200])  # 디버깅
            return False

        with open(output_path, "wb") as f:
            f.write(response.content)

        return True

    except Exception as e:
        print("Download error:", e)
        return False


def solve_astrometry(input_path: str, output_path: str) -> Optional[str]:
    """
    전체 astrometry pipeline 실행
    """

    session = login()
    if session is None:
        return None

    subid = upload_file(session, input_path)
    if subid is None:
        return None

    job_id = wait_for_result(subid)
    if job_id is None:
        return None

    success = download_wcs(job_id, output_path)
    if not success:
        return None

    return output_path
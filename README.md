# 인공위성 궤도 분석 절차 정리  

# 1. 개요

본 과정은 천체 관측 이미지(FITS 파일) 2장을 활용하여 인공위성의 궤도 특성을 추정하고, 데이터베이스 상의 기존 위성과 비교·분석하는 것을 목표로 한다.

---

# 2. 입력 데이터

## 2.1 이미지 데이터

- 파일 형식: `.FITS`
- 동일 대상이 촬영된 연속 이미지 2장
- 각 이미지에서 위성의 시작점과 끝점을 마킹하여 입력

## 2.2 인공지능 및 코드 입력값

다음 정보가 코드 및 AI 분석 모듈로 전달되어야 한다.

1. 위성 지점의 **방위각(Azimuth)**
2. 위성 지점의 **고도(Altitude)**
3. 관측 시간 (노출 시간, Exposure Time)

※ 방위각 및 고도는 일주운동권 각도를 활용하여 궤도 경사각 추정에 사용됨

---

# 3. 처리 과정

## 3.1 좌표 추출

FITS 파일에서 다음 과정을 진행한다.

1. 시작점 (x₁, y₁)
2. 끝점 (x₂, y₂)
3. WCS(World Coordinate System)를 이용하여  
   픽셀 좌표 → 천구 좌표(방위각, 고도) 변환

---

## 3.2 각거리 계산

두 지점 사이의 각거리(Δθ)를 계산한다.

구면 삼각법을 적용한다.

```
cos(Δθ) = sin(alt₁)·sin(alt₂) 
          + cos(alt₁)·cos(alt₂)·cos(az₁ - az₂)
```

Δθ (단위: 도)

---

## 3.3 각속도 계산

각속도 ω는 다음과 같이 계산한다.

```
ω = Δθ / Δt
```

- Δθ : 이동 각거리 (도)
- Δt : 노출 시간 (초)

단위: 도/초 (deg/s)

---

## 3.4 궤도 경사각 추정

일주운동권 각도를 고려하여  
관측 위성의 이동 궤적을 적도 좌표계로 변환 후, 젹도(적도) 기준 기울기를 계산한다.

```
i ≈ arctan(Δδ / (Δα · cos δ))
```

- Δα : 적경 변화량
- Δδ : 적위 변화량
- δ : 평균 적위

결과: 궤도 경사각 i (deg)

---

## 3.5 공전 주기 추정

저궤도 위성(LEO)의 경우  
관측된 각속도를 기반으로 공전 반지름 r 추정 후, 중력 상수 기반 케플러 제3법칙을 적용한다.

```
T = 2π √(r³ / μ)
```

- μ = GM (지구 중력상수)
- T : 공전 주기

지구 자전 속도를 보정한 후 계산을 수행한다.

---

# 4. 데이터베이스 비교

산출된 값을 다음 기준으로 비교한다.

- 각속도
- 궤도 경사각
- 추정 공전 주기 (약 90분 내외 여부)

조건

- 공전 주기 ± 오차 범위
- 경사각 ± 허용 오차
- 각속도 유사성

이를 통해 기존 위성 목록과 매칭을 수행할 수 있다.

---

# 5. 최종 산출 결과

코드를 통해 도출해야 할 값

1. 각속도 (deg/s)
2. 젹도로부터의 궤도 경사각 (deg)
3. 공전 주기 (분)
4. 데이터베이스 상 유사 위성 후보 목록

---

# 6. 전체 요약

1. FITS 파일 2장 입력
2. 시작점/끝점 마킹
3. 천구 좌표 변환
4. 각거리 계산
5. 각속도 산출
6. 궤도 경사각 추정
7. 공전 주기 계산
8. 데이터베이스 비교
9. 위성 후보 도출

---

# 개발 환경 및 사용 기술

- **개발 도구**: Visual Studio  
- **프로그래밍 언어**: C#  
- **플랫폼**: .NET  
- **UI 프레임워크**: Windows Forms (WinForms)  
- **형상 관리**: Git  

## 개발 방식

- Visual Studio에서 WinForms 디자이너를 활용하여 UI 구성
- C#으로 이벤트 기반 로직 구현
- UI(Form)와 비즈니스 로직(Service) 분리
- 코드 컨벤션과 스타일을 팀 내에서 통일하여 유지보수성 확보

---

# C# 공동 개발 코드 규칙

# 1. 기본 원칙

- 이름만 보고도 의도를 이해할 수 있어야 한다.
- 주석보다 코드 자체가 설명이 되도록 작성한다.
- 코드 리뷰 기준을 문서화하고 지속적으로 개선한다.

---

# 2. 네이밍 규칙

## 2.1 PascalCase

다음 항목에는 PascalCase를 사용한다.

- 클래스
- 메서드
- 프로퍼티
- public 멤버
- enum
- 인터페이스

```csharp
public class OrderService
{
    public void CreateOrder() { }
    public int OrderCount { get; set; }
}
```

---

## 2.2 camelCase

다음 항목에는 camelCase를 사용한다.

- 지역 변수
- 매개변수
- private 필드(팀 규칙에 따름)

```csharp
public void CreateOrder(string orderName)
{
    int orderCount = 0;
}
```

---

## 2.3 인터페이스

- `I` 접두어를 사용한다.

```csharp
public interface IOrderService
{
    void CreateOrder();
}
```

---

## 2.4 private 필드

- `_camelCase` 형식을 권장한다.
- readonly 필드는 명확히 구분한다.

```csharp
private readonly IOrderRepository _orderRepository;
private int _orderCount;
```

---

## 2.5 메서드 네이밍

- 동사로 시작한다.
- 역할이 명확하게 드러나야 한다.

```csharp
GetUser()
CreateOrder()
UpdateProfile()
DeleteItem()
```

---

## 2.6 비동기 메서드

- `Async` 접미사를 반드시 붙인다.

```csharp
public async Task<Order> GetOrderAsync()
{
    ...
}
```

---

## 2.7 Boolean 변수

- is, has, can, should 등의 접두어를 사용한다.

```csharp
bool isActive;
bool hasPermission;
bool canEdit;
```

---

## 2.8 상수

- PascalCase를 사용한다.

```csharp
public const int MaxOrderCount = 100;
```

---

## 2.9 Enum

- Enum 이름은 단수형
- 값은 PascalCase

```csharp
public enum OrderStatus
{
    Pending,
    Completed,
    Cancelled
}
```

---

## 2.10 네임스페이스

```
회사명.프로젝트명.기능명
```

예:

```csharp
MyCompany.ECommerce.Services
```

---

## 2.11 파일 및 폴더 구조

- 클래스 이름과 파일 이름을 일치시킨다.
- 한 파일에 하나의 public 클래스만 둔다.
- 기능 단위로 폴더를 구성한다.

예시 구조:

```
Services/
    OrderService.cs
Interfaces/
    IOrderService.cs
Models/
    Order.cs
```

---

# 3. 클린 코드 규칙

## 3.1 의미 있는 이름 사용

```csharp
int orderCount;
string customerName;
```

- 축약어 남발 금지
- 검색 가능한 이름 사용
- 의도가 드러나는 이름 사용

---

## 3.2 함수는 한 가지 일만 하게 작성

```csharp
public void ProcessOrder(Order order)
{
    Validate(order);
    Save(order);
    NotifyCustomer(order);
}
```

- 하나의 메서드는 하나의 책임만 가진다.
- 내부 로직도 가능하면 분리한다.

---

## 3.3 함수는 짧게 유지

- 가능하면 20줄 이하
- 중첩은 2~3단계 이하
- Guard Clause 적극 사용

```csharp
if (user == null)
    return;

if (!user.IsActive)
    return;
```

---

## 3.4 매개변수는 3개 이하

```csharp
public Task<Order> CreateOrderAsync(CreateOrderRequest request)
```

- 관련 값은 DTO로 묶는다.

---

## 3.5 주석은 최소화

- 무엇(What)보다 왜(Why)를 설명한다.
- 코드로 표현 가능한 것은 코드로 작성한다.

---

## 3.6 매직 넘버 사용 금지

```csharp
if (order.Status == OrderStatus.Completed)
```

또는

```csharp
private const int MaxRetryCount = 3;
```

---

## 3.7 중복 제거 (DRY)

- 동일한 로직이 반복되면 메서드로 분리한다.
- 공통 로직은 재사용 가능하게 작성한다.

---

## 3.8 클래스는 작게 유지

- 한 클래스는 한 책임
- 300~500줄 이상이면 분리 고려

예:

```
OrderService
OrderRepository
OrderValidator
```

---

## 3.9 추상화에 의존 (DIP)

```csharp
private readonly IOrderRepository _repository;
```

- 구현체가 아닌 인터페이스에 의존한다.
- 의존성 주입(DI)을 활용한다.

---

## 3.10 예외 처리 명확히

```csharp
catch (SqlException ex)
{
    _logger.LogError(ex, "Database error occurred.");
    throw;
}
```

- 예외를 무시하지 않는다.
- 의미 있는 로그를 남긴다.

---

## 3.11 null 방어 코드 작성

```csharp
ArgumentNullException.ThrowIfNull(order);
```

또는

```csharp
_repository = repository ?? throw new ArgumentNullException(nameof(repository));
```

- Nullable Reference Type 사용 권장

---

## 3.12 비동기 코드 일관성 유지

```csharp
var result = await GetOrderAsync();
```

- `.Result`, `.Wait()` 사용 지양
- async/await 흐름 유지

---

# 4. 코드 스타일 통일

공동 개발 시 반드시 다음을 적용한다.

- `.editorconfig` 사용
- 자동 포맷 적용
- 코드 분석기(예: StyleCop, Roslyn Analyzer) 활용
- 저장 시 자동 정렬 설정

---

# 5. 코드 리뷰

- 메서드는 한 가지 일만 하는가?
- 이름만 보고 역할을 이해할 수 있는가?
- 중복 코드가 존재하지 않는가?
- 매직 넘버를 사용하지 않았는가?
- 예외 처리가 적절한가?
- 인터페이스 기반 설계가 되어 있는가?
- 테스트 가능한 구조인가?

---

# 연구노트 작성 방법 안내

# 1. 목적

본 안내문은 연구 수행 과정의 기록을 체계적으로 관리하고,  
연구의 재현성과 객관성을 확보하기 위한 연구노트 작성 기준을 정리한 것이다.

---

# 2. 작성 양식

- 연구노트는 **공유 드라이브에 저장된 연구노트 양식(스프레드 시트)**을 사용한다.
- 새로운 파일을 임의로 생성하지 않는다.
- 반드시 기존 양식의 **사본을 생성하여 작성**한다.

---

# 3. 파일 생성 절차

1. 공유 드라이브 접속
2. 연구노트 양식(스프레드 시트) 선택
3. **사본 만들기** 실행
4. 파일 제목을 작성 날짜로 변경

## 파일명 작성 형식

```
YYYY-MM-DD
```

예시:

```
2026-02-14
```

---

# 4. 연구노트 작성 기준

## 4.1 필수 기재 사항

- 연구 목적
- 실험 또는 분석 방법
- 사용 데이터 및 조건
- 계산 과정 및 적용 방정식
- 결과 값
- 결과 해석 및 결론
- 향후 보완 사항

모든 내용은 객관적이고 구체적으로 작성한다.  
제3자가 보아도 동일한 실험을 재현할 수 있도록 상세히 기록한다.

---

## 4.2 작성 원칙

- 연구 수행 당일 작성한다.
- 기존 기록을 삭제하지 않는다.
- 수정이 필요한 경우 수정 이력을 남긴다.
- 계산 과정은 생략하지 않는다.
- 코드 사용 시 주요 로직 또는 적용 방정식을 함께 기록한다.
- 추정과 사실을 명확히 구분한다.

---

# 5. 작성자 및 점검자 기재 방법

다음 항목은 문서 출력 시 **공란으로 둔다.**

- 작성자
- 작성일자
- 점검자
- 점검일자

출력 후 다음과 같이 작성한다.

- 볼펜 사용
- 정자로 명확히 기재
- 전자 입력 금지

---

# 6. 사진 및 첨부 자료

- 사진, 그래프, 이미지 자료는 필요 시 삽입한다.
- FITS 이미지, 분석 결과 그래프 등 연구 이해에 도움이 되는 경우에만 포함한다.
- 데이터 파일 경로 또는 저장 위치를 함께 기록한다.

---

# 7. 보관 및 관리

- 작성 완료 후 공유 드라이브에 저장한다.
- 파일명은 날짜 형식을 유지한다.
- 임의 수정 및 삭제를 금지한다.
- 점검 완료 후 관리 기준에 따라 보관한다.

---

# 8. 유의사항

- 감정적 표현을 사용하지 않는다.
- 실험 실패도 반드시 기록한다.
- 오류 발견 시 정정 내용을 명확히 남긴다.
- 모호한 표현을 지양한다.

---

# 외부 링크

**Google Drive**   
<https://drive.google.com/drive/folders/1ITm3FgFtJntNEHG_Hcmw6WF8j0xHcXlt?usp=sharing>

**chat GPT**   
<https://chatgpt.com/g/g-p-698eff8f0c788191bad8226ae9b0d8c1-jeonramhoe/project>

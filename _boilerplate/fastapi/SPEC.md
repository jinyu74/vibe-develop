# FastAPI 보일러플레이트 아키텍처 스펙

> 이 문서는 P2(analysis-api), P4(monitor-api)의 참조 구현 패턴을 정의합니다.
> AI가 코드를 생성할 때 이 아키텍처를 반드시 따라야 합니다.

## 기술 스택

| 기술 | 버전 | 용도 |
|------|------|------|
| Python | 3.12+ | 런타임 |
| FastAPI | latest | 웹 프레임워크 |
| Pydantic | V2 | 데이터 검증 & 스키마 |
| SQLAlchemy | 2.0+ | ORM |
| Alembic | latest | DB 마이그레이션 |
| Celery | latest | 비동기 태스크 |
| Redis | latest | Celery 브로커 & 캐시 |
| PostgreSQL | 15+ | 데이터베이스 |
| ruff | latest | 린터 & 포매터 |
| mypy | latest | 타입 체커 |
| pytest | latest | 테스트 프레임워크 |

## 아키텍처 패턴: Layered Architecture

```
src/
├── api/v1/              # API 라우터 (프레젠테이션 레이어)
│   ├── __init__.py
│   ├── router.py        # APIRouter 통합
│   └── endpoints/
│       └── analysis.py  # 엔드포인트 핸들러
├── core/                # 앱 설정 & 의존성
│   ├── config.py        # pydantic-settings 기반 설정
│   ├── deps.py          # FastAPI Depends 팩토리
│   └── security.py      # 인증/인가 (필요 시)
├── service/             # 비즈니스 로직 레이어
│   └── analysis.py      # 서비스 클래스
├── repository/          # 데이터 접근 레이어
│   └── analysis.py      # SQLAlchemy 쿼리
├── models/              # SQLAlchemy 모델
│   └── analysis.py      # DB 테이블 매핑
├── schemas/             # Pydantic V2 스키마
│   ├── request.py       # 요청 스키마
│   └── response.py      # 응답 스키마
└── tasks/               # Celery 태스크
    └── analysis.py      # 비동기 작업
```

## 의존성 방향

```
api → service → repository → models
         ↓
      schemas (request/response 변환)
```

- `api`는 `service`만 호출
- `service`는 `repository`를 통해 DB 접근
- `models` (SQLAlchemy) ≠ `schemas` (Pydantic) — 반드시 분리

## Pydantic V2 스키마 규칙

```python
from pydantic import BaseModel, Field

class AnalysisRequest(BaseModel):
    model_config = ConfigDict(strict=True)

    file_id: str = Field(..., description="분석 대상 파일 ID")
    options: dict[str, Any] = Field(default_factory=dict)

class AnalysisResponse(BaseModel):
    id: str
    status: str
    result: dict[str, Any] | None = None
    created_at: datetime
```

- `model_config = ConfigDict(strict=True)` 기본 적용
- 모든 필드에 `Field(description=...)` 작성
- `from_attributes = True`로 ORM 모델 변환 지원

## 에러 처리

```python
from fastapi import HTTPException

class AppError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code

# 전역 에러 핸들러 등록
@app.exception_handler(AppError)
async def app_error_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.code, "message": exc.message},
    )
```

## 로깅 규칙

```python
# libs/py-common/logging 모듈 사용
# 구조화된 JSON 로그
import structlog

logger = structlog.get_logger()

logger.info("analysis_started",
    file_id=file_id,
    task_id=task.id,
)
```

| 필드 | 필수 | 설명 |
|------|------|------|
| `timestamp` | O | ISO 8601 형식 |
| `level` | O | info, warning, error |
| `event` | O | 이벤트명 |
| `service` | O | 서비스명 |
| `trace_id` | - | 요청 추적 ID |

## 설정 관리

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="APP_")

    database_url: str
    redis_url: str = "redis://localhost:6379"
    debug: bool = False
```

- `pydantic-settings`로 환경 변수 자동 로드
- `.env` 파일 지원 (개발용)
- 민감 정보는 환경 변수로만 주입

## Celery 태스크 규칙

```python
from libs.py_common.celery import celery_app

@celery_app.task(bind=True, max_retries=3)
def run_analysis(self, file_id: str) -> dict:
    try:
        # 멱등성 보장: 동일 file_id로 재실행해도 안전
        ...
    except Exception as exc:
        self.retry(exc=exc, countdown=60)
```

- 태스크는 멱등성 보장
- 실패 시 지수 백오프로 재시도
- 결과는 DB에 저장 (Celery result backend 의존 금지)

## 테스트 패턴

- `pytest` + `pytest-asyncio`
- 픽스처로 DB 세션, 테스트 클라이언트 관리
- `httpx.AsyncClient`로 API 테스트
- 외부 의존성은 `unittest.mock.patch`로 목 처리

## DB 마이그레이션

```bash
# 마이그레이션 생성
alembic revision --autogenerate -m "add analysis table"

# 마이그레이션 적용
alembic upgrade head
```

- 모든 스키마 변경은 Alembic 마이그레이션으로 관리
- 수동 SQL 실행 금지

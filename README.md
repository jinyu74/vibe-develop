# vibe-develop

문서 기반 바이브 코딩 프로젝트. AI 에이전트와 함께 일관된 품질의 코드를 생산하기 위한 개발 환경입니다.

---

## 핵심 원칙

1. **문서가 기준이다** — 개인의 기억이 아니라 문서에 적힌 내용이 유일한 기준
2. **사람이 기억하지 않는다** — 체크리스트 + CI가 자동 검사
3. **누가 해도 같은 품질이 나온다** — 템플릿, 규칙, 검증 프로토콜로 품질 보장

---

## 프로젝트 구조

```
vibe-develop/
├── AGENTS.md                     # AI 행동 지침 (반드시 읽기)
├── README.md                     # 이 문서
├── pyproject.toml                # Python 설정 (ruff, mypy, pytest)
├── .pre-commit-config.yaml       # pre-commit 훅 설정
├── commitlint.config.js          # 커밋 메시지 규칙
├── .github/workflows/ci.yml      # GitHub Actions CI 파이프라인
├── .cursor/rules/                # Cursor AI 규칙
│   ├── project-conventions.mdc   # 프로젝트 전역 컨벤션
│   ├── doc-conversion.mdc        # PPT → 문서 변환 워크플로우
│   └── service-example-rules.mdc # 서비스별 규칙 템플릿
├── docs/
│   ├── overview.md               # 서비스 맵 (전체 현황)
│   └── _templates/               # 문서 템플릿 7종
│       ├── CONTEXT.md            # AI 진입점 (도메인 배정 포함)
│       ├── 01-requirements.md    # 요구사항
│       ├── 02-screen-spec.md     # 화면설계
│       ├── 03-api-contract.md    # API 계약서 (팀 합의)
│       ├── 05-api-spec.md        # API 스펙 상세
│       ├── 08-implementation-guide.md  # 구현 가이드
│       └── 09-test-cases.md      # 테스트 케이스
├── tools/
│   ├── extract-doc.py            # PPT/PDF 텍스트+이미지 추출
│   ├── validate-docs.py          # 문서 교차 참조 검증
│   └── requirements.txt          # Python 의존성
└── apps/                         # 서비스 코드 (서비스별 폴더)
```

---

## Quick Start: 새 팀원 온보딩

### 1단계: 환경 준비

```bash
git clone <repository-url>
cd vibe-develop

# 문서 추출 도구 의존성 설치
pip install -r tools/requirements.txt
```

### 2단계: 필수 문서 읽기 (순서대로)

| 순서 | 문서 | 목적 |
|------|------|------|
| 1 | `AGENTS.md` | AI 행동 규칙, 검증 프로토콜, 커밋/PR 규칙 이해 |
| 2 | `docs/overview.md` | 전체 서비스 현황 파악, 문서 구조 이해 |
| 3 | `docs/_templates/CONTEXT.md` | 서비스별 진입점 구조 이해 |
| 4 | `.cursor/rules/project-conventions.mdc` | 프로젝트 전역 컨벤션 확인 |

### 3단계: 담당 서비스 파악

- `docs/{service}/CONTEXT.md`에서 **도메인 배정** 테이블을 확인
- 자신이 담당하는 도메인과 관련 기능(F-ID)을 파악
- `03-api-contract.md`에서 해당 도메인의 인터페이스 계약을 확인

### 4단계: 작업 시작

```
CONTEXT.md 확인 → 03-api-contract.md Locked 확인 → 문서 6종 참조 → 구현 → 검증 → 문서 동기화
```

상세 절차는 `AGENTS.md`의 "작업 시작 프로토콜"을 따릅니다.

---

## Quick Start: 새 서비스 추가

1. `docs/{service-name}/` 폴더 생성
2. `docs/_templates/CONTEXT.md` → `docs/{service-name}/CONTEXT.md`로 복사 후 작성
3. `docs/{service-name}/{version}/` 폴더 생성 (`assets/` 포함)
4. `docs/_templates/`에서 **6개 템플릿** 복사 후 작성
5. `.cursor/rules/service-example-rules.mdc` → `.cursor/rules/{service}-rules.mdc`로 복사
   - **반드시** frontmatter의 `globs: apps/{service}/**` 설정
6. `docs/overview.md` "서비스 현황" 테이블에 추가

> 상세 절차: `docs/overview.md` > "빠른 시작" 섹션 참조

---

## Quick Start: PM 기획서 PPT 변환

### 1. 문서 추출

```bash
python tools/extract-doc.py input.pptx --output docs/{service}/{version}/
```

- 텍스트는 `_extracted_text.md`로 저장
- 이미지는 `assets/` 폴더에 저장

### 2. AI 변환 요청

추출된 텍스트를 AI에게 전달하며 다음과 같이 요청:

```
이 기획서를 @docs/_templates/ 템플릿 기반으로
docs/{service}/{version}/에 개발 문서로 변환해줘
```

### 3. 검토 및 합의

- 생성된 6개 문서 검토
- `03-api-contract.md`는 **Draft** 상태로 생성됨
- 팀 리뷰 → **Locked** 전환 후 구현 시작

> 상세 절차: `.cursor/rules/doc-conversion.mdc` 참조

---

## Cursor AI와 작업하기

### 서비스 작업 시

```
@docs/{service}/CONTEXT.md를 참고해서 F001 기능을 구현해줘
```

AI는 `CONTEXT.md`를 진입점으로 관련 문서 6종을 찾아가며 구현합니다.

### 규칙이 자동 적용되는 구조

| 규칙 파일 | 적용 조건 |
|----------|----------|
| `project-conventions.mdc` | 항상 적용 (`alwaysApply: true`) |
| `doc-conversion.mdc` | 문서 변환 작업 시 적용 |
| `{service}-rules.mdc` | 해당 서비스 파일을 열 때 자동 적용 (`globs` 기반) |

### AI가 따르는 프로토콜

1. 작업 시작 → `AGENTS.md` 확인
2. 계약 확인 → `03-api-contract.md` Locked 여부
3. 문서 기반 구현 → 문서 6종 참조
4. 구현 후 검증 → 검증 프로토콜 7항목 + 보안 9항목
5. 문서 동기화 → 코드-문서 드리프트 확인
6. 규칙 유지보수 → 필요 시 `.mdc` 파일 업데이트

---

## 문서 체계

| 번호 | 문서 | 역할 |
|------|------|------|
| 01 | requirements.md | 기능 목록, 비즈니스 규칙 |
| 02 | screen-spec.md | UI 구조, 컴포넌트, 상태 |
| 03 | api-contract.md | 팀 합의 인터페이스 계약 (Draft→Review→Locked) |
| 05 | api-spec.md | API 엔드포인트 상세, 요청/응답 |
| 08 | implementation-guide.md | 아키텍처, 패턴, 코딩 컨벤션 |
| 09 | test-cases.md | 테스트 시나리오, 커버리지 기준 |

> 번호 사이 빈 번호(04, 06, 07)는 향후 문서 유형 추가를 위한 여유 공간입니다.

---

## 개발 환경 설정

### Python Backend

```bash
pip install ruff mypy pytest pytest-cov pytest-asyncio httpx
```

### Frontend (React + TypeScript + Vite)

```bash
corepack enable
cd apps/{frontend-service}
pnpm install
```

### Pre-commit 훅 (전체 팀 필수)

```bash
pip install pre-commit
pre-commit install
pre-commit install --hook-type commit-msg
```

> 이후 `git commit` 시 자동으로 린트, 포맷, 타입 체크, 커밋 메시지 검증이 실행됩니다.

### 문서 검증

```bash
# 전체 서비스 검증
python tools/validate-docs.py

# 특정 서비스만 검증
python tools/validate-docs.py --service auth-api
```

---

## 기술 스택

| 영역 | 기술 | 버전 |
|------|------|------|
| Backend | Python, FastAPI | 3.12+ |
| Database | PostgreSQL | 15+ |
| Task Queue | Celery + Redis | |
| Desktop | Go, Wails | Go 1.25+, Wails v2.11.0 |
| Frontend | React, TypeScript, Vite | React 19.x, TS 5.9.x, Vite 7.x |
| Runtime | Node.js | 24.x (24.13.0) |
| Package Manager | pnpm | 10.x (10.28.2) |
| Reverse Proxy | Nginx | |
| CI | GitHub Actions | |
| Linter/Formatter | ruff (Python), ESLint + Prettier (TS), commitlint | |
| Type Check | mypy (Python), tsc (TypeScript) | |
| Test | pytest (Python), Vitest (Frontend), go test (Go) | |

---

## 주요 참조 문서

| 문서 | 위치 | 언제 참조하는가 |
|------|------|----------------|
| AI 행동 지침 | `AGENTS.md` | 모든 작업 전 |
| 서비스 맵 | `docs/overview.md` | 서비스 파악 시 |
| 프로젝트 컨벤션 | `.cursor/rules/project-conventions.mdc` | 코드 작성 시 |
| 문서 변환 규칙 | `.cursor/rules/doc-conversion.mdc` | PPT 변환 시 |
| 서비스 규칙 템플릿 | `.cursor/rules/service-example-rules.mdc` | 새 서비스 추가 시 |

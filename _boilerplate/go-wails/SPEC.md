# Go + Wails 보일러플레이트 아키텍처 스펙

> 이 문서는 P1(file-watcher), P3(file-relay)의 참조 구현 패턴을 정의합니다.
> AI가 코드를 생성할 때 이 아키텍처를 반드시 따라야 합니다.

## 기술 스택

| 기술 | 버전 | 용도 |
|------|------|------|
| Go | 1.25+ | 백엔드 로직 |
| Wails | v2.11.0 | 데스크탑 앱 프레임워크 |
| React | 19.x | 임베디드 프론트엔드 |
| TypeScript | 5.9.x | 프론트엔드 타입 안전성 |
| slog | stdlib | 구조화된 로깅 |
| Viper | latest | 설정 관리 (YAML) |

## 아키텍처 패턴: Clean Architecture

```
internal/
├── domain/           # 비즈니스 엔티티 & 인터페이스 (의존성 없음)
│   ├── entity.go     # 도메인 모델 (순수 Go struct)
│   └── repository.go # 인터페이스 정의
├── application/      # 유스케이스 (domain만 의존)
│   └── usecase.go    # 비즈니스 로직 오케스트레이션
├── infrastructure/   # 외부 구현체 (domain 인터페이스 구현)
│   ├── sftp.go       # SFTP 클라이언트
│   ├── filesystem.go # 로컬 파일 시스템
│   └── config.go     # Viper 기반 설정
└── ui/               # Wails 바인딩 (application 의존)
    └── app.go        # Wails에 노출하는 메서드
```

## 의존성 방향

```
ui → application → domain ← infrastructure
```

- `domain`은 어떤 패키지도 import하지 않음
- `application`은 `domain`의 인터페이스만 사용
- `infrastructure`는 `domain`의 인터페이스를 구현
- `ui`는 `application`의 유스케이스를 호출

## 로깅 규칙

```go
// libs/go-common/logger 패키지 사용
// 구조화된 JSON 로그, slog 기반
logger.Info("file transferred",
    slog.String("server", serverName),
    slog.String("file", fileName),
    slog.Duration("elapsed", elapsed),
)
```

| 필드 | 필수 | 설명 |
|------|------|------|
| `timestamp` | O | RFC3339 형식 |
| `level` | O | INFO, WARN, ERROR |
| `msg` | O | 로그 메시지 |
| `service` | O | 서비스명 (file-watcher, file-relay) |
| `trace_id` | - | 요청 추적 ID (있는 경우) |

## 설정 관리

```yaml
# configs/config.yaml
app:
  name: file-watcher
  log_level: info

# 서비스별 설정은 각 서비스의 config.yaml에서 확장
```

- Viper로 YAML 파일 로드
- 환경 변수 오버라이드 지원 (`APP_LOG_LEVEL` → `app.log_level`)
- 민감 정보(비밀번호 등)는 환경 변수로만 주입

## 에러 처리

```go
// 도메인 에러 타입 정의
type DomainError struct {
    Code    string
    Message string
    Err     error
}

// 래핑 패턴: fmt.Errorf("operation: %w", err)
// 센티널 에러: var ErrNotFound = errors.New("not found")
```

## 테스트 패턴

- 단위 테스트: `*_test.go` (인터페이스 기반 목 사용)
- 통합 테스트: `tests/` 폴더 또는 `//go:build integration` 빌드 태그
- 테이블 드리븐 테스트 선호

## Wails 바인딩 규칙

```go
// ui/app.go - Wails에 노출하는 구조체
type App struct {
    ctx     context.Context
    usecase *application.SomeUsecase
}

// 프론트엔드에서 호출 가능한 메서드는 exported
func (a *App) GetServers() []domain.Server { ... }
func (a *App) StartWatching(serverID string) error { ... }
```

- Wails 바인딩은 `ui/` 패키지에만 위치
- 비즈니스 로직을 바인딩 메서드에 직접 작성 금지 → 반드시 usecase 호출

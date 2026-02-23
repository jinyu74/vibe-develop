# [서비스명] API 스펙 - [버전]

> **서비스**: [service-name]
> **버전**: [version]
> **Base URL**: `https://api.example.com/v1`
> **최종 수정**: [YYYY-MM-DD]

---

## 변경 이력

| 버전 | 날짜 | 작성자 | 변경 내용 |
|------|------|--------|----------|
| v0.0.1 | YYYY-MM-DD | - | 초기 작성 |

---

## 공통 사항

### 인증

| 방식 | 헤더 | 비고 |
|------|------|------|
| Bearer Token | `Authorization: Bearer {token}` | JWT |

### 공통 에러 응답

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "사용자에게 보여줄 메시지",
    "details": {}
  }
}
```

### 공통 에러 코드

| HTTP 상태 | 에러 코드 | 설명 |
|-----------|---------|------|
| 400 | VALIDATION_ERROR | 요청 파라미터 유효성 검증 실패 |
| 401 | UNAUTHORIZED | 인증 토큰 없음 또는 만료 |
| 403 | FORBIDDEN | 권한 없음 |
| 404 | NOT_FOUND | 리소스 없음 |
| 429 | RATE_LIMITED | 요청 횟수 초과 |
| 500 | INTERNAL_ERROR | 서버 내부 오류 |

### 페이지네이션

```json
{
  "data": [],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 100,
    "totalPages": 5
  }
}
```

---

## API 엔드포인트

### 인증 (Auth)

<!-- PM 기획서의 "비즈니스 로직" / "데이터 흐름" 슬라이드에서 추출 -->

#### POST /api/auth/login

- **기능 ID**: F001
- **설명**: 사용자 로그인
- **인증 필요**: No

**Request Body**:

```json
{
  "email": "string (required, email format)",
  "password": "string (required, min 8)"
}
```

**Response 200 (성공)**:

```json
{
  "data": {
    "accessToken": "string (JWT)",
    "refreshToken": "string",
    "expiresIn": 3600,
    "user": {
      "id": "string",
      "email": "string",
      "name": "string",
      "role": "string"
    }
  }
}
```

**에러 응답**:

| HTTP 상태 | 에러 코드 | 조건 |
|-----------|---------|------|
| 401 | INVALID_CREDENTIALS | 이메일/비밀번호 불일치 |
| 422 | VALIDATION_ERROR | 입력값 형식 오류 |
| 429 | RATE_LIMITED | 5회 연속 실패 시 |

---

#### POST /api/auth/logout

- **기능 ID**: F001
- **설명**: 사용자 로그아웃
- **인증 필요**: Yes

**Request Header**:

```
Authorization: Bearer {accessToken}
```

**Response 200 (성공)**:

```json
{
  "data": {
    "message": "로그아웃 성공"
  }
}
```

---

### [도메인명] ([Domain])

#### [METHOD] /api/[path]

- **기능 ID**: F00X
- **설명**: ...
- **인증 필요**: Yes/No

**Request**:

```json
{}
```

**Response 200**:

```json
{}
```

**에러 응답**:

| HTTP 상태 | 에러 코드 | 조건 |
|-----------|---------|------|

---

## 데이터 모델

<!-- 주요 엔티티 정의 -->

### User

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| id | string (UUID) | Yes | 고유 식별자 |
| email | string | Yes | 이메일 |
| name | string | Yes | 이름 |
| role | enum | Yes | admin, user, viewer |
| createdAt | datetime | Yes | 생성일시 |

---

## Webhook / 이벤트

<!-- 외부 시스템 연동이 있는 경우 -->

| 이벤트 | 트리거 조건 | Payload |
|--------|-----------|---------|

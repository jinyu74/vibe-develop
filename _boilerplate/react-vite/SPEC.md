# React + Vite 보일러플레이트 아키텍처 스펙

> 이 문서는 P2 FE(analysis-web), P4 FE(monitor-web)의 참조 구현 패턴을 정의합니다.
> AI가 코드를 생성할 때 이 아키텍처를 반드시 따라야 합니다.

## 기술 스택

| 기술 | 버전 | 용도 |
|------|------|------|
| React | 19.x | UI 프레임워크 |
| TypeScript | 5.9.x | 타입 안전성 |
| Vite | 7.x | 번들러 & 개발 서버 |
| pnpm | 10.x | 패키지 매니저 |
| Zustand | latest | 클라이언트 상태 관리 |
| TanStack Query | latest | 서버 상태 관리 |
| React Router | latest | 라우팅 |
| ESLint | latest | 린터 |
| Prettier | latest | 포매터 |
| Vitest | latest | 테스트 프레임워크 |

## 아키텍처 패턴: Feature-Sliced Design (FSD)

```
src/
├── app/                 # 앱 설정, 라우터, 프로바이더
│   ├── App.tsx
│   ├── providers.tsx    # QueryClient, Store 등 감싸기
│   └── router.tsx       # 라우트 정의
├── pages/               # 페이지 컴포넌트 (라우트 1:1)
│   ├── dashboard/
│   │   ├── ui/
│   │   └── index.ts
│   └── settings/
├── widgets/             # 복합 UI 블록 (여러 feature 조합)
│   └── header/
├── features/            # 기능 단위 (API 호출 + 로직 + UI)
│   └── analysis/
│       ├── api/         # TanStack Query 훅
│       ├── model/       # Zustand 슬라이스 (필요 시)
│       └── ui/          # feature 전용 컴포넌트
├── entities/            # 도메인 엔티티 타입 & 기본 UI
│   └── analysis/
│       ├── types.ts     # 타입 정의
│       └── ui/          # 엔티티 카드 등
└── shared/              # 공유 유틸, 타입, UI 프리미티브
    ├── api/             # axios/fetch 인스턴스
    ├── lib/             # 유틸리티 함수
    ├── ui/              # Button, Input 등 기본 컴포넌트
    └── config/          # 환경 변수, 상수
```

## FSD 레이어 규칙

```
app → pages → widgets → features → entities → shared
```

- 상위 레이어만 하위 레이어를 import 가능
- 같은 레이어 간 cross-import 금지
- `shared`는 모든 레이어에서 import 가능

## 컴포넌트 규칙

```tsx
// 함수형 컴포넌트 + TypeScript
interface Props {
  title: string;
  onSubmit: (data: FormData) => void;
}

export function AnalysisForm({ title, onSubmit }: Props) {
  // ...
}
```

- 함수형 컴포넌트만 사용 (클래스 컴포넌트 금지)
- Props는 `interface`로 정의 (`type` alias 금지)
- 컴포넌트 파일과 Props 정의는 같은 파일에
- `export default` 금지 → named export만 사용

## 서버 상태 관리 (TanStack Query)

```tsx
// features/analysis/api/useAnalysis.ts
import { useQuery } from '@tanstack/react-query';

export function useAnalysis(id: string) {
  return useQuery({
    queryKey: ['analysis', id],
    queryFn: () => api.get(`/api/v1/analysis/${id}`),
  });
}
```

- 모든 서버 데이터는 TanStack Query로 관리
- `queryKey`는 계층적으로 구성: `['entity', id, 'sub']`
- 직접 `fetch`/`axios` 호출을 컴포넌트에서 하지 않음

## 클라이언트 상태 관리 (Zustand)

```tsx
// features/settings/model/store.ts
import { create } from 'zustand';

interface SettingsStore {
  theme: 'light' | 'dark';
  setTheme: (theme: 'light' | 'dark') => void;
}

export const useSettingsStore = create<SettingsStore>((set) => ({
  theme: 'light',
  setTheme: (theme) => set({ theme }),
}));
```

- UI 상태만 Zustand에 저장 (서버 데이터는 TanStack Query)
- 스토어는 feature 단위로 분리

## 환경 변수

```tsx
// shared/config/env.ts
export const env = {
  apiUrl: import.meta.env.VITE_API_URL,
} as const;
```

- `VITE_` 접두사로 클라이언트 노출 환경 변수 관리
- `shared/config/env.ts`에서 중앙 관리

## 테스트 패턴

- Vitest + React Testing Library
- 컴포넌트 테스트: 렌더링 + 사용자 인터랙션
- 훅 테스트: `renderHook`
- API 모킹: MSW (Mock Service Worker)

## 스타일링

스타일링 방식은 서비스 설계 시 결정 (Tailwind CSS 또는 CSS Modules).
어떤 방식이든 아래 규칙 적용:

- 인라인 스타일 금지 (`style={}` 직접 사용 금지)
- 글로벌 CSS 최소화
- 디자인 토큰(색상, 간격 등)은 변수로 관리

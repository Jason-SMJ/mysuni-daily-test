# Architecture And Service Flows

이 문서는 점검항목 유형별 서비스 흐름과 애플리케이션 아키텍처를 정리합니다.

## 서비스 구조(역할 중심) : Playwright + LLM + Slack

```mermaid
flowchart LR
  USER[배치 실행 / 운영자] --> APP[QA Application\nmain.py]

  APP --> PW[Playwright\n브라우저 제어 / 요소 탐색 / 화면 전환]
  APP --> LLM[LLM Vision\n스크린샷 판정 / 기준이미지 비교]
  APP --> SLACK[Slack\n실패 알림 / 결과 공유]

  PW --> SITE[MySuni Career 서비스]
  PW --> SHOT[실행 스크린샷]
  SHOT --> LLM
  BASE[기준 이미지\nbaselines/<service>/] --> LLM

  LLM --> RESULT[정상 / 비정상 / 판단불가]
  RESULT --> APP
  APP --> LOG[debug JSON / 로그 / 산출물 저장]
  APP --> SLACK
```

| 구성 요소 | 주요 역할 | 입력 | 출력 |
| --- | --- | --- | --- |
| QA Application | 실행 제어, 시나리오 선택, 결과 종합 | 설정값, 체크리스트, 환경변수 | 실행 흐름 제어, 최종 결과 |
| Playwright | 로그인, 페이지 이동, 요소 식별, 클릭, 팝업 전환 감지, 스크린샷 캡처 | URL, selector, action_type | 브라우저 상태, 캡처 이미지 |
| LLM Vision | 실행 이미지 판정, 기준 이미지 비교, 정상/비정상 판단 | 실행 스크린샷, 기준 이미지, 프롬프트 | 판정 결과, 상세 응답 |
| Slack | 실패 결과 및 운영 알림 전달 | 시나리오 결과, 스크린샷, 메시지 | DM/채널 알림 |
| Baselines | 기준 화면 관리 | 서비스별 기준 이미지 | LLM 비교 기준 |
| Screenshots / Debug | 실행 증적 및 디버그 분석 자료 저장 | 실행 중 캡처/전환 정보 | PNG, JSON, 로그 |

## 점검항목 유형별 서비스 흐름도

```mermaid
flowchart TD
  A[main.py 시작] --> B[설정 로드 config/settings.py]
  B --> C[MySuni 로그인]
  C --> D{시나리오 선택}

  D --> P[career_profile]
  D --> R[career_recommend]
  D --> M[career_mypick]
  D --> O[career_1on1]
  D --> G[career_myprogress]

  P --> P0{항목 action_type}
  P0 -->|navigate| P1[메뉴/URL 이동 확인]
  P0 -->|click| P2[우선순위 클릭 data-testid -> semantic -> structural -> js]
  P0 -->|popup| P3[잔존 모달 정리 -> 클릭 -> 전환감지 popup/nav/new-page]
  P0 -->|none| P4[화면 유지 상태 점검]

  P1 --> P5[스크린샷 캡처]
  P2 --> P5
  P3 --> P5
  P4 --> P5

  R --> R1[페이지 이동 -> 스크린샷]
  M --> M1[페이지 이동 -> 스크린샷]
  O --> O1[페이지 이동 -> 스크린샷]
  G --> G1[페이지 이동 -> 스크린샷]

  P5 --> V[LLM 판정 + 기준이미지 비교 optional]
  R1 --> V
  M1 --> V
  O1 --> V
  G1 --> V

  V --> Z{결과}
  Z -->|정상| S1[다음 항목/시나리오 진행]
  Z -->|비정상/판단불가| S2[Slack 알림 + 디버그/스크린샷 저장]
```

## 애플리케이션 아키텍처도

```mermaid
flowchart LR
  subgraph Runner[Execution Layer]
    MAIN[main.py\nScenario Orchestrator]
  end

  subgraph Config[Configuration Layer]
    YAML[config/config.yaml]
    ENV[.env]
    SETTINGS[config/settings.py]
  end

  subgraph Test[Domain Test Layer]
    BASE[tests/base_test.py]
    PROFILE[tests/career_profile_test.py]
    OTHERS[tests/career_*_test.py]
    SPEC[tests/specs/daily_check_spec.py]
  end

  subgraph Core[Automation Core Layer]
    BROWSER[core/browser.py\nPlaywright Driver]
    SHOT[core/screenshot.py\nCapture/Encode]
  end

  subgraph AI[AI Integration Layer]
    VISION[integrations/azure_openai.py]
  end

  subgraph Notify[Notification Layer]
    SLACK[integrations/slack_notifier.py]
  end

  subgraph Artifacts[Artifacts]
    BASELINE[baselines/<service>/]
    SCREEN[screenshots/<service>/]
    DEBUG[screenshots/debug/]
  end

  MAIN --> SETTINGS
  SETTINGS --> YAML
  SETTINGS --> ENV

  MAIN --> BASE
  MAIN --> PROFILE
  MAIN --> OTHERS
  PROFILE --> SPEC

  BASE --> BROWSER
  BASE --> SHOT
  PROFILE --> BROWSER
  PROFILE --> SHOT

  BASE --> VISION
  PROFILE --> VISION

  BASE --> SLACK
  PROFILE --> SLACK

  PROFILE --> BASELINE
  PROFILE --> SCREEN
  PROFILE --> DEBUG
  OTHERS --> SCREEN
```

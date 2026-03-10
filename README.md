# career_qa_v0.3

MySuni Career 화면을 Playwright로 탐색하고, Azure OpenAI Vision으로 스크린샷을 판별한 뒤 Slack DM으로 결과를 알리는 자동 점검 프로젝트입니다.

## 기술 스택

- Python (asyncio 기반)
- Playwright (브라우저 자동화)
- Azure OpenAI Vision (`openai` SDK)
- Slack SDK (`slack_sdk`)
- YAML + `.env` 기반 설정 관리

## 주요 기능

- MySuni 로그인 후 Career 관련 페이지 자동 이동
- 페이지/팝업 스크린샷 캡처
- LLM 기반 정상/비정상 판정 (`정상`, `비정상`, `판단불가`)
- 비정상 시 Slack DM 텍스트 + 스크린샷 파일 알림
- 시나리오별 ON/OFF 실행 (`config/config.yaml`)

## 프로젝트 구조

```text
career_qa_v0.3/
├── main.py                      # 엔트리포인트
├── requirements.txt
├── config/
│   ├── config.yaml              # 테스트/브라우저/페이지/시나리오 설정
│   └── settings.py              # YAML + .env 로더
├── core/
│   ├── browser.py               # BrowserManager, MySuniPage
│   └── screenshot.py            # 스크린샷 캡처/인코딩
├── integrations/
│   ├── azure_openai.py          # Vision 판정 클라이언트
│   └── slack_notifier.py        # Slack DM 전송
├── tests/
│   ├── base_test.py             # 공통 베이스
│   ├── career_*_test.py         # 페이지별 시나리오
│   └── specs/
│       ├── daily_check_spec.py  # 체크리스트/선택자 정의
│       └── PRECHECK_SPEC.md
├── screenshots/                 # 실행 결과 이미지
├── downloads/                   # 다운로드 파일
└── baselines/                   # 기준 이미지(샘플)
```

## 사전 준비

1. Python 가상환경 활성화
2. 의존성 설치

```bash
pip install -r requirements.txt
```

3. Playwright 브라우저 설치

```bash
playwright install chromium
```

## 환경변수 설정

프로젝트 루트에 `.env` 파일을 만들고 아래 값을 채웁니다.

```env
AZURE_OPENAI_KEY=your_azure_openai_key
SLACK_BOT_TOKEN=xoxb-your-token
SLACK_DM_USER_ID=U12345678
# 또는 SLACK_DM_EMAIL=user@company.com
MYSUNI_ID=your_mysuni_id
MYSUNI_PWD=your_mysuni_password

# 필요 시 프록시
# HTTPS_PROXY=http://proxy.example.com:8080
# HTTP_PROXY=http://proxy.example.com:8080
```

## 설정 파일 (`config/config.yaml`)

- `azure.openai`: endpoint / api_version / deployment
- `slack`: 토큰, DM 대상, 재시도 정책
- `mysuni`: base URL
- `browser`: headless, viewport, timeout, download_dir
- `test.pages`: 페이지 경로 맵
- `test.scenarios`: 실행 시나리오 ON/OFF

예시:

```yaml
test:
  scenarios:
    - name: "career_profile"
      enabled: true
    - name: "career_recommend"
      enabled: false
```

## 실행 방법

```bash
python main.py
```

특정 시나리오만 실행:

```bash
python main.py --scenario career_profile
```

`career_profile`의 특정 체크리스트 항목(1-based)만 실행:

```bash
python main.py --scenario career_profile --item 10
```

CLI 옵션 규칙:

- `--scenario`: 해당 시나리오만 실행 (YAML의 다른 시나리오 설정은 무시)
- `--item`: `career_profile`에서만 사용 가능
- `--item` 인덱스는 1-based이며, 범위를 벗어나면 실패 처리

실행 시 순서:

1. 설정 로드
2. MySuni 로그인
3. 활성화된 시나리오 실행
4. 스크린샷 + LLM 판정
5. 결과 요약 출력 및 Slack 알림

## 현재 기본 시나리오

- 기본 활성화: `career_profile`
- 기본 비활성화:
- `career_recommend`
- `career_mypick`
- `career_1on1`
- `career_myprogress`

## 결과 산출물

- 스크린샷: `screenshots/`
- 디버그 덤프(팝업 분석): `screenshots/debug/` (Career Profile 팝업 점검 시)
- 다운로드 파일: `downloads/`

## Slack 권한 권장값

- `chat:write`
- `files:write`
- `users:read.email` (이메일 조회 사용 시)
- `conversations:write` 또는 `im:write` (워크스페이스 정책에 따라)

## 참고 / 주의

- 실제 계정, 토큰, 비밀번호는 `config.yaml`이 아닌 `.env` 사용 권장
- 기준 이미지 비교를 쓰려면 체크리스트의 `reference_image` 경로에 맞춰 파일을 준비해야 합니다
- 회사망 환경에서는 프록시/인증서 설정이 필요할 수 있습니다

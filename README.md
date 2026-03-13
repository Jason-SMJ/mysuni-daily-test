# career_qa_v0.3

MySuni Career 서비스 화면을 자동 점검하는 QA 애플리케이션입니다.  
Playwright로 실제 화면을 조작하고, 캡처 이미지를 LLM(Vision)으로 판정하여 결과를 Slack으로 알립니다.

## 애플리케이션 목적 및 주요 기능

### 개요
- 사람이 매일 수동으로 확인하던 Career 화면 점검을 자동화해 점검 시간과 누락 리스크를 줄입니다.
- UI 깨짐, 모달 미노출, 로딩 비정상 등의 화면 이슈를 조기에 탐지합니다.(스모크 테스트 + 새너티 테스트)
- 점검 로그/이미지/판정 근거를 남겨 재현성과 추적성을 확보합니다.

### 목적
- **서비스 가용성 확보**: Career 핵심 사용자 흐름을 상시 점검해 화면 장애와 기능 이상을 조기에 탐지하고, 서비스 중단 및 품질 저하 리스크를 최소화합니다.
- **운영 안전성 강화**: 수작업 점검을 자동화하여 점검 편차와 누락 가능성을 줄이고, 장애 징후를 표준화된 알림 체계로 신속히 공유해 대응 속도와 운영 신뢰도를 높입니다.
- **근거 기반 품질관리 체계화**: 점검 결과를 로그, 스크린샷, AI 판정 근거로 축적해 재현성·추적성을 확보하고, 원인 분석 및 개선 의사결정의 정확도를 높입니다.
- **서비스 확장성 내재화**: 시나리오/항목 단위의 모듈형 점검 구조를 통해 신규 Career 서비스 및 기능 확장 시에도 동일한 품질 기준을 빠르게 적용할 수 있는 운영 기반을 마련합니다.
- **지속 가능한 운영 효율화**: 반복 점검 업무를 경감해 운영 리소스를 고부가가치 개선 과제에 집중시키고, 장기적으로 안정적이고 예측 가능한 품질 운영 체계를 구축합니다.

### 주요 기능
**시나리오 기반 자동 실행**
  - MySuni 로그인부터 서비스별 핵심 화면 진입까지 점검 흐름 자동 수행함
  - 반복 점검 절차 표준화로 운영 편차 축소 가능함
  - 일일 점검 수행 안정성과 지속 운영 기반 확보함
**체크리스트 중심 품질 점검**
  - `tests/specs/daily_check_spec.py` 기반으로 항목별 기대 결과 구조화함
  - 점검 기준을 코드로 관리해 기준 일관성과 변경 대응 속도 확보함
  - 운영 통제력 강화 및 품질 기준 내재화 가능함
**화면 전환·팝업 정합 검증**
  - 사용자 액션 이후 popup/navigation/new-page 전환 자동 감지함
  - 동적 UI 구간 정상 흐름 여부를 일관된 기준으로 판별함
  - 전환 실패 지점 조기 식별로 서비스 체감 품질 리스크 완화함
**증거 기반 캡처·비교 분석**
  - 실행 화면 스크린샷 저장 및 기준 이미지 비교 수행함
  - 화면 품질 편차를 시각적 근거 기반으로 확인 가능함
  - 재현 가능한 이력 축적으로 원인 분석 신뢰도 제고함
**AI 판정 및 이력 관리**
  - LLM 기반으로 정상/비정상/판단불가 자동 분류 수행함
  - 판정 결과와 근거 응답 동시 기록해 판단 맥락 보존함
  - 운영 의사결정 속도와 정확도 동시 향상 가능함
**Slack 실시간 결과 공유**
  - 실패 항목 및 최종 요약을 Slack 텍스트/파일로 즉시 전파함
  - 채널·DM 연계 알림으로 운영 공조 체계 강화함
  - 장애 인지부터 대응 착수까지 리드타임 단축 가능함
**유연한 실행 단위 제어**
  - `--scenario`, `--item` 옵션으로 전체/시나리오/단일 항목 실행 지원함
  - 장애 재현, 변경 검증, 핫픽스 확인 등 상황별 점검 범위 조정 가능함
  - 운영 민첩성 및 검증 효율 동시 확보 가능함

## 프로젝트 구조와 파일 역할
```text
career_qa_v0.3/
├── main.py
├── requirements.txt
├── config/
│   ├── config.yaml
│   └── settings.py
├── core/
│   ├── browser.py
│   └── screenshot.py
├── integrations/
│   ├── azure_openai.py
│   └── slack_notifier.py
├── tests/
│   ├── base_test.py
│   ├── career_profile_test.py
│   ├── career_recommend_test.py
│   ├── career_mypick_test.py
│   ├── career_1on1_test.py
│   ├── career_myprogress_test.py
│   └── specs/
│       ├── daily_check_spec.py
│       └── PRECHECK_SPEC.md
├── baselines/
│   └── <service>/
├── screenshots/
│   ├── <service>/
│   └── debug/
└── downloads/
```

### 폴더/파일별 역할
- `main.py`: 실행 엔트리포인트. 설정 로드, 로그인, 시나리오 실행, 결과 요약/Slack 알림 담당
- `config/config.yaml`: 브라우저/시나리오 활성화/재시도/경로 등 운영 설정
- `config/settings.py`: `config.yaml` + `.env` 값을 로딩/병합
- `core/browser.py`: Playwright 브라우저/페이지 생성, 로그인, 페이지 이동
- `core/screenshot.py`: 전체/요소 캡처, base64 인코딩. 하위 폴더 자동 생성 포함
- `integrations/azure_openai.py`: Vision 모델 호출 및 판정 결과 파싱
- `integrations/slack_notifier.py`: 실패 알림 및 첨부파일 전송
- `tests/base_test.py`: 공통 캡처/LLM 검증/실패 알림 베이스 클래스
- `tests/career_profile_test.py`: 체크리스트 기반 하이브리드 검증 핵심 로직
- `tests/career_*_test.py`: 페이지 단위 시나리오 실행 클래스
- `tests/specs/daily_check_spec.py`: 점검 항목 정의(기대결과, 선택자, reference_image 등)
- `baselines/<service>/`: 기준 이미지 저장소
- `screenshots/<service>/`: 실행 결과 이미지 저장소
- `screenshots/debug/`: 팝업 전환/탐지 디버그 JSON

## Playwright 및 LLM 사용 정책/로직

별도 문서: `docs/architecture.md`

품질 평가 가이드: `docs/quality-evaluation.md`

### Playwright 요소 식별 정책

`career_profile` 기준 클릭 우선순위는 아래와 같습니다.

1. `data-testid` 기반 탐색
2. 텍스트(semantic candidates) 기반 탐색
3. 구조 선택자(structural selectors) 기반 탐색
4. JS fallback (`document.querySelectorAll`) 기반 클릭

정책 의도:
- 가장 안정적인 식별자(`data-testid`)를 최우선 사용
- UI 문구 변경 가능성을 감안해 semantic/structural을 보조로 사용
- 프레임(main + iframe) 컨텍스트를 순회하여 cross-frame 요소까지 탐지

### 팝업/전환 감지 로직

- 팝업 감지 기준: `BaseModal_main__` 클래스를 포함하는 visible 모달
- 클릭 후 전환 체크: `popup` / `navigation` / `new-page`를 구분
- 이전 테스트의 잔존 모달 오염 방지: 팝업 액션 전/후 `close_all_popups` 수행
- 복수 모달 동시 존재 시, 제목 히트 + 내용 점수(fields + text length)로 타깃 모달 선택

### 스크린샷 캡처 정책

- 저장 경로: `screenshots/<service>/...`
- `career_profile`는 `reference_image`가 있으면 동일 파일명으로 저장
  - 예: `reference_image="career_profile/09_project_popup.png"`
  - 실행 이미지: `screenshots/career_profile/09_project_popup.png`
- 팝업 캡처 우선순위
1. 타깃 모달 요소 캡처
2. iframe 전체영역 캡처
3. full-page 캡처 폴백

### LLM 판정 정책

- 입력: 실행 캡처 이미지 + (있으면) 기준 이미지
- 프롬프트 구성 요소
  - 점검 항목명/상세/기대 결과
  - 사전 동작 성공/실패
  - 전환 타입(popup/navigation 등)
  - 정상/비정상 추가 판정 기준
- 판정값
  - `정상`: 기대 결과가 화면에서 확인됨
  - `비정상`: 기대 결과 불충족, 깨짐/오류/로딩 이상
  - `판단불가`: 근거 부족 또는 모호

### 기준 이미지 운영 규칙

- 기준 이미지는 `baselines/<service>/`에 저장
- 파일명은 실행 캡처 파일명과 동일하게 유지 권장
- 기준 이미지가 없으면 실행 이미지만으로 판정 (테스트는 계속 진행)

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

프로젝트 루트 `.env` 예시:

```env
AZURE_OPENAI_KEY=your_azure_openai_key
SLACK_BOT_TOKEN=xoxb-your-token
SLACK_CHANNEL_ID=C12345678
# 또는 SLACK_CHANNEL_NAME=#career-qa-noti
SLACK_DM_USER_ID=U12345678
# 또는 SLACK_DM_EMAIL=user@company.com
SLACK_SEND_DM_ALSO=true
MYSUNI_ID=your_mysuni_id
MYSUNI_PWD=your_mysuni_password

# 필요 시 프록시
# HTTPS_PROXY=http://proxy.example.com:8080
# HTTP_PROXY=http://proxy.example.com:8080
```

## 실행 방법

전체 실행:

```bash
python main.py
```

시나리오 단위 실행:

```bash
python main.py --scenario career_profile
```

체크리스트 항목 단위 실행 (`career_profile` 전용, 1-based):

```bash
python main.py --scenario career_profile --item 10
```

CLI 규칙:
- `--scenario`: 해당 시나리오만 실행 (YAML 타 시나리오 설정 무시)
- `--item`: `career_profile`에서만 유효

## 업로드/배포 운영 가이드

브랜치/커밋/PR 규칙: `docs/contributing.md`

### 1) GitHub 업로드(최초 1회)

```bash
git init
git branch -M main
git add .
git commit -m "Initial commit"
git remote add origin <repo-url>
git push -u origin main
```

### 2) 일상 운영 배포(코드 반영)

```bash
git status
git add .
git commit -m "chore: update scenario logic"
git push
```

### 3) 서버/배치 실행 가이드(권장)

1. 코드 Pull
2. 가상환경 활성화
3. `pip install -r requirements.txt`
4. `playwright install chromium` (최초/업데이트 시)
5. `.env` 주입
6. `python main.py --scenario ...` 실행

### 3-1) macOS 로컬 Daily 실행 가이드 (`launchd`)

1. 실행 스크립트 생성 (예시)

```bash
cat > ~/scripts/run_career_qa_daily.sh <<'EOF'
#!/bin/zsh
set -euo pipefail

PROJECT_DIR="/Users/a11681/Documents/OZ/My_Project/career_qa_v0.3 2"
PYTHON_BIN="$PROJECT_DIR/bin/python"
LOG_DIR="$HOME/Library/Logs/career_qa_daily"

mkdir -p "$LOG_DIR"
cd "$PROJECT_DIR"

"$PYTHON_BIN" main.py >> "$LOG_DIR/daily.log" 2>&1
EOF

chmod +x ~/scripts/run_career_qa_daily.sh
```

2. LaunchAgent 등록 파일 생성 (매일 오전 9시 실행 예시)

```bash
cat > ~/Library/LaunchAgents/com.mysuni.careerqa.daily.plist <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
  <dict>
    <key>Label</key>
    <string>com.mysuni.careerqa.daily</string>

    <key>ProgramArguments</key>
    <array>
      <string>/Users/a11681/scripts/run_career_qa_daily.sh</string>
    </array>

    <key>StartCalendarInterval</key>
    <dict>
      <key>Hour</key>
      <integer>9</integer>
      <key>Minute</key>
      <integer>0</integer>
    </dict>

    <key>RunAtLoad</key>
    <false/>

    <key>StandardOutPath</key>
    <string>/Users/a11681/Library/Logs/career_qa_daily/launchd.out.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/a11681/Library/Logs/career_qa_daily/launchd.err.log</string>
  </dict>
</plist>
EOF
```

3. 등록/활성화/즉시 실행 테스트

```bash
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.mysuni.careerqa.daily.plist
launchctl enable gui/$(id -u)/com.mysuni.careerqa.daily
launchctl kickstart -k gui/$(id -u)/com.mysuni.careerqa.daily
```

4. 상태/로그 확인

```bash
launchctl print gui/$(id -u)/com.mysuni.careerqa.daily
tail -n 200 ~/Library/Logs/career_qa_daily/daily.log
tail -n 200 ~/Library/Logs/career_qa_daily/launchd.err.log
```

5. 중지/해제

```bash
launchctl disable gui/$(id -u)/com.mysuni.careerqa.daily
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.mysuni.careerqa.daily.plist
```

### 4) 운영 체크리스트

- `.env`, 토큰, 계정정보는 절대 커밋 금지
- 기준 이미지 변경 시 PR에 변경 사유 기록
- 실패 케이스는 `screenshots/debug/` JSON과 함께 분석
- 회사망 프록시/인증서 환경이면 네트워크 설정 선확인

## Slack 권한 권장값

- `chat:write`
- `files:write`
- `users:read.email` (이메일 대상 조회 시)
- `conversations:write` 또는 `im:write`

## 참고

- 기본 활성 시나리오: `career_profile`
- 비활성 시나리오: `career_recommend`, `career_mypick`, `career_1on1`, `career_myprogress`

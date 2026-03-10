# career_qa_v0.3

MySuni Career 서비스 화면을 자동 점검하는 QA 애플리케이션입니다.  
Playwright로 실제 화면을 조작하고, 캡처 이미지를 LLM(Vision)으로 판정하여 결과를 Slack으로 알립니다.

## 애플리케이션 목적 및 주요 기능

### 목적
- 사람이 매일 수동으로 확인하던 Career 화면 점검을 자동화해 점검 시간과 누락 리스크를 줄입니다.
- UI 깨짐, 모달 미노출, 로딩 비정상 등의 화면 이슈를 조기에 탐지합니다.(스모크 테스트 + 새너티 테스트)
- 점검 로그/이미지/판정 근거를 남겨 재현성과 추적성을 확보합니다.

### 주요 기능
- MySuni 로그인 후 시나리오별 페이지 이동 자동화
- 체크리스트 기반 항목 점검 (`tests/specs/daily_check_spec.py`)
- 요소 클릭/팝업 진입/전환 감지 (Playwright)
- 스크린샷 캡처 및 기준 이미지 비교 (optional)
- LLM 판정 (`정상`, `비정상`, `판단불가`) 및 상세 응답 기록
- 실패 시 Slack DM 텍스트/파일 알림
- 시나리오 단위 및 항목 단위 실행 지원 (`--scenario`, `--item`)

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
SLACK_DM_USER_ID=U12345678
# 또는 SLACK_DM_EMAIL=user@company.com
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

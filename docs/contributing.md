# Contributing Guide

이 문서는 Jira 티켓 기반 브랜치/커밋/PR 규칙을 정의합니다.

## 기본 원칙

- 1 티켓 = 1 브랜치 = 1 PR
- `main` 브랜치 직접 커밋/푸시는 지양
- 작업은 항상 `main` 최신화 후 새 브랜치에서 시작

## 브랜치 네이밍 규칙

형식:

```text
dev/<name>/<JIRA-KEY>-<short-topic>
```

예시:

- `dev/jason/QA-142-popup-overlap-fix`
- `dev/jason/QA-155-readme-architecture-update`
- `dev/jason/QA-160-ci-workflow-update`

## 커밋 메시지 규칙

형식:

```text
<type>(<scope>): [<JIRA-KEY>] <summary>
```

예시:

- `fix(career_profile): [QA-142] close stale modal before learning popup`
- `docs(readme): [QA-155] add architecture and service flow diagrams`
- `ci(workflow): [QA-160] add syntax and import smoke checks`

권장 type:

- `feature`, `fix`, `docs`, `refactor`, `test`, `chore`, `ci`

## PR 제목 규칙

형식:

```text
[<JIRA-KEY>] <type>: <summary>
```

예시:

- `[QA-142] fix: prevent overlapping modals in popup checks`

## PR 본문 템플릿

```md
### Jira
- Ticket: <JIRA URL or KEY>

### 변경 목적
- 왜 이 변경이 필요한지 1-2줄

### 변경 내용
- 핵심 변경 1
- 핵심 변경 2

### 테스트
- [ ] 로컬 실행
- [ ] 관련 시나리오 확인
- [ ] 회귀 영향 확인

### 체크리스트
- [ ] 민감정보(.env, token) 미포함
- [ ] 문서/스크린샷 경로 규칙 준수
- [ ] 리뷰어 확인 포인트 명시
```

## 권장 작업 순서

```bash
git checkout main
git pull origin main
git checkout -b dev/<name>/<JIRA-KEY>-<short-topic>

# 작업
git add .
git commit -m "fix(scope): [<JIRA-KEY>] <summary>"
git push -u origin dev/<name>/<JIRA-KEY>-<short-topic>
```

이후 GitHub에서 해당 브랜치로 PR을 생성합니다.

# ZCP Configuration Guide for MySuni Career QA Daily Batch

이 문서는 SK C&C / SK AX ZCP 환경에 Career QA Daily Batch를 배포하기 위한 구체적인 설정 가이드입니다.

---

## 1. ZCP 클러스터 연결 설정

### 1.1 kubeconfig 획득 및 설정

**ZCP 대시보드에서 kubeconfig 다운로드:**
```bash
# 1. ZCP 대시보드 접속
# https://zcp.sk.com/dashboard

# 2. 프로필 → kubeconfig 다운로드
# 파일명: zcp-kubeconfig.yaml

# 3. 로컬에 저장
mkdir -p ~/.kube
cp ~/Downloads/zcp-kubeconfig.yaml ~/.kube/config
chmod 600 ~/.kube/config

# 4. 연결 테스트
kubectl cluster-info
```

### 1.2 클러스터 접근 검증

```bash
kubectl get nodes
kubectl config current-context
kubectl auth can-i create deployments --namespace career-qa
```

---

## 2. SK 프라이빗 레지스트리 설정

### 2.1 레지스트리 로그인

```bash
# Docker 로그인
docker login registry.zcp.sk.com

# 이미지 푸시 테스트
docker push registry.zcp.sk.com/myteam/career-qa:v1.0.0
```

### 2.2 Kubernetes ImagePullSecret 생성

```bash
kubectl create secret docker-registry sk-registry-credentials \
  --docker-server=registry.zcp.sk.com \
  --docker-username=<YOUR_USERNAME> \
  --docker-password=<YOUR_PASSWORD> \
  --docker-email=<YOUR_EMAIL> \
  -n career-qa
```

---

## 3. 네트워크 및 프록시 설정

### 3.1 프록시가 필요한 경우

```bash
# Docker 프록시 설정
export HTTPS_PROXY=http://proxy.sk.com:8080
export HTTP_PROXY=http://proxy.sk.com:8080

# Kubernetes Secret에 프록시 추가
kubectl create secret generic career-qa-secrets \
  --from-literal=https-proxy='http://proxy.sk.com:8080' \
  -n career-qa
```

### 3.2 외부 API 연결 확인

```bash
# MySuni 서비스 연결 확인
kubectl run curl-test --image=curlimages/curl:latest -it --rm \
  --restart=Never -n career-qa -- \
  curl -v https://mysuni.sk.com/
```

---

## 4. Secret 관리

### 4.1 안전한 Secret 생성

```bash
# 대화형 스크립트 사용 (권장)
bash deployment/k8s/create-secrets.sh

# 또는 환경변수로부터
kubectl create secret generic career-qa-secrets \
  --from-literal=azure-openai-key='...' \
  --from-literal=slack-bot-token='...' \
  --from-literal=mysuni-id='...' \
  --from-literal=mysuni-pwd='...' \
  -n career-qa
```

### 4.2 Secret 검증

```bash
kubectl get secret career-qa-secrets -n career-qa
kubectl describe secret career-qa-secrets -n career-qa
```

---

## 5. 배포

### 5.1 매니페스트 검증

```bash
kubectl apply -f deployment/k8s/ --dry-run=client -n career-qa
```

### 5.2 배포 실행

```bash
bash deployment/k8s/deploy.sh
# 또는
kubectl apply -f deployment/k8s/
```

### 5.3 배포 검증

```bash
bash deployment/k8s/health-check.sh
```

---

## 6. 테스트

### 6.1 수동 Job 실행

```bash
kubectl create job --from=cronjob/career-qa-daily test-run-1 -n career-qa
kubectl get pods -n career-qa -w
POD_NAME=$(kubectl get pods -n career-qa -l job-name=test-run-1 -o jsonpath='{.items[0].metadata.name}')
kubectl logs $POD_NAME -n career-qa -f
```

---

## 7. 운영

### 7.1 모니터링

```bash
# CronJob 상태
kubectl get cronjob -n career-qa

# 최근 실행 이력
kubectl get jobs -n career-qa --sort-by=.metadata.creationTimestamp | tail -5

# 리소스 사용량
kubectl top pods -n career-qa
```

### 7.2 CronJob 일시 중지/재개

```bash
# 중지
kubectl patch cronjob career-qa-daily -n career-qa -p '{"spec":{"suspend":true}}'

# 재개
kubectl patch cronjob career-qa-daily -n career-qa -p '{"spec":{"suspend":false}}'
```

---

## 트러블슈팅

| 문제 | 해결 |
|------|------|
| ImagePullBackOff | 이미지 레지스트리 확인, Secret 검증 |
| CrashLoopBackOff | Pod 로그 확인, 환경변수/Secret 검증 |
| Connection refused | kubeconfig 경로 및 권한 확인 |
| Unauthorized | kubeconfig 만료 또는 재발급 필요 |

---

참고: `deployment/k8s/DEPLOYMENT_CHECKLIST.md` 파일에 빠른 배포 체크리스트가 있습니다.

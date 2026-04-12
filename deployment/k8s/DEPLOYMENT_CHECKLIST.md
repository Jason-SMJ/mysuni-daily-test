# ZCP 배포 체크리스트 (빠른 참고)

## 사전 준비 (ZCP 관리자에게 받을 정보)

- [ ] kubeconfig 파일
- [ ] SK 레지스트리 URL, 사용자명, 비밀번호
- [ ] 네임스페이스 이름 및 생성 권한
- [ ] 프록시 주소 (필요시)
- [ ] 리소스 할당량 확인

---

## 배포 순서

### ✅ Phase 1: 로컬 환경 설정 (본인 머신)

```bash
# 1. kubeconfig 설정
mkdir -p ~/.kube
cp ~/Downloads/zcp-kubeconfig.yaml ~/.kube/config
chmod 600 ~/.kube/config

# 2. 연결 확인
export KUBECONFIG=~/.kube/config
kubectl cluster-info
kubectl get nodes
```

### ✅ Phase 2: Docker 이미지 빌드 및 푸시 (본인 머신)

```bash
# 1. SK 레지스트리 로그인
docker login registry.zcp.sk.com

# 2. 이미지 빌드 및 푸시
cd /path/to/career_qa_v0.3\ 2
bash deployment/k8s/build-image.sh v1.0.0 registry.zcp.sk.com/myteam
```

### ✅ Phase 3: ZCP 클러스터 설정 (ZCP 환경)

```bash
# 1. 클러스터 접근 확인
kubectl config current-context

# 2. 네임스페이스 생성
kubectl create namespace career-qa

# 3. 레지스트리 Secret 생성
kubectl create secret docker-registry sk-registry-credentials \
  --docker-server=registry.zcp.sk.com \
  --docker-username=<YOUR_USERNAME> \
  --docker-password=<YOUR_PASSWORD> \
  -n career-qa
```

### ✅ Phase 4: 민감 정보 Secret 생성 (ZCP 환경)

```bash
# 대화형 스크립트 실행 (권장)
bash deployment/k8s/create-secrets.sh
```

### ✅ Phase 5: 매니페스트 배포 (ZCP 환경)

```bash
# 1. 검증
kubectl apply -f deployment/k8s/ --dry-run=client -n career-qa

# 2. 배포
bash deployment/k8s/deploy.sh
```

### ✅ Phase 6: 배포 검증 (ZCP 환경)

```bash
bash deployment/k8s/health-check.sh
```

### ✅ Phase 7: 수동 테스트 (ZCP 환경)

```bash
# 1. 테스트 Job 생성
kubectl create job --from=cronjob/career-qa-daily test-run-1 -n career-qa

# 2. 로그 확인
POD_NAME=$(kubectl get pods -n career-qa -l job-name=test-run-1 -o jsonpath='{.items[0].metadata.name}')
kubectl logs $POD_NAME -n career-qa -f

# 3. 결과 확인
kubectl get job test-run-1 -n career-qa
```

---

## 주요 명령어

| 목적 | 명령어 |
|------|--------|
| 클러스터 연결 | `kubectl cluster-info` |
| 네임스페이스 생성 | `kubectl create namespace career-qa` |
| Secret 생성 | `bash deployment/k8s/create-secrets.sh` |
| CronJob 배포 | `kubectl apply -f deployment/k8s/cronjob.yaml` |
| CronJob 상태 | `kubectl describe cronjob career-qa-daily -n career-qa` |
| 수동 테스트 | `kubectl create job --from=cronjob/career-qa-daily test-run-1 -n career-qa` |
| 로그 확인 | `kubectl logs <pod-name> -n career-qa -f` |

---

## 문제 해결

| 문제 | 해결 |
|------|------|
| connection refused | `export KUBECONFIG=~/.kube/config` 확인 |
| unauthorized | kubeconfig 재발급 요청 |
| ImagePullBackOff | `docker push` 재시도, Secret 검증 |
| CrashLoopBackOff | `kubectl logs --previous` 확인 |

---

**시작하기**: Phase 1부터 순서대로 진행하세요!

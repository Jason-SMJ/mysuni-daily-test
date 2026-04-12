#!/bin/bash

# Career QA Daily Batch - Kubernetes Secrets 생성 스크립트
# 용도: ZCP 환경에 필요한 민감한 정보를 안전하게 생성

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

NAMESPACE="career-qa"
SECRET_NAME="career-qa-secrets"

print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# 1. 네임스페이스 확인/생성
print_header "Step 1: Namespace 확인/생성"

if kubectl get namespace $NAMESPACE >/dev/null 2>&1; then
    print_success "네임스페이스 '$NAMESPACE' 이미 존재"
else
    print_info "네임스페이스 '$NAMESPACE' 생성 중..."
    kubectl create namespace $NAMESPACE
    print_success "네임스페이스 '$NAMESPACE' 생성 완료"
fi

# 2. 기존 Secret 확인
print_header "Step 2: 기존 Secret 확인"

if kubectl get secret $SECRET_NAME -n $NAMESPACE >/dev/null 2>&1; then
    print_warning "Secret '$SECRET_NAME'이 이미 존재합니다"
    read -p "덮어쓰시겠습니까? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "작업 취소됨"
        exit 0
    fi
    kubectl delete secret $SECRET_NAME -n $NAMESPACE
    print_info "기존 Secret 삭제됨"
fi

# 3. 민감한 정보 입력
print_header "Step 3: 민감한 정보 입력"

read -sp "Azure OpenAI API Key: " AZURE_OPENAI_KEY
echo
read -sp "Slack Bot Token (xoxb-...): " SLACK_BOT_TOKEN
echo
read -p "Slack Channel ID (C...): " SLACK_CHANNEL_ID
read -p "Slack DM User ID (U..., 선택): " SLACK_DM_USER_ID
read -p "MySuni ID: " MYSUNI_ID
read -sp "MySuni Password: " MYSUNI_PWD
echo
read -p "HTTPS Proxy URL (선택): " HTTPS_PROXY

# 4. Secret 생성
print_header "Step 4: Secret 생성"

CMD="kubectl create secret generic $SECRET_NAME \
  --from-literal=azure-openai-key='$AZURE_OPENAI_KEY' \
  --from-literal=slack-bot-token='$SLACK_BOT_TOKEN' \
  --from-literal=slack-channel-id='$SLACK_CHANNEL_ID'"

if [ -n "$SLACK_DM_USER_ID" ]; then
    CMD="$CMD --from-literal=slack-dm-user-id='$SLACK_DM_USER_ID'"
fi

CMD="$CMD --from-literal=mysuni-id='$MYSUNI_ID' \
  --from-literal=mysuni-pwd='$MYSUNI_PWD'"

if [ -n "$HTTPS_PROXY" ]; then
    CMD="$CMD --from-literal=https-proxy='$HTTPS_PROXY'"
fi

CMD="$CMD -n $NAMESPACE"

eval $CMD
print_success "Secret '$SECRET_NAME' 생성 완료"

# 5. 검증
print_header "Step 5: Secret 검증"

kubectl get secret $SECRET_NAME -n $NAMESPACE
echo ""
kubectl describe secret $SECRET_NAME -n $NAMESPACE

print_header "완료"
print_success "Secret 생성이 완료되었습니다"
print_info "다음 단계:"
echo "  1. 배포: bash deployment/k8s/deploy.sh"
echo "  2. 상태 확인: bash deployment/k8s/health-check.sh"

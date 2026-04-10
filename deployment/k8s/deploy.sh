#!/bin/bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="career-qa"
DEPLOYMENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$DEPLOYMENT_DIR/../.." && pwd)"

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed. Please install kubectl first."
    fi

    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster. Please check your kubeconfig."
    fi

    log_success "Prerequisites check passed"
}

# Create namespace
create_namespace() {
    log_info "Creating namespace: $NAMESPACE"

    if kubectl get namespace "$NAMESPACE" &> /dev/null; then
        log_warning "Namespace '$NAMESPACE' already exists. Skipping creation."
    else
        kubectl apply -f "$DEPLOYMENT_DIR/namespace.yaml"
        log_success "Namespace created"
    fi
}

# Create ServiceAccount and RBAC
create_rbac() {
    log_info "Creating ServiceAccount and RBAC..."

    kubectl apply -f "$DEPLOYMENT_DIR/service-account.yaml"
    log_success "ServiceAccount and RBAC created"
}

# Create or update Secrets
create_secrets() {
    log_info "Checking for Secrets..."

    if kubectl get secret career-qa-secrets -n "$NAMESPACE" &> /dev/null; then
        log_warning "Secret 'career-qa-secrets' already exists."
        log_info "To update secrets, run:"
        log_info "  kubectl delete secret career-qa-secrets -n $NAMESPACE"
        log_info "  kubectl create secret generic career-qa-secrets --from-literal=... -n $NAMESPACE"
    else
        log_error "Secret 'career-qa-secrets' not found."
        log_info "Please create the secret first:"
        log_info "  kubectl create secret generic career-qa-secrets \\"
        log_info "    --from-literal=azure-openai-key='...' \\"
        log_info "    --from-literal=slack-bot-token='...' \\"
        log_info "    --from-literal=slack-channel-id='...' \\"
        log_info "    --from-literal=slack-dm-user-id='...' \\"
        log_info "    --from-literal=mysuni-id='...' \\"
        log_info "    --from-literal=mysuni-pwd='...' \\"
        log_info "    --from-literal=https-proxy='...' \\"
        log_info "    -n $NAMESPACE"
    fi
}

# Create registry credentials secret
create_registry_secret() {
    log_info "Checking for Docker registry credentials..."

    if kubectl get secret sk-registry-credentials -n "$NAMESPACE" &> /dev/null; then
        log_warning "Secret 'sk-registry-credentials' already exists. Skipping."
    else
        log_warning "Secret 'sk-registry-credentials' not found."
        log_info "Please create the registry credentials secret:"
        log_info "  kubectl create secret docker-registry sk-registry-credentials \\"
        log_info "    --docker-server=registry.zcp.sk.com \\"
        log_info "    --docker-username=<USERNAME> \\"
        log_info "    --docker-password=<PASSWORD> \\"
        log_info "    --docker-email=<EMAIL> \\"
        log_info "    -n $NAMESPACE"
    fi
}

# Deploy CronJob
deploy_cronjob() {
    log_info "Deploying CronJob..."

    kubectl apply -f "$DEPLOYMENT_DIR/cronjob.yaml"
    log_success "CronJob deployed"
}

# Verify deployment
verify_deployment() {
    log_info "Verifying deployment..."

    log_info "CronJob status:"
    kubectl get cronjob career-qa-daily -n "$NAMESPACE" || log_warning "CronJob not found"

    log_info "ServiceAccount status:"
    kubectl get sa -n "$NAMESPACE" || log_warning "ServiceAccount not found"

    log_success "Deployment verification complete"
}

# Show next steps
show_next_steps() {
    echo ""
    log_info "Deployment completed!"
    echo ""
    log_info "Next steps:"
    echo "  1. Verify secrets are created:"
    echo "     kubectl get secret -n $NAMESPACE"
    echo ""
    echo "  2. Check CronJob details:"
    echo "     kubectl describe cronjob career-qa-daily -n $NAMESPACE"
    echo ""
    echo "  3. View the next scheduled time:"
    echo "     kubectl get cronjob career-qa-daily -n $NAMESPACE -o jsonpath='{.status.lastScheduleTime}'"
    echo ""
    echo "  4. Manual test run:"
    echo "     kubectl create job --from=cronjob/career-qa-daily test-run-1 -n $NAMESPACE"
    echo ""
    echo "  5. View logs:"
    echo "     kubectl logs -f -n $NAMESPACE -l app=career-qa"
    echo ""
}

# Main execution
main() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  ZCP Daily Batch Deployment Script${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""

    check_prerequisites
    create_namespace
    create_rbac
    create_secrets
    create_registry_secret
    deploy_cronjob
    verify_deployment
    show_next_steps

    log_success "All deployment steps completed!"
}

main "$@"

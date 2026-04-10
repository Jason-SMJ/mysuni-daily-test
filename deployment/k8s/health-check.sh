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

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Check kubectl connection
check_kubectl() {
    log_info "Checking kubectl connection..."

    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        return 1
    fi

    local cluster_name=$(kubectl config current-context)
    log_success "Connected to cluster: $cluster_name"
    return 0
}

# Check namespace
check_namespace() {
    log_info "Checking namespace: $NAMESPACE"

    if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
        log_error "Namespace '$NAMESPACE' does not exist"
        return 1
    fi

    log_success "Namespace '$NAMESPACE' exists"
    return 0
}

# Check CronJob
check_cronjob() {
    log_info "Checking CronJob status..."

    if ! kubectl get cronjob career-qa-daily -n "$NAMESPACE" &> /dev/null; then
        log_error "CronJob 'career-qa-daily' not found"
        return 1
    fi

    local suspended=$(kubectl get cronjob career-qa-daily -n "$NAMESPACE" -o jsonpath='{.spec.suspend}')
    if [ "$suspended" = "true" ]; then
        log_warning "CronJob is suspended"
        return 0
    fi

    log_success "CronJob 'career-qa-daily' is active"

    local schedule=$(kubectl get cronjob career-qa-daily -n "$NAMESPACE" -o jsonpath='{.spec.schedule}')
    log_info "Schedule: $schedule"

    local last_schedule=$(kubectl get cronjob career-qa-daily -n "$NAMESPACE" -o jsonpath='{.status.lastScheduleTime}' 2>/dev/null || echo "None")
    log_info "Last scheduled: $last_schedule"

    return 0
}

# Check ServiceAccount
check_serviceaccount() {
    log_info "Checking ServiceAccount..."

    if ! kubectl get serviceaccount career-qa-sa -n "$NAMESPACE" &> /dev/null; then
        log_error "ServiceAccount 'career-qa-sa' not found"
        return 1
    fi

    log_success "ServiceAccount 'career-qa-sa' exists"
    return 0
}

# Check Secrets
check_secrets() {
    log_info "Checking Secrets..."

    if ! kubectl get secret career-qa-secrets -n "$NAMESPACE" &> /dev/null; then
        log_error "Secret 'career-qa-secrets' not found"
        return 1
    fi

    log_success "Secret 'career-qa-secrets' exists"

    if ! kubectl get secret sk-registry-credentials -n "$NAMESPACE" &> /dev/null; then
        log_warning "Secret 'sk-registry-credentials' not found (optional)"
        return 0
    fi

    log_success "Secret 'sk-registry-credentials' exists"
    return 0
}

# Check recent Job history
check_job_history() {
    log_info "Checking recent Job history..."

    local jobs=$(kubectl get jobs -n "$NAMESPACE" --sort-by=.metadata.creationTimestamp 2>/dev/null | tail -5)

    if [ -z "$jobs" ]; then
        log_warning "No jobs found yet"
        return 0
    fi

    echo "$jobs"
    return 0
}

# Check Pod status
check_pods() {
    log_info "Checking Pod status..."

    local pods=$(kubectl get pods -n "$NAMESPACE" 2>/dev/null | grep -E "Running|Failed|Error" || true)

    if [ -z "$pods" ]; then
        log_info "No active pods"
        return 0
    fi

    echo "$pods"
    return 0
}

# Get latest logs
get_latest_logs() {
    log_info "Checking latest Pod logs..."

    local latest_pod=$(kubectl get pods -n "$NAMESPACE" --sort-by=.metadata.creationTimestamp -o jsonpath='{.items[-1].metadata.name}' 2>/dev/null || echo "")

    if [ -z "$latest_pod" ]; then
        log_warning "No pods found"
        return 0
    fi

    log_info "Latest Pod: $latest_pod"
    log_info "Pod logs (last 20 lines):"
    echo "---"
    kubectl logs "$latest_pod" -n "$NAMESPACE" --tail=20 2>/dev/null || log_warning "Could not retrieve logs"
    echo "---"

    return 0
}

# Show summary
show_summary() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  Health Check Summary${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    log_info "Useful commands:"
    echo "  # View CronJob details"
    echo "  kubectl describe cronjob career-qa-daily -n $NAMESPACE"
    echo ""
    echo "  # Manual test run"
    echo "  kubectl create job --from=cronjob/career-qa-daily test-run-1 -n $NAMESPACE"
    echo ""
    echo "  # View all resources"
    echo "  kubectl get all -n $NAMESPACE"
    echo ""
    echo "  # Stream logs"
    echo "  kubectl logs -f -n $NAMESPACE -l app=career-qa"
    echo ""
    echo "  # Check resource usage"
    echo "  kubectl top pods -n $NAMESPACE"
    echo ""
}

# Main execution
main() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  ZCP Daily Batch Health Check${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""

    local failed=0

    check_kubectl || failed=$((failed + 1))
    echo ""
    check_namespace || failed=$((failed + 1))
    echo ""
    check_serviceaccount || failed=$((failed + 1))
    echo ""
    check_secrets || failed=$((failed + 1))
    echo ""
    check_cronjob || failed=$((failed + 1))
    echo ""
    check_job_history
    echo ""
    check_pods
    echo ""
    get_latest_logs

    show_summary

    if [ $failed -eq 0 ]; then
        log_success "All health checks passed!"
        echo ""
        exit 0
    else
        log_error "$failed health check(s) failed!"
        echo ""
        exit 1
    fi
}

main "$@"

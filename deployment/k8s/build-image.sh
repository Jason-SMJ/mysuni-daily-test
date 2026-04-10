#!/bin/bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default configuration
REGISTRY="${REGISTRY:-registry.zcp.sk.com}"
IMAGE_NAME="${IMAGE_NAME:-career-qa/career-qa}"
VERSION="${1:-latest}"
BUILD_CONTEXT="${BUILD_CONTEXT:-.}"
DOCKERFILE="${DOCKERFILE:-./Dockerfile}"

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

# Show usage
show_usage() {
    cat << EOF
Usage: $0 [VERSION] [REGISTRY] [IMAGE_NAME]

Arguments:
  VERSION       Image version/tag (default: latest)
  REGISTRY      Docker registry URL (default: registry.zcp.sk.com)
  IMAGE_NAME    Image name (default: career-qa/career-qa)

Environment Variables:
  REGISTRY      Docker registry URL
  IMAGE_NAME    Image name
  BUILD_CONTEXT Build context directory (default: current dir)
  DOCKERFILE    Dockerfile path (default: ./Dockerfile)

Examples:
  # Build latest version
  $0

  # Build specific version
  $0 v1.0.0

  # Build with custom registry
  $0 v1.0.0 docker.io myteam/career-qa

EOF
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
    fi

    if ! docker ps &> /dev/null; then
        log_error "Cannot connect to Docker daemon. Please check Docker installation."
    fi

    log_success "Docker is available"
}

# Check Dockerfile
check_dockerfile() {
    log_info "Checking Dockerfile..."

    if [ ! -f "$DOCKERFILE" ]; then
        log_error "Dockerfile not found at $DOCKERFILE"
    fi

    log_success "Dockerfile found"
}

# Build Docker image
build_image() {
    log_info "Building Docker image..."
    log_info "Image: $REGISTRY/$IMAGE_NAME:$VERSION"

    docker build \
        -t "$REGISTRY/$IMAGE_NAME:$VERSION" \
        -t "$REGISTRY/$IMAGE_NAME:latest" \
        -f "$DOCKERFILE" \
        "$BUILD_CONTEXT" || log_error "Docker build failed"

    log_success "Docker image built successfully"
}

# Test image locally (optional)
test_image_locally() {
    log_info "Testing image (checking entrypoint)..."

    docker run --rm "$REGISTRY/$IMAGE_NAME:$VERSION" --help &> /dev/null || true

    log_success "Image test completed"
}

# Login to registry
login_to_registry() {
    log_info "Checking Docker registry authentication..."

    if [ "$REGISTRY" = "docker.io" ] || [ "$REGISTRY" = "index.docker.io" ]; then
        log_warning "DockerHub registry detected"
        log_info "Please ensure you are logged in:"
        log_info "  docker login"
        return 0
    fi

    if ! docker images --digests | grep "$REGISTRY" &> /dev/null; then
        log_warning "Not authenticated to $REGISTRY"
        log_info "To authenticate, run:"
        log_info "  docker login $REGISTRY"
        return 0
    fi

    log_success "Authenticated to $REGISTRY"
}

# Push image to registry
push_image() {
    log_info "Pushing image to registry..."
    log_info "Target: $REGISTRY/$IMAGE_NAME:$VERSION"

    if ! docker push "$REGISTRY/$IMAGE_NAME:$VERSION"; then
        log_error "Failed to push image with tag '$VERSION'"
    fi

    if ! docker push "$REGISTRY/$IMAGE_NAME:latest"; then
        log_warning "Failed to push image with tag 'latest' (non-critical)"
    fi

    log_success "Image pushed successfully"
}

# Show image information
show_image_info() {
    log_info "Image information:"

    docker images "$REGISTRY/$IMAGE_NAME" | tail -1

    echo ""
    log_info "Image tags:"
    echo "  $REGISTRY/$IMAGE_NAME:$VERSION"
    echo "  $REGISTRY/$IMAGE_NAME:latest"
    echo ""
}

# Show next steps
show_next_steps() {
    echo ""
    log_info "Next steps:"
    echo ""
    echo "  1. Update cronjob.yaml with the image:"
    echo "     image: $REGISTRY/$IMAGE_NAME:$VERSION"
    echo ""
    echo "  2. Deploy to ZCP:"
    echo "     ./deployment/k8s/deploy.sh"
    echo ""
    echo "  3. Verify deployment:"
    echo "     ./deployment/k8s/health-check.sh"
    echo ""
}

# Main execution
main() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  Docker Image Build & Push${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""

    # Override with command line arguments
    if [ -n "$2" ]; then
        REGISTRY="$2"
    fi
    if [ -n "$3" ]; then
        IMAGE_NAME="$3"
    fi

    log_info "Configuration:"
    log_info "  Registry: $REGISTRY"
    log_info "  Image: $IMAGE_NAME"
    log_info "  Version: $VERSION"
    log_info "  Dockerfile: $DOCKERFILE"
    echo ""

    check_prerequisites
    check_dockerfile
    build_image
    test_image_locally
    show_image_info

    read -p "Push image to registry? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        login_to_registry
        push_image
        show_next_steps
        log_success "Build and push completed!"
    else
        log_warning "Push cancelled. Run 'docker push' manually when ready:"
        echo "  docker push $REGISTRY/$IMAGE_NAME:$VERSION"
        echo "  docker push $REGISTRY/$IMAGE_NAME:latest"
    fi
}

# Show help if requested
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    show_usage
    exit 0
fi

main "$@"

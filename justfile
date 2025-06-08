# Default registry if not set in environment
REGISTRY := "docker.io/username"

# Build Docker image with version tag
build:
    docker context use default
    docker build -t ${REGISTRY}/images.pype.dev:latest .

# Push Docker image with version tag
build-and-push:
    docker context use default
    just build
    docker push ${REGISTRY}/images.pype.dev:latest

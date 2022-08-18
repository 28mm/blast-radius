#! /bin/bash
IMAGE_NAME="blast-radius-fork-local"
MULTI_CPU=false
SCRIPT_DIR=$(dirname "$(readlink -f "${BASH_SOURCE[0]}")") # get the directory of this script
DOCKERFILE_DIR=$(dirname -- "$(readlink -f -- "$SCRIPT_DIR")") # get the parent directory of this script (the directory of the Dockerfile)

if [ "$1" != "" ]; then
  IMAGE_NAME=$1
fi

if [ "$2" == true ]; then
  MULTI_CPU=true
fi

if [ ! -e "$DOCKERFILE_DIR/Dockerfile" ]; then
  echo "File $DOCKERFILE_DIR/Dockerfile does not exist, so image $IMAGE_NAME could not be built. Exiting"
  exit 1
fi

if [ "$MULTI_CPU" == false ]; then
  echo "Building image $IMAGE_NAME without multi-cpu support. Your image will be saved locally."
  docker build -t "$IMAGE_NAME" "$DOCKERFILE_DIR"
else
  echo "Building image $IMAGE_NAME with multi-cpu support. Your image will be pushed remotely to Docker Hub and saved locally afterwards. "
  docker buildx build \
  --platform linux/arm64,linux/amd64,linux/amd64/v2,linux/ppc64le,linux/s390x,linux/386,linux/arm/v7,linux/arm/v6 \
  -t "$IMAGE_NAME" --push "$DOCKERFILE_DIR"
  docker pull "$IMAGE_NAME"
fi
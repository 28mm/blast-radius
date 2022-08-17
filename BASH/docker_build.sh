#! /bin/bash
IMAGE_NAME="blast-radius-fork"
MULTI_CPU=false
SCRIPT_DIR=$(dirname "$(readlink -f "${BASH_SOURCE[0]}")") # get the directory of this script
DOCKERFILE_DIR=$(dirname -- "$(readlink -f -- "$SCRIPT_DIR")")

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
  echo "Building image $IMAGE_NAME without multi-cpu support"
  docker build -t "$IMAGE_NAME" "$DOCKERFILE_DIR"
else
  echo "Building image $IMAGE_NAME with multi-cpu support"
  docker buildx build --platform linux/arm64,linux/amd64,linux/amd64/v2,linux/ppc64le,linux/s390x,linux/386,linux/arm/v7,linux/arm/v6 -t "$IMAGE_NAME" "$DOCKERFILE_DIR"
fi
#! /bin/bash

SCRIPT_DIR=$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")
BUILDFILE=$SCRIPT_DIR/docker_build.sh

IMAGE_NAME="blast-radius-fork"
ACCESS_PORT=5000
DETACHED=""

# first check if number of arguments to script is greater than 3 or not, if it is exit
if [ $# -gt 3 ]; then
    echo "$0 does not accept more than 3 arguments (image name, port, and detached flag). You have provided $# arguments."
    exit 1
fi

# if number of arguments is equal to 0
if [ $# -eq 0 ]; then
    echo "Using default image name: ${IMAGE_NAME} and default port: ${ACCESS_PORT} because no arguments were passed"
else
    if [ "$1" != "" ]; then
        IMAGE_NAME=$1
    fi
    if [ "$2" != "" ]; then
        ACCESS_PORT=$2
    fi
    if [ "$3" == "-d" ] || [ "$3" == "--detach" ]; then
        DETACHED=$3
    fi
fi

# check if image exists
if [[ "$(docker image inspect "$IMAGE_NAME" --format='exists')" == 'exists' ]]; then
#if [ "$(docker image inspect "$IMAGE_NAME" --format="$IMAGE_EXISTS"  ==  "$IMAGE_EXISTS")" ]; then
  echo "Running Docker Image: $IMAGE_NAME on $ACCESS_PORT $DETACHED"
  docker run --rm -it "$DETACHED" -p "$ACCESS_PORT":5000 -v "$(PWD)":/data:ro --security-opt apparmor:unconfined --cap-add=SYS_ADMIN "$IMAGE_NAME"
else
  echo "$IMAGE_NAME does not exist. Trying to rebuild the image using $BUILDFILE ..."

  if [ ! -e "$BUILDFILE" ]; then
    echo "File $BUILDFILE does not exist. Exiting"
    exit 1
  fi

  if [ ! -s "$BUILDFILE" ]; then
    echo "File $BUILDFILE is empty. Exiting"
    exit 1
  fi

  if [ ! -x "$BUILDFILE" ]; then
    echo "File $BUILDFILE is not executable. Exiting"
    echo "Hint: Try running 'chmod +x $BUILDFILE'"
    exit 1
  fi

  echo "Using $BUILDFILE to build image $IMAGE_NAME"
  $BUILDFILE "$IMAGE_NAME"

fi



#if [ "$(docker i Docker Image: $IMAGE_NAME echo $IMAGE_NAME)" ]; then
#    echo "Image $IMAGE_NAME exists"
#else
#    echo "Image $IMAGE_NAME does not exist"
#    echo "docker buildx build --platform linux/amd64,linux/arm64,linux/arm/v7 -t $IMAGE_NAME . format="$IMAGE_EXISTS"  ==  "$IMAGE_EXISTS")" ]; then
#  echo "Running Docker Image: $IMAGE_NAME"
#  docker run --rm -it -p $PORT:5000 -v "$(pwd)":/data:ro --security-opt apparmor:unconfined --cap-add=SYS_ADMIN $IMAGE_NAME
#fi
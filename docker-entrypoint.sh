#!/bin/bash

set -e

# prepare overlayFS
# shamelessly taken from https://gist.github.com/detunized/7c8fc4c37b49c5475e68ef9574587eee

mkdir -p /tmp/overlay && \
mount -t tmpfs tmpfs /tmp/overlay && \
mkdir -p /tmp/overlay/{upper,work} && \
mkdir -p /workdir-rw && \
mount -t overlay overlay -o lowerdir=/workdir,upperdir=/tmp/overlay/upper,workdir=/tmp/overlay/work /workdir-rw

cd /workdir-rw

# if we are given arguments we assume
#  $1 will be "--serve" and
#  $2 the actual stack to run tf in
# so we have to init terraform in the given directory $2
# if $2 is no directory just fall back to the default and run
# terraform init in /workdir

if [ -z ${2+x} ];
  then
    echo;
  else
    if [ -d "$2" ];
      then
        cd $2;
        terraform get --update=true
        terraform init
        cd /workdir-rw
    fi
fi

terraform init -input=false

blast-radius $1 $2 $3

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
#  $1 will be "--port" or "--serve" and
#  $2 will be the actual port or directory to server. Please explicitly state serve and custom port if it is NOT 5000 to work with serve together.
#  $3 will be "--serve" with "--port" as $2 and with port offset of 1 or 2 i.e. 5001 and 5002
#  $4 the actual stack to run tf in with "--port" as $2
# so we have to init terraform in the given directory $2 or $4
# if $1 and $3 is no port and directory just fall back to the default and run i.e. without parameters
# terraform init in /workdir are we meant to run terraform in a sub-directory?
if { [ $# == 2 ] || [ $# == 4 ]; } && { [ -d "$2" ] || [ -d "$4" ]; }; then
    if [ $# == 2 ] && [ $1 == "--serve" ]; then
        cd $2
    elif [ $# == 4 ] && [ $1 == "--port" ] && [ $3 == "--serve" ]; then
        cd $4
    else
        echo "wrong params"
    fi
else
        echo "Specify --serve directory"
fi

# is terraform already initialized? 
[ -d '.terraform' ] && terraform get --update=true

# re-initialize anyway.
terraform init -input=false

# it's possible that we're in a sub-directory. leave.
cd /workdir-rw

# okay, we should be good to go.
blast-radius $1 $2 $3 $4 $5

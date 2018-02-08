#!/bin/sh

set -e

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
        terraform init;
        cd /workdir
    fi
fi

terraform init

blast-radius $1 $2 $3

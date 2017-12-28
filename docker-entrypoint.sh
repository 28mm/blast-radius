#!/bin/sh

set -e

echo $1 $2 $3

terraform init
blast-radius $1 $2 $3


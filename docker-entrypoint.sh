#!/bin/sh

set -e

terraform init

blast-radius $1 $2 $3


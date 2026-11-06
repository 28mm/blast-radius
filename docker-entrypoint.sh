#!/bin/sh
set -e

# Preserve the existing Docker shorthand for commands such as `--serve`.
if [ -n "${1}" ] && [ "${1}" != "blast-radius" ]; then
  set -- blast-radius "$@"
fi

# Inside the container
# Need to create the upper and work dirs inside a tmpfs.
# Otherwise OverlayFS complains about AUFS folders.
# Source: https://gist.github.com/detunized/7c8fc4c37b49c5475e68ef9574587eee
mkdir -p /tmp/overlay && \
mount -t tmpfs tmpfs /tmp/overlay && \
mkdir -p /tmp/overlay/upper && \
mkdir -p /tmp/overlay/work && \
mkdir -p /data-rw && \
mount -t overlay overlay -o lowerdir=/data,upperdir=/tmp/overlay/upper,workdir=/tmp/overlay/work /data-rw

# change to the overlayFS
cd /data-rw

/bin/docker-terraform-init.sh /data-rw

if [ -n "${CHDIR:-}" ]; then
  case "$CHDIR" in
    /*)
      config_dir=$CHDIR
      ;;
    *)
      config_dir=/data-rw/$CHDIR
      ;;
  esac
else
  config_dir=/data-rw
fi

cd "$config_dir"

# Let's go!
exec "$@"

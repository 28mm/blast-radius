#!/bin/sh
set -eu

workspace=${1:?usage: docker-terraform-init.sh WORKSPACE}
mode=${BLAST_RADIUS_TERRAFORM_INIT:-auto}

case "$mode" in
  auto|always|never)
    ;;
  *)
    echo "Invalid BLAST_RADIUS_TERRAFORM_INIT value '$mode'; expected auto, always, or never." >&2
    exit 64
    ;;
esac

if [ -n "${CHDIR:-}" ]; then
  case "$CHDIR" in
    /*)
      config_dir=$CHDIR
      ;;
    *)
      config_dir=$workspace/$CHDIR
      ;;
  esac
else
  config_dir=$workspace
fi

if [ ! -d "$config_dir" ]; then
  echo "Terraform configuration directory does not exist: $config_dir" >&2
  exit 66
fi

if [ -n "${TF_DATA_DIR:-}" ]; then
  case "$TF_DATA_DIR" in
    /*)
      cache_dir=$TF_DATA_DIR
      ;;
    *)
      cache_dir=$config_dir/$TF_DATA_DIR
      ;;
  esac
else
  cache_dir=$config_dir/.terraform
fi

has_configuration=false
for terraform_file in "$config_dir"/*.tf; do
  if [ -f "$terraform_file" ]; then
    has_configuration=true
    break
  fi
done

has_cache=false
if [ -d "$cache_dir" ] && find "$cache_dir" -mindepth 1 -maxdepth 1 -print -quit | grep -q .; then
  has_cache=true
fi

should_initialize=false
case "$mode" in
  always)
    should_initialize=true
    ;;
  never)
    echo "Skipping Terraform init because BLAST_RADIUS_TERRAFORM_INIT=never."
    ;;
  auto)
    if [ "$has_configuration" = false ]; then
      echo "Skipping Terraform init because no .tf files were found in $config_dir."
    elif [ "$has_cache" = true ]; then
      echo "Skipping Terraform init because cached Terraform data exists at $cache_dir."
    else
      should_initialize=true
    fi
    ;;
esac

if [ "$should_initialize" = true ]; then
  echo "Initializing Terraform in directory: $config_dir"
  terraform -chdir="$config_dir" init -backend=false -input=false
fi

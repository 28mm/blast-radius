# Docker Terraform initialization

The container controls Terraform initialization with
`BLAST_RADIUS_TERRAFORM_INIT`. The default is `auto`.

| Mode | Behavior |
| --- | --- |
| `auto` | Skip when no `.tf` files exist or a non-empty Terraform data cache exists; initialize otherwise. |
| `always` | Run initialization on every container start. |
| `never` | Never run initialization. |

Initialization uses:

```sh
terraform init -backend=false -input=false
```

Disabling the backend prevents a visualization from contacting or modifying a
configured state backend. The input flag makes startup deterministic.

## Cache and directory detection

The configuration directory is the mounted workspace unless `CHDIR` selects a
subdirectory. An absolute `CHDIR` is used directly; a relative value is
resolved from the workspace.

The cache is:

1. `TF_DATA_DIR`, resolved from the configuration directory when relative; or
2. `<configuration-directory>/.terraform`.

In `auto` mode, any non-empty cache is reused without running `terraform get`
or `terraform init`. This allows already-downloaded private modules to work
without making the container authenticate to their source again.

Example:

```sh
docker run --rm -it -p 5000:5000 \
  -e BLAST_RADIUS_TERRAFORM_INIT=never \
  -e CHDIR=stacks/application \
  -v "$(pwd):/data:ro" \
  --security-opt apparmor:unconfined \
  --cap-add=SYS_ADMIN \
  ianyliu/blast-radius-fork
```

## Cached provider compatibility

Terraform provider binaries are operating-system and architecture specific.
A `.terraform` directory created on macOS or Windows, or on a different CPU
architecture, may contain providers that cannot execute in the Linux
container. Cached Terraform modules are source files and generally do not
have this restriction.

If a reused cache lacks compatible Linux providers, use
`BLAST_RADIUS_TERRAFORM_INIT=always` so the container can populate its writable
overlay with compatible providers. This does not modify the read-only host
mount. Private provider and module sources may still require a mounted
Terraform CLI configuration or credentials.

For DOT-only visualization, leave the default `auto` mode: startup skips
Terraform automatically when the mounted directory has no `.tf` files.

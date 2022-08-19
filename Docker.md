<h1 align="center">Docker</h1>

[privileges]: https://docs.docker.com/engine/reference/run/#runtime-privilege-and-linux-capabilities
[overlayfs]: https://wiki.archlinux.org/index.php/Overlay_filesystem

## Table of Contents
- [Preqrequisites](#prerequisites)
- [Run Docker Containers](#run-docker-containers)
- [Docker Configurations](#docker-configurations)
- [Docker Subdirectories](#docker--subdirectories)
- [Image Building](#image-building)

[//]: # (- [Aliases]&#40;#aliases&#41; )

## Prerequisites
* Install Docker
  * [Linux](https://docs.docker.com/desktop/install/linux-install/)
  * [Mac](https://docs.docker.com/desktop/install/mac-install/)
  * [Windows](https://docs.docker.com/desktop/install/windows-install/)

You can also install [Docker Desktop](https://www.docker.com/products/docker-desktop/), a more intuitive GUI for Docker.

Verify Docker is installed in your Terminal: ```docker info```

## Run Docker Containers

Launch *Blast Radius* for a local directory by manually running:

sh, zsh, bash, etc. (Linux recommended):
```sh
docker run --rm -it -p 5000:5000 \
  -v $(pwd):/data:ro \
  --security-opt apparmor:unconfined \
  --cap-add=SYS_ADMIN \
  ianyliu/blast-radius-fork
```

Windows PowerShell:
```powershell
docker run --rm -it -p 5000:5000 `
  -v ${pwd}:/data:ro `
  --security-opt apparmor:unconfined `
  --cap-add=SYS_ADMIN `
  ianyliu/blast-radius-fork
```

If you do not have the Docker image, it will be automatically pulled for you. You can also [build the image yourself]
(#image-building).

A slightly more customized variant of this is also available as an example
[docker-compose.yml](./Docker/docker-compose.yml) use case for Workspaces.

## Docker configurations

<details><summary></summary>

*Terraform* module links are saved as _absolute_ paths in relative to the
project root (note `.terraform/modules/<uuid>`). Given these paths will vary
betwen Docker and the host, we mount the volume as read-only, assuring we don't
ever interfere with your real environment.

However, in order for *Blast Radius* to actually work with *Terraform*, it needs
to be initialized. To accomplish this, the container creates an [overlayfs][]
that exists within the container, overlaying your own, so that it can operate
independently. To do this, certain runtime privileges are required --
specifically `--cap-add=SYS_ADMIN`. 

> Note: This is considered a security risk by some, so be sure you understand how this works. 

For more information on how this works and what it means for your host, check
out the [runtime privileges][privileges] documentation.
</details>

## Docker & Subdirectories

<details>
<summary></summary>

If you organized your *Terraform* project using stacks and modules,
*Blast Radius* must be called from the project root and reference them as
subdirectories -- don't forget to prefix `--serve`!

For example, let's create a Terraform `project` with the following:

```txt
$ tree -d
`-- project/
    |-- modules/
    |   |-- foo
    |   |-- bar
    |   `-- dead
    `-- stacks/
        `-- beef/
             `-- .terraform
```

It consists of 3 modules `foo`, `bar` and `dead`, followed by one `beef` stack.
To apply *Blast Radius* to the `beef` stack, you would want to run the container
with the following:

```sh
$ cd project
$ docker run --rm -it -p 5000:5000 \
    -v $(pwd):/data:ro \
    --security-opt apparmor:unconfined \
    --cap-add=SYS_ADMIN \
    ianyliu/blast-radius-fork --serve stacks/beef
```
</details>

## Image Building

If you'd like to build your own Docker image after making changes to Blast Radius, you can build it in 2 ways:
1. Normal Build

To execute a normal build, navigate (using commands like `cd`) to the root of your modified Blast Radius project in your terminal. 
Make sure you have the Dockerfile in the root of your project.
Now run:

```
docker build -t imagename .
``` 

Replace imagename with the name you'd like to give your image. 

Once the build is complete you can run it in the Terraform directory you'd like visualize.

sh, zsh, bash, etc. (Linux recommended):
```sh
docker run --rm -it -p 5000:5000 \
  -v $(pwd):/data:ro \
  --security-opt apparmor:unconfined \
  --cap-add=SYS_ADMIN \
  imagename
```

Windows PowerShell:
```powershell
docker run --rm -it -p 5000:5000 `
  -v ${pwd}:/data:ro `
  --security-opt apparmor:unconfined `
  --cap-add=SYS_ADMIN `
  imagename
```

Go to http://127.0.0.1:5000/ to view the visualization.

2. Multi-CPU Build

If you'd like to build your own Docker image that supports multiple computer architectures like AMD64, ARM, etc. 
You can use the following command: 

```sh
docker buildx build \ 
--platform  \  
linux/arm64,linux/amd64,linux/amd64/v2,linux/ppc64le,linux/s390x,linux/386,linux/arm/v7,linux/arm/v6 \ 
-t imagename\  
--load . 
```

Architectures `linux/riscv64,linux/mips64le,linux/mips64` are supported by buildx, 
but Python 3.8 Alpine image does not support these architectures.
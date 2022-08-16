& docker buildx build -f ..\Dockerfile `
--platform `
linux/arm64,linux/amd64,linux/amd64/v2,linux/ppc64le,linux/s390x,linux/386,linux/arm/v7,linux/arm/v6 `
-t blast-radius-fork .
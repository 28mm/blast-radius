ARG TF_VERSION=1.15.8
ARG PYTHON_VERSION=3.10

FROM hashicorp/terraform:${TF_VERSION} AS terraform

FROM python:${PYTHON_VERSION}-alpine
ARG TF_VERSION
ARG PYTHON_VERSION

LABEL org.opencontainers.image.title="blast-radius-fork" \
      org.opencontainers.image.description="Interactive Terraform graph visualizer" \
      org.opencontainers.image.source="https://github.com/Ianyliu/blast-radius-fork" \
      org.opencontainers.image.version="${TF_VERSION}"

ENV BLAST_RADIUS_TERRAFORM_VERSION=${TF_VERSION}

RUN apk add --no-cache graphviz ttf-freefont git \
    && python -m pip install --upgrade --no-cache-dir pip ply

COPY --from=terraform /bin/terraform /bin/terraform
COPY ./docker-entrypoint.sh /bin/docker-entrypoint.sh
COPY ./docker-terraform-init.sh /bin/docker-terraform-init.sh
RUN chmod +x /bin/docker-entrypoint.sh /bin/docker-terraform-init.sh \
    && terraform version \
    && dot -V

WORKDIR /src
COPY . .
RUN pip install -e . \
    && blast-radius --help >/dev/null

WORKDIR /data

ENTRYPOINT ["/bin/docker-entrypoint.sh"]
CMD ["blast-radius", "--serve"]

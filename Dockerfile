ARG TF_VERSION=0.12.12
ARG PYTHON_VERSION=3.7

FROM hashicorp/terraform:$TF_VERSION AS terraform

FROM python:$PYTHON_VERSION-alpine
RUN pip install -U pip ply \
 && apk add --update --no-cache graphviz ttf-freefont

COPY --from=terraform /bin/terraform /bin/terraform
COPY ./docker-entrypoint.sh /bin/docker-entrypoint.sh
RUN chmod +x /bin/docker-entrypoint.sh

WORKDIR /src
COPY . .
RUN pip install -e .

WORKDIR /data

ENTRYPOINT ["/bin/docker-entrypoint.sh"]
CMD ["blast-radius", "--serve"]

ARG TF_VERSION=0.12.20
ARG PYTHON_VERSION=3.7

FROM python:$PYTHON_VERSION-alpine



FROM hashicorp/terraform:$TF_VERSION AS terraform
FROM ibmterraform/terraform-provider-ibm-docker AS provideribm
FROM nibhart1/hcl2json:hcl2json AS hcl2json

FROM python:$PYTHON_VERSION-alpine
RUN pip install -U pip ply \
 && apk add --update --no-cache graphviz ttf-freefont
RUN pip install graphviz
COPY --from=terraform /bin/terraform /bin/terraform
COPY --from=provideribm /go/bin/terraform-provider-ibm_v* /root/.terraform.d/plugins/linux_amd64/terraform-provider-ibm
COPY --from=hcl2json /go/bin/hcl2json /bin/hcl2json
COPY ./docker-entrypoint.sh /bin/docker-entrypoint.sh
RUN chmod +x /bin/docker-entrypoint.sh

WORKDIR /bin
RUN ls

WORKDIR /src
COPY . .
RUN pip install -e .
WORKDIR /data

ENTRYPOINT ["/bin/docker-entrypoint.sh"]
CMD ["blast-radius", "--serve"]





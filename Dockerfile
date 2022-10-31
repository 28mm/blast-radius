ARG TF_VERSION=1.3.3
ARG PYTHON_VERSION=3.10

FROM hashicorp/terraform:$TF_VERSION AS terraform

FROM python:$PYTHON_VERSION-alpine
RUN pip install -U --no-cache-dir pip ply \
    && apk add --update --no-cache graphviz ttf-freefont \
    && apk upgrade

COPY --from=terraform /bin/terraform /bin/terraform
COPY ./Docker/docker-entrypoint.sh /bin/docker-entrypoint.sh
RUN chmod +x /bin/docker-entrypoint.sh

WORKDIR /src
COPY . .
RUN pip install -e .

# comment out 2 lines below to optimize build speed
WORKDIR /data
RUN echo $(timeout 15 blast-radius --serve --port 5001; test $? -eq 124) > /output.txt

ENTRYPOINT ["/bin/docker-entrypoint.sh"]
CMD ["blast-radius", "--serve"]
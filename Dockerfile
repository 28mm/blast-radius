#howto build docker image (from working-directory having blast-radius source)
#  docker build -t blast-radius .
#
#howto run docker container (from working-directory having *.tf files)
#  docker run -it --rm -p 5000:5000 -v $(pwd):/workdir blast-radius

#use latest tag for now for terraform version
FROM hashicorp/terraform:latest

#expose blast-radius port
EXPOSE 5000

#install graphviz and py dependencies
RUN apk --update --no-cache add graphviz font-bitstream-type1 && \
    apk add --no-cache python3 && \
    python3 -m ensurepip && \
    rm -r /usr/lib/python*/ensurepip && \
    pip3 install --upgrade pip setuptools && \
    if [ ! -e /usr/bin/pip ]; then ln -s pip3 /usr/bin/pip ; fi && \
    if [[ ! -e /usr/bin/python ]]; then ln -sf /usr/bin/python3 /usr/bin/python; fi && \
    rm -r /root/.cache

#create package from source
WORKDIR /src
COPY . .
RUN pip3 install -e .

#set up entrypoint script
RUN chmod +x ./docker-entrypoint.sh

#set up runtime workdir for tf files
WORKDIR /workdir
ENTRYPOINT ["/src/docker-entrypoint.sh"]
CMD ["--serve"]
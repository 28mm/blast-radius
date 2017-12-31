#!/bin/sh

set -e

cd $1

# Download terraform zip
terraform_url=https://releases.hashicorp.com/terraform/$TF_VERSION/terraform_${TF_VERSION}_linux_amd64.zip

echo "Downloading $terraform_url."
curl -o terraform.zip $terraform_url

# Unzip and install
unzip terraform.zip
mv terraform /usr/local/bin
rm terraform.zip




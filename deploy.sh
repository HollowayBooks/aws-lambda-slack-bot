#!/bin/bash
set -exuo pipefail

make build
sam package --template-file template.yaml --output-template-file packaged.yaml --s3-bucket $1
sam deploy --template-file ./packaged.yaml --stack-name $1 --capabilities CAPABILITY_IAM


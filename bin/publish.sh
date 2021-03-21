#!/bin/bash
BASEDIR=$(dirname $(realpath "$0"))
echo "$BASEDIR"
docker build -t valuation $BASEDIR/..
docker tag valuation:latest 174232563144.dkr.ecr.ap-southeast-1.amazonaws.com/yueda:latest
docker push 174232563144.dkr.ecr.ap-southeast-1.amazonaws.com/yueda

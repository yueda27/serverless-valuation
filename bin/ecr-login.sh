#!/bin/bash

credentials=$(aws ecr get-login --registry-id 174232563144 --no-include-email)
eval "$credentials"
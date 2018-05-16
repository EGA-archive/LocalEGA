#!/bin/bash

set -e

source /ega/bootstrap/boot.sh

cd /ega/private/

git init
git add .
git commit -m "Initialize configuration repository"

cd /ega/config

./mvnw clean spring-boot:run
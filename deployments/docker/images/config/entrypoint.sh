#!/bin/bash

set -e

source /ega/bootstrap/boot.sh

cd /ega/config

git init
git add .
git commit -m "Initialize configuration repository"

cd /ega/server

./mvnw clean spring-boot:run

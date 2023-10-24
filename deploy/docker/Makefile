SHELL := /bin/bash

all: up

.PHONY: up down ps logs restart image exec handler reset-storage

up:
	@docker-compose up -d

ps:
	@docker-compose ps

down:
	@docker-compose down -v

logs:
	@docker-compose logs -f

restart:
	@docker-compose restart


####################################################
## Docker Image for the Handler
####################################################

IMAGE_ARGS=
# eg --no-cache

image:
	cd ../../ingestion && \
	docker build -f Dockerfile \
		     --build-arg LEGA_UID=$(shell id -u lega || id -u) \
		     --build-arg LEGA_GID=$(shell id -g lega || id -g) \
		     $(IMAGE_ARGS) \
		     --tag egarchive/lega:latest \
		     .


####################################################
# Cleaning docker images

exec: CMD=bash
handler: CMD=python -m code /etc/ega/lega.ini
handler exec:
	@docker-compose exec handler $(CMD)

reset-storage:
	-rm -r data/{inbox,staging,vault,vault.bkp}/*

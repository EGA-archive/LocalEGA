PROJECT_NAME=crg
ARGS=
SHELL := /bin/bash
TAG=$(shell git rev-parse --short HEAD)

.PHONY: help bootstrap private up down clean ps bootstrap-image bootstrap-dev nfs nfs-down

help:
	@echo -e "Usage: make <target>\n"
	@echo -e "where <target> is: 'bootstrap', 'up', 'ps', 'down', 'clean'\n\n"
	@echo -e "If you use 'bootstrap-dev', passwords are replaced with the value 'dummy'\n"

bootstrap-image: 
	@echo "Checking the egarchive/lega image"
	@docker pull egarchive/lega

# If DEPLOY_DEV is yes, we use dummy passwords
bootstrap-dev: ENVS=--env DEPLOY_DEV=yes
private/lega.yml private bootstrap bootstrap-dev:
	@echo "Running the bootstrap script in egarchive/lega"
	@docker run --rm -it \
		    -v /dev/urandom:/dev/random \
                    ${ENVS} \
		    -v ${PWD}:/ega \
		    --entrypoint /ega/bootstrap/run.sh \
		    -v ${PWD}/../extras/rabbitmq_hash.py:/tmp/rabbitmq_hash.py \
		    -v ~/_cryptor/crypt4gh:/root/.local/lib/python3.6/site-packages/crypt4gh \
		    egarchive/lega --prefix $(PROJECT_NAME) ${ARGS}

up: private/lega.yml
	@docker-compose --log-level ERROR -f $< up -d

# up: private/lega.yml
# 	@docker-compose --log-level ERROR -f $< up -d mq db vault
# 	@sleep 6
# 	@docker-compose --log-level ERROR -f $< up -d inbox ingest verify finalize outgest streamer

down:
	-@docker-compose --log-level ERROR down -v

ps:
	@docker-compose --log-level ERROR ps

clean:
	rm -rf .env private


nfs:
	mkdir -p nfsshare
	if mount | grep -q 130.239.81.131; then : ; else mount -v -t nfs -o vers=4 130.239.81.131:/var/nfsshare $(shell pwd)/nfsshare; fi

nfs-down:
	-umount $(shell pwd)/nfsshare
	rmdir nfsshare

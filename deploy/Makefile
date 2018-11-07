PROJECT_NAME=crg
ARGS=
SHELL := /bin/bash
TAG=$(shell git rev-parse --short HEAD)

.PHONY: help bootstrap private up down clean ps bootstrap-image bootstrap-dev

help:
	@echo "Usage: make <target>\n"
	@echo "where <target> is: 'bootstrap', 'up', 'ps', 'down', 'clean'\n\n"
	@echo "If you use 'bootstrap-dev', passwords are replaced with the value 'dummy'\n"

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
		    -v ~/_cryptor/crypt4gh:/root/.local/lib/python3.6/site-packages/crypt4gh \
		    egarchive/lega --prefix $(PROJECT_NAME) ${ARGS}

up: private/lega.yml
	@docker-compose --log-level ERROR -f $< up -d db mq vault inbox
	@sleep 5 # Allow mq to be ready with its users, so other containers can consume from the queues
	@docker-compose --log-level ERROR -f $< up -d ingest verify finalize outgest streamer

down:
	-@docker-compose --log-level ERROR down -v

ps:
	@docker-compose --log-level ERROR ps

clean:
	rm -rf .env private

# up: private/lega.yml
# 	@docker stack deploy --compose-file $< lega

# down:
# 	-@docker stack rm lega

# ps:
# 	@docker stack services lega

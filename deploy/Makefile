PROJECT_NAME=crg
ARGS=
SHELL := /bin/bash

.PHONY: help bootstrap private up down clean ps

help:
	@echo "Usage: make <target>\n"
	@echo "where <target> is: 'bootstrap', 'up', 'ps', 'down', 'clean', or 'clean-all'\n\n"
	@echo "If you use 'bootstrap-dev', passwords are replaced with the value 'dummy'\n"

# If DEPLOY_DEV is yes, we use dummy passwords
bootstrap-dev: ENVS=--env DEPLOY_DEV=yes
private/lega.yml private bootstrap bootstrap-dev:
	@echo "Checking the egarchive/lega image"
	@docker pull egarchive/lega
	@echo "Running the bootstrap script in egarchive/lega"
	@docker run --rm -it \
		    -v /dev/urandom:/dev/random \
                    ${ENVS} \
		    -v ${PWD}:/ega \
		    --entrypoint /ega/bootstrap/run.sh \
		    egarchive/lega --prefix $(PROJECT_NAME) ${ARGS}


up: private/lega.yml
	@docker-compose -f $< up -d

down:
	-@[[ -f private/lega.yml ]] && docker-compose -f private/lega.yml down -v

ps:
	@docker-compose ps

clean-volumes:
	-docker volume rm $(PROJECT_NAME)_{db,inbox,s3}
	-docker volume prune -f

clean:
	rm -rf .env private

clean-all: clean clean-volumes

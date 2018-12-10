ARGS=

.PHONY: help bootstrap private network up down clean ps clean-volumes clean-all

help:
	@echo "Usage: make <target>\n"
	@echo "where <target> is: 'bootstrap', 'up' 'ps', 'down', 'network' or 'clean'\n"

# If DEPLOY_DEV is yes, we use dummy passwords
bootstrap-dev: ENVS=--env DEPLOY_DEV=yes
private/cega.yml private/lega.yml private bootstrap bootstrap-dev:
	@docker run --rm -it \
		    -v /dev/urandom:/dev/random \
                    ${ENVS} \
		    -v ${PWD}:/ega \
		    -v ${PWD}/../extras/generate_pgp_key.py:/tmp/generate_pgp_key.py \
		    -v ${PWD}/../extras/rabbitmq_hash.py:/tmp/rabbitmq_hash.py \
		    --entrypoint /ega/bootstrap/boot.sh \
		    nbisweden/ega-base:dev ${ARGS}

network:
	@docker network inspect cega &>/dev/null || docker network create cega &>/dev/null

up:network private/cega.yml private/lega.yml
	@docker-compose -f private/cega.yml -f private/lega.yml up -d

# Omiting just one service from the setup, to avoid bootstrap flags
up-omit:network private/cega.yml private/lega.yml
	@docker-compose -f private/cega.yml -f private/lega.yml up -d --scale ${service}=0

clean-volumes:
	docker volume rm lega_db lega_inbox lega_s3

ps:
	@docker-compose ps

down: #.env
	@[[ -f private/cega.yml ]] && [[ -f private/lega.yml ]] && docker-compose down -v || echo "No recipe to bring containers down\nHave you bootstrapped? (ie make bootstrap)"

clean:
	rm -rf .env private
	-docker network rm cega &>/dev/null

clean-all: clean clean-volumes

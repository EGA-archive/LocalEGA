ARGS=

.PHONY: help bootstrap private network up down clean ps clean-volumes clean-all

help:
	@echo "Usage: make <target>\n"
	@echo "where <target> is: 'bootstrap', 'up' 'ps', 'down', 'network' or 'clean'\n"

# If DEPLOY_DEV is yes, we use dummy passwords
bootstrap: ENVS=--env DEPLOY_DEV=yes
private/lega.yml private bootstrap:
	@docker run --rm -it \
		    -v /dev/urandom:/dev/random \
                    ${ENVS} \
		    -v ${PWD}:/ega \
		    -v ${PWD}/../extras/generate_pgp_key.py:/tmp/generate_pgp_key.py \
		    --entrypoint /ega/bootstrap/boot.sh \
		    nbisweden/ega-base:latest ${ARGS}

up-omit: OMIT=--scale ${service}=0
up up-omit:private/lega.yml
	@docker-compose -f $< up -d ${OMIT}

clean-volumes:
	docker volume rm lega_db lega_inbox lega_s3

ps:
	@docker-compose ps

down: #.env
	@[[ -f private/lega.yml ]] && docker-compose down -v || echo "No recipe to bring containers down\nHave you bootstrapped? (ie make bootstrap)"

clean:
	rm -rf .env private

clean-all: clean clean-volumes

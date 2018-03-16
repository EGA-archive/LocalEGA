ARGS=

.PHONY: help bootstrap private network up all-up down clean ps

help:
	@echo "Usage: make <target>\n"
	@echo "where <target> is: 'bootstrap', 'up', 'all-up', 'ps', 'down', 'network' or 'clean'\n"

private/cega.yml private/ega_swe1.yml private/ega_fin1.yml private bootstrap:
	@docker run --rm -it \
		    -v /dev/urandom:/dev/random \
		    -v ${PWD}:/ega \
		    -v ${PWD}/../../extras/db.sql:/tmp/db.sql \
		    -v ${PWD}/../../extras/generate_pgp_key.py:/tmp/generate_pgp_key.py \
		    --entrypoint /ega/bootstrap/boot.sh \
		    nbisweden/ega-base ${ARGS}

network:
	@docker network inspect cega &>/dev/null || docker network create cega &>/dev/null

up:network private/cega.yml private/ega_swe1.yml private/ega_fin1.yml
	@docker-compose -f private/cega.yml -f private/ega_swe1.yml -f private/ega_fin1.yml \
	 		up -d \
			cega-mq cega-users cega-eureka mq-swe1 db-swe1 inbox-swe1 vault-swe1 ingest-swe1 keys-swe1 mq-fin1 inbox-fin1 db-fin1 vault-fin1 ingest-fin1 keys-fin1

all-up:
	@docker-compose -f private/cega.yml -f private/ega_swe1.yml -f private/ega_fin1.yml up -d

ps:
	@docker-compose ps

down: #.env
	@[[ -f private/cega.yml ]] && [[ -f private/ega_swe1.yml ]] && [[ -f private/ega_fin1.yml ]] && docker-compose down -v || echo "No recipe to bring containers down\nHave you bootstrapped? (ie make bootstrap)"

clean:
	rm -rf .env private
	-docker network rm cega &>/dev/null

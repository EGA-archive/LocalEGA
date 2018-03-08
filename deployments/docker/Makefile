ARGS=

.PHONY: help bootstrap private network up all-up down clean ps

help:
	@echo "Usage: make <target>\n"
	@echo "where <target> is: 'bootstrap', 'up', 'all-up', 'ps', 'down', 'network' or 'clean'\n"

private bootstrap:
	@docker run --rm -it \
		    -v ${PWD}:/ega \
		    -v ${PWD}/../../extras/db.sql:/tmp/db.sql \
		    -v ${PWD}/../../extras/generate_pgp_key.py:/tmp/generate_pgp_key.py \
		    nbisweden/ega-bootstrap ${ARGS}

network:
	@docker network inspect cega &>/dev/null || docker network create cega &>/dev/null

up:network
	@docker-compose up -d cega-mq cega-users mq-swe1 db-swe1 inbox-swe1 vault-swe1 ingest-swe1 keys-swe1 mq-fin1 inbox-fin1 db-fin1 vault-fin1 ingest-fin1 keys-fin1

all-up:
	@docker-compose -f private/cega.yml -f private/ega_swe1.yml -f private/ega_fin1.yml up -d

ps:
	@docker-compose ps

down: #.env
	@docker-compose down -v

clean:
	rm -rf .env private
	-docker network rm cega &>/dev/null


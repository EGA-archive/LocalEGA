ARGS=

.PHONY: help bootstrap private network up all-up down clean ps

help:
	@echo "Usage: make <target>\n"
	@echo "where <target> is: 'bootstrap', 'up', 'all-up', 'ps', 'down', or 'clean'\n"

private bootstrap:
	@docker run --rm -it -v ${PWD}:/ega -v ${PWD}/../../extras/db.sql:/tmp/db.sql nbisweden/ega-bootstrap ${ARGS}

network:
	@docker network inspect cega &>/dev/null || docker network create cega &>/dev/null

up:network
	@docker-compose -f private/cega/ega.yml up -d cega-mq cega-users
	@docker-compose -f private/swe1/ega.yml up -d mq-swe1 db-swe1 inbox-swe1 vault-swe1 ingest-swe1 keys-swe1
	@docker-compose -f private/fin1/ega.yml up -d mq-fin1 inbox-fin1

all-up:
	@docker-compose -f private/cega/ega.yml -f private/swe1/ega.yml -f private/fin1/ega.yml up -d

ps:
	@docker-compose ps

down: #.env
	@docker-compose down -v

clean:
	rm -rf .env private
	-docker network rm cega &>/dev/null


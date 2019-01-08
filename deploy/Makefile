ARGS=

.PHONY: help bootstrap private network up down clean ps clean-volumes clean-all

help:
	@echo "Usage: make <target>\n"
	@echo "where <target> is: 'bootstrap', 'up' 'ps', 'down', 'network' or 'clean'\n"

# If DEPLOY_DEV is yes, we use dummy passwords
bootstrap-dev: DEV="DEPLOY_DEV=yes "
private/lega.yml private bootstrap bootstrap-dev:
	@:$(if CEGA_CONNECTION,,$(error CEGA_CONNECTION is not set))
	@:$(if CEGA_USERS_CREDS,,$(error CEGA_USERS_CREDS is not set))
	@${DEV}bootstrap/boot.sh ${ARGS}


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

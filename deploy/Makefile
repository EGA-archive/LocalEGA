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
	@${DEV}bootstrap/boot.sh ${ARGS} || { cat private/.err; exit 1; }


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

purge:
	@:$(if CEGA_CONNECTION,,$(error CEGA_CONNECTION is not set))
	@python ../extras/rabbitmq/purge.py --connection ${CEGA_CONNECTION}


ensure-system-up:
	@echo "Ensure the system is up"
	@sleep 60

# Note: "sleep 60" will be replaced with a script that checks for open port, mq settings, etc.
# It might be a good idea to run it in the same network as the containers.
# docker run --rm -it --network=lega_lega \
#        -v ${PWD}/integration/ensure_system_up.sh:/ensure_system_up.sh \
#        nbisweden/ega-base /ensure_system_up.sh

# For the moment, we simply do sleep 60, because we need
# - the inbox notification server up
# - the rabbitmq shovel to CentralEGA (the federated queue can be late, it doesn't hurt)
# - the key server (the java spring needs the 60 seconds, other 10 is enough)

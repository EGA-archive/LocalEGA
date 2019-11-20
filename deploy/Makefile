SHELL := /bin/bash
OPENSSL=openssl
ARGS=

.PHONY: help bootstrap private network up down clean ps clean-volumes clean-all prepare images install-bootstrap-packages

help:
	@echo "Usage: make <target>\n"
	@echo "where <target> is: 'bootstrap', 'up' 'ps', 'down', 'network' or 'clean'\n"

# If DEPLOY_DEV is yes, we use dummy passwords
bootstrap-dev: export DEPLOY_DEV=yes
.env private/lega.yml private bootstrap bootstrap-dev:
	@bootstrap/run.sh ${ARGS} || { cat private/.err; exit 1; }


up: .env private/lega.yml
	@docker-compose up -d ${OMIT}

clean-volumes:
	docker volume rm lega_db lega_inbox lega_s3
	-docker volume rm lega_inbox-s3

ps:
	@docker-compose ps

down: #.env
	@[[ -f private/lega.yml ]] && docker-compose down -v || echo -e "No recipe to bring containers down\nHave you bootstrapped? (ie make bootstrap)"

clean:
	rm -rf .env private
	make -C bootstrap/certs clean

clean-all: clean clean-volumes

preflight-check:
	@echo "Ensure the system is up"
	sleep 80

# Note: "sleep 80" will be replaced with a script that checks for open port, mq settings, etc.
# It might be a good idea to run it in the same network as the containers.
# docker run --rm -it --network=lega_lega \
#        -v ${PWD}/bootstrap/ensure_system_up.sh:/ensure_system_up.sh \
#        egarchive/lega-base /ensure_system_up.sh

# For the moment, we simply do sleep 60, because we need
# - the rabbitmq shovel to CentralEGA (the federated queue can be late, it doesn't hurt)
# - the key server (slow setup with java spring)


images:
	make -C images

# That's for Travis
install-bootstrap-packages:
	pip3 install git+https://github.com/EGA-archive/crypt4gh.git
	pip3 install pika==1.0.1

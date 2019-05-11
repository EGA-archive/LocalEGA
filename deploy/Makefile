SHELL := /bin/bash

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
	sleep 150

# Note: "sleep 150" will be replaced with a script that checks for open port, mq settings, etc.
# It might be a good idea to run it in the same network as the containers.
# docker run --rm -it --network=lega_lega \
#        -v ${PWD}/bootstrap/ensure_system_up.sh:/ensure_system_up.sh \
#        egarchive/lega-base /ensure_system_up.sh

# For the moment, we simply do sleep 60, because we need
# - the rabbitmq shovel to CentralEGA (the federated queue can be late, it doesn't hurt)
# - the key server (the java spring needs 97 seconds, 10 are enough for the other)


# Decrypt the encoded data from the repository
# That is, some users private ssh keys and the database of fake CentralEGA Users
prepare: ../tests/_common/dummy.sec ../tests/_common/john.sec ../tests/_common/jane.sec ../tests/_common/users.json

%.sec: %.sec.enc
	openssl enc -aes-256-cbc -d -in $< -out $@ -k ${REPO_PASSWORD}
	chmod 400 $@

%.json: %.json.enc
	openssl enc -aes-256-cbc -d -in $< -out $@ -k ${REPO_PASSWORD}

images:
	make -C images

# That's for Travis
install-bootstrap-packages:
	pip3 install git+https://github.com/NBISweden/LocalEGA-cryptor.git
	pip3 install pgpy pika==1.0.1

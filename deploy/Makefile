SHELL := /bin/bash
OPENSSL=openssl
ARGS=
SELECTED=
HOSTNAME_DOMAIN=
#HOSTNAME_DOMAIN=.localega

.PHONY: help bootstrap up down clean ps clean-volumes clean-all erase purge

help:
	@echo "Usage: make <target>\n"
	@echo "where <target> is: 'bootstrap', 'up', 'ps', 'down', or 'clean'\n"

# If DEPLOY_DEV is yes, we use dummy passwords
bootstrap-dev: export DEPLOY_DEV=yes
bootstrap bootstrap-dev:
	@make -C bootstrap -s
	@echo "Boostrapping done."


# [[ -x $(readlink ${OPENSSL}) ]] && echo "${OPENSSL} is not executable. Adjust the setting with --openssl" && exit 3


up: bootstrap/private/lega.yml
	@docker-compose up -d ${SELECTED}


clean-volumes:
	docker volume rm lega_db lega_inbox lega_s3
	-docker volume rm lega_inbox-s3

ps:
	@docker-compose ps

down:
	@[[ -f bootstrap/private/lega.yml ]] && docker-compose down -v || echo -e "No recipe to bring containers down\nHave you bootstrapped? (ie make bootstrap)"

clean:
	make -C bootstrap clean

clean-all: clean clean-volumes

preflight-check:
	@echo "Ensure the system is up"
	sleep 20

# Note: "sleep 20" will be replaced with a script that checks for open port, mq settings, etc.
# It might be a good idea to run it in the same network as the containers.
# docker run --rm -it --network=lega_lega \
#        -v ${PWD}/bootstrap/ensure_system_up.sh:/ensure_system_up.sh \
#        egarchive/lega-base /ensure_system_up.sh

# For the moment, we simply do sleep 20, because we need
# the rabbitmq shovel to CentralEGA (the federated queue can be late, it doesn't hurt)



####################################################
## Base Image
####################################################

IMAGE_ARGS=
# eg --no-cache
# eg --build-arg LEGA_GID=1000

image:
	cd .. && \
	docker build -f Dockerfile $(IMAGE_ARGS) --tag egarchive/lega-base:latest .


####################################################
# Cleaning images

define remove_dangling
	docker images $(1) -f "dangling=true" -q | uniq | while read n; do docker rmi -f $$n; done
endef

erase:
	@$(call remove_dangling,egarchive/lega-base)

purge:
	@$(call remove_dangling,)


SHELL := /bin/bash
ARGS=
SELECTED=
HOSTNAME_DOMAIN=
#HOSTNAME_DOMAIN=.localega

.PHONY: up down clean ps clean-volumes clean-all image erase purge preflight-check

up: .env
	@docker-compose up -d ${SELECTED}

private/lega.yml .env:
	make -C bootstrap -s

clean-volumes:
	docker volume rm lega_db lega_inbox lega_s3
	-docker volume rm lega_inbox-s3

ps:
	@docker-compose ps

down:
	@[[ -f private/lega.yml ]] && docker-compose down -v || echo -e "No recipe to bring containers down\nHave you bootstrapped? (ie make bootstrap)"

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

logs:
	@docker-compose logs -f
# 	@docker-compose logs -f logs

####################################################
## Base Image
####################################################

IMAGE_ARGS=
# eg --no-cache
# eg --build-arg LEGA_GID=1000

image:
	cd .. && \
	docker build -f Dockerfile \
		     --build-arg LEGA_UID=$(shell id -u) \
		     $(IMAGE_ARGS) \
		     --tag egarchive/lega-base:latest \
		     .


####################################################
# Cleaning docker images

define remove_dangling
	docker images $(1) -f "dangling=true" -q | uniq | while read n; do docker rmi -f $$n; done
endef

erase:
	@$(call remove_dangling,egarchive/lega-base)

purge:
	@$(call remove_dangling,)


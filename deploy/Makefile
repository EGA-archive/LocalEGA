SHELL := /bin/bash
ARGS=
SELECTED=
HOSTNAME_DOMAIN=
#HOSTNAME_DOMAIN=.localega

.PHONY: up down clean ps clean-volumes clean-all images erase purge preflight-check

lega-up: SELECTED=inbox ingest cleanup db backup1 backup2 save2db archive-db mq dispatcher
lega-up up: .env private/lega.yml
	@docker-compose up -d ${SELECTED}

private/lega.yml .env:
	make -C bootstrap -s

clean-volumes:
	docker volume rm lega_db lega_inbox lega_archive_db lega_vault lega_vault_bkp

ps:
	@docker-compose ps

down:
	@[[ -f private/lega.yml ]] && docker-compose down -v \
	 || echo -e "No recipe to bring containers down\nHave you bootstrapped? (ie make bootstrap)"

preflight-check:
	@echo "Ensure the system is up"
	sleep 20

# Note: "sleep 20" will be replaced with a script that checks for open port, mq settings, etc.
# It might be a good idea to run it in the same network as the containers.
# docker run --rm -it --network=lega_lega \
#        -v ${PWD}/bootstrap/ensure_system_up.sh:/ensure_system_up.sh \
#        egarchive/lega-base /ensure_system_up.sh
#
# For the moment, we simply do sleep 20, because we need
# the rabbitmq shovel to CentralEGA (the federated queue can be late, it doesn't hurt)

logs:
	@docker-compose logs -f $(SELECTED)
# 	@docker-compose logs -f logs

# Restart all but the CentralEGA stubs
restart: SELECTED=ingest backup1 backup2 cleanup dispatcher save2db db mq archive-db inbox
restart:
	@docker-compose restart $(SELECTED)


####################################################
## Docker Images
####################################################

IMAGE_ARGS=
MQ_ARGS=
DB_ARGS=
# eg --no-cache, or --build-arg LEGA_GID=1000

.PHONY: images image mq-image db-image
images: image mq-image db-image

image:
	cd ../ingestion && \
	docker build -f Dockerfile \
		     --build-arg LEGA_UID=$(shell id -u) \
		     $(IMAGE_ARGS) \
		     --tag egarchive/lega-base:latest \
		     .

mq-image:
	cd ../ingestion/mq && \
	docker build -f Dockerfile \
		     $(MQ_ARGS) \
		     --tag egarchive/lega-mq:latest \
		     .

db-image:
	cd ../ingestion/db && \
	docker build -f Dockerfile \
		     $(DB_ARGS) \
		     --tag egarchive/lega-db:latest \
		     .


####################################################
# Cleaning docker images

define remove_dangling
	docker images $(1) -f "dangling=true" -q | uniq | while read n; do docker rmi -f $$n; done
endef

erase:
	@$(call remove_dangling,egarchive/lega-*)

purge:
	@$(call remove_dangling,)


####################################################
# Checking the archive DB

dbshell: private/secrets/archive-db.lega
	@chmod 600 $(CURDIR)/private/certs/save2db.sec.pem
	@psql "postgres://lega:$(file <$<)@localhost:15432/lega?sslmode=verify-ca&sslcert=$(CURDIR)/private/certs/save2db.cert.pem&sslkey=$(CURDIR)/private/certs/save2db.sec.pem&sslrootcert=$(CURDIR)/private/certs/CA.save2db.cert.pem"

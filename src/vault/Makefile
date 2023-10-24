HOSTNAME := $(shell hostname)
DB_DATA := $(shell pwd)/data
ETC_DB := $(shell pwd)


#DB_PORT := 127.0.0.1:15432
DB_PORT := 15432
SERVICE := vault-db
PG_VERSION := 15

IMG=fega/vault-db:latest
PG_SU_PASSWORD=change-me-please-it-is-important
DATABASE_NAME=ega

all: build

$(DB_DATA):
	mkdir -p $@
$(DB_DATA)/$(PG_VERSION):
	mkdir -p $@
	chown -R 999.999 $@ # that the postgres user and group in the container


image-build: ARGS+=--target BUILD
image-%: VERSION=
image-%:
	docker build $(ARGS) -t fega/vault-db:$*$(VERSION) .


up: ENVVARS=-e PGDATA=/ega/data
up: MOUNTPOINTS=-v $(DB_DATA)/$(PG_VERSION):/ega/data
up: MOUNTPOINTS+=-v $(ETC_DB)/pg.conf:/etc/ega/pg.conf
up: MOUNTPOINTS+=-v $(ETC_DB)/pg_hba.conf:/etc/ega/pg_hba.conf
up: MOUNTPOINTS+=-v /etc/ega/nss:/ega/cache/nss
up: MOUNTPOINTS+=-v /etc/ega/authorized_keys:/ega/cache/authorized_keys


up: ENTRYPOINT=--entrypoint postgres $(IMG) -c config_file=/etc/ega/pg.conf

ifdef DEBUG
up: ENTRYPOINT=--entrypoint /bin/sleep $(IMG) 365d
else
up: CAPABILITIES=--cap-drop ALL
endif

NETWORKS=--network fega-internal

up: EXTRA=--shm-size=1g

up:
	docker run -d --rm \
	-p "$(DB_PORT):5432" \
	$(MOUNTPOINTS) \
	$(ENVVARS) \
	$(NETWORKS) \
	$(LOGS) \
	$(EXTRA) \
	--hostname "$(SERVICE)" \
	--name "$(SERVICE)" \
	--user postgres \
	$(ENTRYPOINT)

exec-root: DOCKER_USER=--user root
exec exec-root: CMD=bash
exec exec-root:
	-docker exec -it $(DOCKER_USER) $(SERVICE) $(CMD)

down:
	-docker stop $(SERVICE)
	-docker rm $(SERVICE)

logs:
	docker logs -f $(SERVICE)

rm:
	rm -rf $(DB_DATA)/$(PG_VERSION)

###########################

build: | $(DB_DATA)/$(PG_VERSION)
build: MOUNTPOINTS=
build: ENVVARS=

build: MOUNTPOINTS+=-v $(DB_DATA)/$(PG_VERSION):/ega/data
build: MOUNTPOINTS+=-v $(shell pwd)/build.sh:/ega/build.sh
build: MOUNTPOINTS+=-v $(shell pwd)/initdb.d:/ega/initdb.d
build: ENVVARS+=-e PGDATA=/ega/data
build: ENVVARS+=-e POSTGRES_PASSWORD=$(PG_SU_PASSWORD)
build: ENVVARS+=-e POSTGRES_DB=$(DATABASE_NAME)

ifdef DEBUG
build: ENTRYPOINT=-d --entrypoint /bin/sleep
build: CMD=356d
else
build: ENTRYPOINT=-it --entrypoint /ega/build.sh
endif
build:
	docker run --rm \
	$(MOUNTPOINTS) \
	$(ENVVARS) \
	--hostname "$(SERVICE)-build" \
	--name "$(SERVICE)-build" \
	$(ENTRYPOINT) $(IMG) $(CMD)

build-exec:
	-docker exec -it --user root "$(SERVICE)-build" bash

build-down:
	-docker stop $(SERVICE)-build
	-docker rm $(SERVICE)-build


rebuild: down rm build up


###########################

export PGUSER=postgres
export PGPASSWORD=$(PG_SU_PASSWORD)
export PGDATABASE=$(DATABASE_NAME)
export PGHOST=localhost
export PGPORT=$(DB_PORT)



# psql:
# 	docker exec -it $(SERVICE) psql -d $(DATABASE_NAME)
psql:
	@psql


indexes:
	@psql < initdb.d/later/3-indexes.sql

re-index:
	@psql < initdb.d/later/4-reindex.sql

cache-triggers:
	@psql < initdb.d/later/5-nss-triggers.sql

nss:
	@psql \
	-c 'SELECT * FROM fs.make_nss_users(); SELECT * FROM fs.make_nss_passwords(); SELECT * FROM fs.make_nss_groups(); SELECT fs.make_authorized_keys(ut.id) FROM public.user_table ut;'


wait:
	@sleep 3

world: rebuild wait subscriptions


logpath:
	docker inspect $(SERVICE) | jq -r '.[0].LogPath'


reboot: down wait up


redefine-%:
	@psql < initdb.d/$*
redefine-later-%:
	@psql < initdb.d/later/$*

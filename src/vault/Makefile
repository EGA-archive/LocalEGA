
DB_DATA := $(shell pwd)/../../deploy/docker/data/vault-db
ETC_DB := $(shell pwd)
SERVICE=vault-db
IMG=fega/vault-db:latest
PG_SU_PASSWORD=change-me-please-it-is-important
DATABASE_NAME=ega

all: latest

$(DB_DATA):
	mkdir -p $@
	chown -R 999.999 $@ # that the postgres user and group in the container

build: ARGS+=--target BUILD
build latest:
	docker build $(ARGS) -t fega/vault-db:$@ .

###########################

init: | $(DB_DATA)
init: MOUNTPOINTS=
init: ENVVARS=

init: MOUNTPOINTS+=-v $(DB_DATA):/ega/data
init: MOUNTPOINTS+=-v $(shell pwd)/build.sh:/ega/build.sh
init: MOUNTPOINTS+=-v $(shell pwd)/initdb.d:/ega/initdb.d
init: ENVVARS+=-e PGDATA=/ega/data
init: ENVVARS+=-e POSTGRES_PASSWORD=$(PG_SU_PASSWORD)
init: ENVVARS+=-e POSTGRES_DB=$(DATABASE_NAME)

ifdef DEBUG
init: ENTRYPOINT=-d --entrypoint /bin/sleep
init: CMD=356d
else
init: ENTRYPOINT=-it --entrypoint /ega/build.sh
endif
init:
	docker run --rm \
	$(MOUNTPOINTS) \
	$(ENVVARS) \
	--hostname "$(SERVICE)-build" \
	--name "$(SERVICE)-build" \
	$(ENTRYPOINT) $(IMG) $(CMD)

down:
	-docker stop $(SERVICE)-build
	-docker rm $(SERVICE)-build

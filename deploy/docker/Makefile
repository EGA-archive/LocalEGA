SHELL := /bin/bash

LEGA_UID := $(shell id -u lega)
LEGA_GID := $(shell id -g lega)

#############################
## Build docker images
#############################

define error-lega-gid-message
Please specify the group id via the LEGA_GID variable.
For example, by calling "make $@ LEGA_UID=$$(id -g lega)"
endef

image-inbox:
ifeq ($(LEGA_GID),)
	$(error $(error-lega-gid-message))
endif
	make -C ../../src/inbox latest LEGA_GID=$(LEGA_GID)

define error-lega-ugid-message
Please specify the user and group ids via the LEGA_UID/LEGA_GID variable.
For example, by calling "make $@ LEGA_UID=$$(id -u lega) LEGA_GID=$$(id -g lega)"
endef


image-handler:
ifeq ($(LEGA_UID),)
	$(error $(error-lega-ugid-message))
endif
ifeq ($(LEGA_GID),)
	$(error $(error-lega-ugid-message))
endif
	make -C ../../src/handler latest LEGA_UID=$(LEGA_UID) LEGA_GID=$(LEGA_GID)

image-vault:
	make -C ../../src/vault latest

images: image-inbox image-handler image-vault


#############################
## Initialize the database
#############################
init-vault:
ifeq ("$(wildcard pg_vault_su_password)","")
	$(error 'Please specify the superuser password file "pg_vault_su_password"')
endif
	make -C ../../src/vault init DB_DATA=$(shell pwd)/data/vault-db PG_SU_PASSWORD=$(file < pg_vault_su_password)

# Connect to the database from the host machine
export PGHOST=localhost
export PGPORT=5432
export PGUSER=postgres
export PGPASSWORD=$(file < pg_vault_su_password)
export PGDATABASE=ega
psql:
	psql


#############################
## Utility targets
#############################

down:
	docker-compose down -v
logs:
	docker-compose logs -f
ps:
	docker-compose ps

clean:
	-rm -rf data/{vault,vault.bkp,staging,inbox}/*
	-rm -rf data/vault-db
	-rm -f data/example.txt.c4gh data/example.txt

#############################
## Distribution
#############################

# we need to sort to return the files in the desired order
SQL_FILES=$(sort $(notdir $(wildcard ../../src/distribution/src/db/*.sql)))

echo:
	@echo $(SQL_FILES)

load: $(SQL_FILES:%=load-%)

load-%:
	psql < ../../src/distribution/src/db/$*

nss-users:
	psql -c 'SELECT * FROM nss.make_users();'
nss-passwords:
	psql -c 'SELECT * FROM nss.make_passwords();'
nss-groups:
	psql -c 'SELECT * FROM nss.make_groups();'
nss-keys:
	psql -c 'SELECT nss.make_authorized_keys(r.db_uid) FROM public.requesters r;'
nss: nss-users nss-passwords nss-groups nss-keys



#############################
## Upload example
#############################

data/example.txt.c4gh: data/example.txt
	crypt4gh encrypt --recipient_pk service.key.pub < $< > $@

data/example.txt:
	dd if=/dev/urandom bs=1024 count=2 > $@

example: data/example.txt.c4gh

sftp:
	sftp -P 9000 john@localhost

permission:
	curl http://localhost:8080/permission/jane/EGAD90000000123

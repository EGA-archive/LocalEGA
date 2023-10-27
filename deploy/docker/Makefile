SHELL := /bin/bash


define error-inbox-lega-message
Please specify the group id via the LEGA_GID variable.
For example, by calling "make $@ LEGA_GID=$$(id -g lega)"
endef

ARCH=$(shell uname -m)
ifeq ($(ARCH), arm64) # reset for MacOS
	ARCH=aarch64
endif

image-inbox:
ifeq ($(LEGA_GID),)
	$(error $(error-inbox-lega-message))
endif
	make -C ../../src/inbox latest LEGA_GID=$(LEGA_GID) ARCH=$(ARCH)

image-handler:
	make -C ../../src/handler latest

image-vault:
	make -C ../../src/vault latest

images: image-inbox image-handler image-vault

confs:
	for f in *.sample; do cp $$f $${f//.sample/}; done

## Initialize the database
init-vault:
ifeq ("$(wildcard pg_vault_su_password)","")
	$(error 'Please specify the superuser password file "pg_vault_su_password"')
endif
	make -C ../../src/vault init DB_DATA=$(shell pwd)/data/vault-db PG_SU_PASSWORD=$(file < pg_vault_su_password)


#############################
## Utility targets
#############################

down:
	docker-compose down -v
logs:
	docker-compose logs -f
ps:
	docker-compose ps



psql: export PGHOST=localhost
psql: export PGPORT=5432
psql: export PGUSER=postgres
psql: export PGPASSWORD=$(file < pg_vault_su_password)
psql: export PGDATABASE=ega
psql:
	psql



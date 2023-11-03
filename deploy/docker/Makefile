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

clean:
	-rm -rf data/{vault,vault.bkp,staging,inbox}/*
	-rm -rf data/vault-db
	-rm -f data/example.txt.c4gh data/example.txt

#############################
## Distribution
#############################

SQL_FILES=$(notdir $(wildcard ../../src/distribution/src/db/*.sql))

echo:
	@echo $(SQL_FILES)

load: $(SQL_FILES:%=load-%)

load-%: export PGHOST=localhost
load-%: export PGPORT=5432
load-%: export PGUSER=postgres
load-%: export PGPASSWORD=$(file < pg_vault_su_password)
load-%: export PGDATABASE=ega
load-%:
	psql < ../../src/distribution/src/db/$*



#############################
## Upload example
#############################

data/example.txt.c4gh: data/example.txt
	crypt4gh encrypt --recipient_pk service.key.pub < $< > $@

data/example.txt:
	dd if=/dev/urandom bs=1024 count=2 > $@

example: data/example.txt.c4gh

sftp:
	sftp -P 2222 john@localhost

#########################################################
############## LocalEGA Bootstrap Makefile ##############
#########################################################
#
#
# * Docker-compose .env
# * Users credentials ( ssh-keys, passphrases, .json)
# * Stores configurations in {cega,lega}.conf
# * {cega,lega}.yml
# * {ingest,verify,finalize}.ini
# * cega_mq_defs.json
# * cega_mq_rabbitmq.config
# * The certificates
# * the secrets
#
#
#########################################################



SHELL := /bin/bash
OPENSSL=openssl
HOSTNAME_DOMAIN=
#HOSTNAME_DOMAIN=.localega

ARGS=
ifdef DOCKER_SECRETS
ARGS+=--secrets ../private/secrets
endif

ifdef S3
ARGS+=--archive_s3
endif


.PHONY: clean users certs secrets
.DELETE_ON_ERROR: ../private/*
#.INTERMEDIATE: c4gh_keygen.sh

all: ../.env certs users

dev: export DEPLOY_DEV=yesplease
dev: all

SECRETS:= master.key.passphrase \
	  db.lega.in db.lega.out \
	  mq
ifdef S3
SECRETS+= s3.access s3.secret
endif

############### Generate global settings

../private/cega.conf: run/cega/conf.py
	@mkdir -p $(@D)
	@echo "Creating $(@F)"
	@python -m run.cega.conf > $@

../private/lega.conf: run/lega/conf.py $(SECRETS:%=../private/secrets/%)
	@mkdir -p $(@D)
	@echo "Creating $(@F)"
ifdef S3
	@python -m run.lega.conf --secrets $(CURDIR)/../private/secrets --archive_s3 > $@
else
	@python -m run.lega.conf --secrets $(CURDIR)/../private/secrets > $@
endif

../.env: ../private/lega.yml ../private/cega.yml
	@echo "COMPOSE_PROJECT_NAME=lega" > $@
	@echo "COMPOSE_FILE=private/lega.yml:private/cega.yml" >> $@
	@echo "COMPOSE_PATH_SEPARATOR=:" >> $@

secrets: $(SECRETS:%=../private/secrets/%)

############### Generate CentralEGA services

../private/cega-mq-defs.json: ../private/cega.conf run/cega/mq_defs.py
	@mkdir -p $(@D)
	@echo "Creating $(@F)"
	@python -m run.cega.mq_defs < $< > $@

../private/cega-mq-rabbitmq.config: run/cega/mq-rabbitmq.config
	@echo "Creating $(@F)"
	@cp $< $@

../private/cega.yml: run/cega/services.py
../private/cega.yml: ../private/cega-mq-defs.json ../private/cega-mq-rabbitmq.config ../private/cega-entrypoint.sh
	@mkdir -p $(@D)
	@echo "Creating $(@F)"
	@python -m run.cega.services > $@

############### Generate CentralEGA users

USERS=john jane dummy

include users.mk

users: prepare-users \
       $(USERS:%=../private/users/%.passphrase) \
       $(USERS:%=../private/users/%.sshkey) \
       $(USERS:%=../private/users/%.json)

############### Generate LocalEGA settings

../private/lega.yml: run/lega/services.py ../private/entrypoint.sh $(SECRETS:%=../private/secrets/%)
../private/lega.yml: ../private/ingest.ini ../private/verify.ini ../private/finalize.ini ../private/master.key.sec
../private/lega.yml: ../private/cega.conf ../private/lega.conf
	@mkdir -p $(@D)
	@echo "Creating $(@F)"
	@python -m run.lega.services $(ARGS) ../private/cega.conf ../private/lega.conf 2>../private/.err > $@

../private/%.ini: ../private/lega.conf run/lega/%.py
	@mkdir -p $(@D)
	@echo "Creating $(@F)"
	@python -m run.lega.$(@:../private/%.ini=%) $(ARGS) $< 2>../private/.err > $@

# ../private/master.key.sec: c4gh_keygen.sh
# 	@echo "Creating $(@F)"
# 	@expect -f $< &>/dev/null
# 	@chmod 440 $@
# # Making the key readable, because when it's injected inside the container
# # it retains the permissions. Therefore, originally 400, will make it unreadable to the lega user.

# c4gh_keygen.sh: ../private/secrets/master.key.passphrase
# 	@echo "Creating $(@F) (intermediate)"
# 	@mkdir -p $(<D)
# 	@echo "set timeout -1" > $@
# 	@echo "spawn crypt4gh-keygen -f --pk ../private/master.key.pub --sk ../private/master.key.sec" >> $@
# 	@echo 'expect "Passphrase for *"' >> $@
# 	@echo 'send -- "$(file < $<)\r"' >> $@
# 	@echo "expect eof" >> $@

../private/master.key.sec: ../private/secrets/master.key.passphrase
	@echo "Creating $(@F)"
	@ssh-keygen -t ed25519 -f $@ -N "$(file < $<)" -C "Master.Key@LocalEGA" &>/dev/null	
	@mv $@.pub $(@:%.sec=%.pub)
	@chmod 440 $@

# Stronger passphrase
../private/secrets/master.key.passphrase:
	@mkdir -p $(@D)
	@echo "Creating $(@F) (stronger)"
	@python -m run.pwd_gen 32 > $@

ifdef S3
../private/secrets/s3.access ../private/secrets/s3.secret:
	@mkdir -p $(@D)
	@echo "Creating $(@F) (stronger)"
	@python -m run.pwd_gen 32 > $@
endif

../private/secrets/%:
	@mkdir -p $(@D)
	@echo "Creating $(@F)"
	@python -m run.pwd_gen 16 > $@

############### Generate Certificates

include certs.mk

certs: prepare-certs
	@yes | make --no-print-directory all-certs 2>../private/.err
	@yes | make --no-print-directory cega-certs 2>../private/.err
	@yes | make --no-print-directory testsuite-certs 2>../private/.err

############### Clean up
clean:
	rm -rf ../private/*.{conf,yml,ini,sec,pub,config,json,sh,py} ../private/secrets
	rm -f ../.env

clean-all:
	rm -rf ../private ../.env

############### Extras

# This script is used to go around a feature (bug?) of docker.
# When the /etc/ega/ssl.key is injected,
# it is owned by the host user that injected it.
# On Travis, it's the travis (2000) user.
# It needs to be 600 or less, meaning no group nor world access.
#
# In other words, the lega user cannot read that file.
#
# So we use the following trick.
# We make:
#     * /etc/ega/ssl.key world-readable.
#     * /etc/ega owned by the lega group (so we can write a file in it)
# and then, we copy /etc/ega/ssl.key to /etc/ega/ssl.key.lega
# But this time, owned by lega, and with 400 permissions
#
# This should not be necessary for the deployment
# as they are capable of injecting a file with given owner and permissions.
#
../private/entrypoint.sh: entrypoint.sh
../private/cega-entrypoint.sh: cega-entrypoint.sh
../private/cega-entrypoint.sh ../private/entrypoint.sh:
	@echo "Creating $(@F)"
	@cp $< $@
	@chmod +x $@

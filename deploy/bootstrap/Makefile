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


.PHONY: all users certs clean clean-all
.DELETE_ON_ERROR: ../private/*

SECRETS:= master.key.passphrase \
	  db.lega.in db.lega.out \
	  mq
ifdef S3
SECRETS+= s3.access s3.secret
endif

ALL_FILES=$(addprefix ../private/, lega-entrypoint.sh cega-entrypoint.sh \
		                   cega-mq-defs.json cega-mq-rabbitmq.config \
                                   ingest.ini verify.ini finalize.ini master.key.sec \
	                           lega.yml cega.yml)

all: ../.env $(ALL_FILES) certs users

dev: export DEPLOY_DEV=yesplease
dev: all

../private:
	@rm -rf $@
	@mkdir -p $@

../private/secrets:
	@mkdir -p $@

############### Generate global settings

../private/cega.conf: run/cega/conf.py | ../private
	@echo "Creating CentralEGA configuration trace: $(@F)"
	@python -m run.cega.conf > $@

../private/lega.conf: run/lega/conf.py $(addprefix ../private/secrets/,$(SECRETS))
	@echo "Creating LocalEGA configuration trace: $(@F)"
ifdef S3
	@python -m run.lega.conf --secrets $(CURDIR)/../private/secrets --archive_s3 > $@
else
	@python -m run.lega.conf --secrets $(CURDIR)/../private/secrets > $@
endif

../.env: | ../private
	@echo "COMPOSE_PROJECT_NAME=lega" > $@
	@echo "COMPOSE_FILE=private/lega.yml:private/cega.yml" >> $@
	@echo "COMPOSE_PATH_SEPARATOR=:" >> $@

############### Generate CentralEGA services

../private/cega-mq-defs.json: ../private/cega.conf run/cega/mq_defs.py | ../private
	@echo "Creating CentralEGA MQ defs: $(@F)"
	@python -m run.cega.mq_defs < $< > $@

../private/cega-mq-rabbitmq.config: run/cega/mq-rabbitmq.config | ../private
	@echo "Creating CentralEGA MQ conf: $(@F)"
	@cp $< $@

../private/cega.yml: run/cega/services.py | ../private
	@echo "Creating CentralEGA docker-compose file: $(@F)"
	@python -m run.cega.services > $@

############### Generate LocalEGA settings

../private/lega.yml: run/lega/services.py | ../private
../private/lega.yml: ../private/cega.conf ../private/lega.conf
	@echo "Creating LocalEGA docker-compose file: $(@F)"
	@python -m run.lega.services $(ARGS) ../private/cega.conf ../private/lega.conf 2>../private/.err > $@

../private/%.ini: ../private/lega.conf run/lega/%.py | ../private
	@echo "Creating LocalEGA service configuration: $(@F)"
	@python -m run.lega.$* $(ARGS) $< 2>../private/.err > $@

../private/master.key.sec: ../private/secrets/master.key.passphrase
	@echo "Creating master key: $(@F)"
	@ssh-keygen -t ed25519 -f $@ -N "$(shell cat $<)" -C "Master.Key@LocalEGA" &>/dev/null
	@mv $@.pub $(@:%.sec=%.pub)
	@chmod 440 $@

# Stronger passphrase
../private/secrets/master.key.passphrase: | ../private/secrets
	@echo "Creating master key passphrase: $(@F)"
	@python -m run.pwd_gen 32 > $@

ifdef S3
../private/secrets/s3.access ../private/secrets/s3.secret: | ../private/secrets
	@echo "Creating S3 credentials: $(@F)"
	@python -m run.pwd_gen 32 > $@
endif

../private/secrets/%: | ../private/secrets
	@echo "Creating secret: $(@F)"
	@python -m run.pwd_gen 16 > $@

############### Generate CentralEGA users

USERS=john jane dummy

include users.mk

users: $(USERS:%=../private/users/%.passphrase) \
       $(USERS:%=../private/users/%.sshkey) \
       $(USERS:%=../private/users/%.json)

############### Generate Certificates

COMPONENTS=ingest \
           verify \
           finalize \
           db \
           mq \
           keys \
           inbox \
	   outgest \
	   streamer

ifdef S3
COMPONENTS+=archive inbox-s3-backend
endif

COMPONENTS+=cega-mq cega-users testsuite

CERTS=$(COMPONENTS:%=../private/certs/%.sec.pem) \
      $(COMPONENTS:%=../private/certs/%.cert.pem) \
      $(COMPONENTS:%=../private/certs/CA.%.cert.pem)

include certs.mk

certs: $(CERTS)

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
../private/%-entrypoint.sh: %-entrypoint.sh
	@echo "Creating entrypoint replacement: $(@F)"
	@cp $< $@
	@chmod +x $@

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
ifdef SECRETS
ARGS+=--secrets ../private/secrets
endif

ifdef S3
ARGS+=--archive_s3
endif


.PHONY: clean users certs secrets
.DELETE_ON_ERROR: ../private/*
.INTERMEDIATE: c4gh_keygen.sh

all: ../private/cega.yml ../private/lega.yml users ../.env
	@echo "Bootstrapping done"

USERS=john jane dummy

SECRETS=master.key.passphrase \
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
	@python -m run.lega.conf --secrets $(CURDIR)/../private/secrets ${ARGS} > $@

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

# Keep them here to cancel the deletions from the implicit rules
users: ../private/users/serial \
	$(USERS:%=../private/users/%.passphrase) \
	$(USERS:%=../private/users/%.sshkey) \
	$(USERS:%=../private/users/%.json)

../private/users/%.sshkey: ../private/users/%.passphrase
	@echo "Creating $(@F)"
	@ssh-keygen -t ed25519 -f $@ -N "$(file < $<)" -C "$(@:../private/users/%.sshkey=%)@LocalEGA" &>/dev/null
	@chmod 400 $@
# Making the key readable, because when it's injected inside the container
# it retains the permissions. Therefore, originally 400, will make it unreadable to the lega user.

../private/users/%.json: ../private/users/%.sshkey
	@mkdir -p $(@D)
	@echo "Creating $(@F)"
	@python -m run.cega.user $(@:../private/users/%.json=%) $(file < ../private/users/serial) '$(@:.json=.passphrase)' < $(<:=.pub) > $@
	@$(file > ../private/users/serial,$(shell echo "$$(($(file < ../private/users/serial)+1))"))

../private/users/%.passphrase:
	@mkdir -p $(@D)
	@echo "Creating $(@F)"
	@python -m run.pwd_gen 8 > $@

../private/users/serial:
	@mkdir -p $(@D)
	@echo '15000' > $@

############### Generate LocalEGA settings

../private/lega.yml: run/lega/services.py ../private/entrypoint.sh secrets
../private/lega.yml: ../private/ingest.ini ../private/verify.ini ../private/finalize.ini ../private/master.key.sec
../private/lega.yml: PY_RUN=python -m run.lega.services
../private/lega.yml: ../private/cega.conf ../private/lega.conf
	@mkdir -p $(@D)
	@echo "Creating $(@F)"
	@$(PY_RUN) ${ARGS} ../private/cega.conf ../private/lega.conf 2>../private/.err > $@

../private/ingest.ini: run/lega/ingest.py
../private/ingest.ini: PY_RUN=python -m run.lega.ingest
../private/verify.ini: run/lega/verify.py
../private/verify.ini: PY_RUN=python -m run.lega.verify
../private/finalize.ini: run/lega/finalize.py
../private/finalize.ini: PY_RUN=python -m run.lega.finalize
../private/ingest.ini ../private/verify.ini ../private/finalize.ini: ../private/lega.conf
	@mkdir -p $(@D)
	@echo "Creating $(@F)"
	@$(PY_RUN) ${ARGS} $< 2>../private/.err > $@

# ../private/master.key: ../private/secrets/master.key.passphrase
# 	@echo "Creating $(@F)"
# 	@ssh-keygen -t ed25519 -f $@ -N "$(file < $<)" -C "Master.Key@LocalEGA" &>/dev/null

../private/master.key.sec: c4gh_keygen.sh
	@echo "Creating $(@F)"
	@expect -f $< &>/dev/null
	@chmod 440 $@
# Making the key readable, because when it's injected inside the container
# it retains the permissions. Therefore, originally 400, will make it unreadable to the lega user.

c4gh_keygen.sh: ../private/secrets/master.key.passphrase
	@echo "Creating $(@F) (intermediate)"
	@mkdir -p $(<D)
	@echo "set timeout -1" > $@
	@echo "spawn crypt4gh-keygen -f --pk ../private/master.key.pub --sk ../private/master.key.sec" >> $@
	@echo 'expect "Passphrase for *"' >> $@
	@echo 'send -- "$(file < $<)\r"' >> $@
	@echo "expect eof" >> $@

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

certs:
	@echo "Creating certificates"
	@mkdir -p ../private
	make -C certs clean prepare OPENSSL=${OPENSSL} &>../private/.err
	yes | make -C certs OPENSSL=${OPENSSL} DOMAIN="${HOSTNAME_DOMAIN}" &>../private/.err
	yes | make -C certs cega testsuite OPENSSL=${OPENSSL} DOMAIN="${HOSTNAME_DOMAIN}" &>../private/.err

############### Clean up
clean:
	rm -rf ../private
	rm -f ../.env

clean-certs:
	make -C certs clean

clean-all: clean clean-certs

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

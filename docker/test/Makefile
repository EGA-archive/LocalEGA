SHELL := /bin/bash

.PHONY: upload submit user check

HERE:=$(dir $(realpath $(lastword $(MAKEFILE_LIST))))
MAIN_REPO:=$(realpath $(HERE)/../..)

USER=ega-box-999
USER_ID=100
FILE=file.txt
FILESIZE=10 # in MB

get_md5 =                                      \
         if which md5 &> /dev/null; then       \
           md5 $(1) | cut -d' ' -f4 > $(2);    \
         else                                  \
           md5sum $(1) | cut -d' ' -f1 > $(2); \
         fi

##############################

DOCKER_PATH=$(MAIN_REPO)/docker
CEGA_USERS=$(DOCKER_PATH)/private/cega/users

INSTANCE_PORT=$(shell awk -F= '/DOCKER_PORT_inbox/ {print $$2}' $(DOCKER_PATH)/bootstrap/settings.rc)
PGP_PUB=$(DOCKER_PATH)/private/lega/pgp/ega.pub
PGP_EMAIL=$(shell awk -F= '/PGP_EMAIL/ {print $$2}' $(DOCKER_PATH)/bootstrap/settings.rc)
CEGA_MQ_CONNECTION=$(subst cega-mq,localhost,$(shell awk -F= '/^CEGA_CONNECTION/ {print $$2}' $(DOCKER_PATH)/private/lega/mq.env))


SSH_KEY=$(CEGA_USERS)/$(USER).sshkey
SSH_PASS="" # no passphrase
##############################

all: user upload submit

$(FILE):
	dd if=/dev/zero of=$@ count=$(FILESIZE) bs=1048576

$(FILE).c4ga: $(FILE)
	lega-cryptor encrypt --pk $(PGP_PUB) -i $< -o $@

upload: $(FILE).c4ga $(SSH_KEY) user
	sftp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -P $(INSTANCE_PORT) -i $(SSH_KEY) $(USER)@localhost <<< $$"put $<"

$(FILE).md5: $(FILE)
	$(call get_md5,$<,$@)

$(FILE).c4ga.md5: $(FILE).c4ga
	$(call get_md5,$<,$@)

submit: $(FILE).c4ga $(FILE).c4ga.md5 $(FILE).md5
	python $(MAIN_REPO)/extras/publish.py --connection $(CEGA_MQ_CONNECTION) $(USER) $(FILE).c4ga --enc $(shell cat $(FILE).c4ga.md5) --stableID EGAF$(shell cat $(FILE).md5)

user: $(CEGA_USERS)/lega/$(USER).yml

$(CEGA_USERS)/lega/$(USER).yml: $(CEGA_USERS)/$(USER).yml
	-cd $(CEGA_USERS)/lega && ln -s ../$(USER).yml .
	-cd $(CEGA_USERS)/lega_ids && ln -s ../$(USER).yml $(USER_ID).yml

$(CEGA_USERS)/$(USER).yml: $(SSH_KEY)
	@echo --- > $@
	@echo "username: $(USER)" >> $@
	@echo "pubkey: $(shell cat $<.pub)" >> $@
	@echo "uid: $(USER_ID)" >> $@
	@echo "gecos: EGA User - $(USER)" >> $@

$(SSH_KEY):
	ssh-keygen -t rsa -b 2048 -f $@ -N $(SSH_PASS) -C "$(USER)@LocalEGA"
	chmod 400 $@

# We only read the first message from the completed queue
# If it contains COMPLETED, and it is the right user/filepath/stableID, 
# then we say it's ok
# That'll do it for the moment
check: CEGA_MQ_USER=$(shell awk -F= '/CEGA_MQ_USER/ {print $$2}' $(DOCKER_PATH)/private/lega/.trace)
check: CEGA_MQ_PASSWORD=$(shell awk -F= '/CEGA_MQ_PASSWORD/ {print $$2}' $(DOCKER_PATH)/private/lega/.trace)
check: MESSAGE=$(shell ./rabbitmqadmin -H localhost -P 15670 -V lega -u lega -p $(CEGA_MQ_PASSWORD) get queue=completed count=1 requeue=true)
check: $(FILE).c4ga
	@echo "$(MESSAGE)" | grep 'state: COMPLETED' &>/dev/null
	@echo "$(MESSAGE)" | grep 'user: $(USER)' &>/dev/null
	@echo "$(MESSAGE)" | grep 'filepath: $(<F)' &>/dev/null
	@echo "$(MESSAGE)" | grep 'details: EGAF$(shell cat $(FILE).md5)' &>/dev/null
	@echo "Message found in the CentralEGA broker"

clean:
	-unlink $(CEGA_USERS)/lega/$(USER).yml
	-unlink $(CEGA_USERS)/lega_ids/$(USER_ID).yml
	rm -rf $(FILE){,.c4ga,.c4ga.md5,.md5}
	rm -rf $(CEGA_USERS)/$(USER).yml $(SSH_KEY) $(SSH_KEY).pub

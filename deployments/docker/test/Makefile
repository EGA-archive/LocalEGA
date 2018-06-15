.PHONY: upload submit user

MAIN_REPO=~/_ega
SSH_KEY_PUB=~/.ssh/lega.pub
SSH_KEY_PRIV=~/.ssh/lega

USER=ega-box-999
FILE=HG00458.unmapped.ILLUMINA.bwa.CHS.low_coverage.20130415.bam

##############################

DOCKER_PATH=$(MAIN_REPO)/deployments/docker
INSTANCE_PORT=$(shell awk -F= '/DOCKER_PORT_inbox/ {print $$2}' $(DOCKER_PATH)/bootstrap/settings.rc)
PGP_PUB=$(DOCKER_PATH)/private/lega/pgp/ega.pub
PGP_EMAIL=$(shell awk -F= '/PGP_EMAIL/ {print $$2}' $(DOCKER_PATH)/bootstrap/settings.rc)
CEGA_USERS=$(DOCKER_PATH)/private/cega/users
CEGA_MQ_CONNECTION=$(shell awk -F= '/^CEGA_CONNECTION/ {print $$2}' $(DOCKER_PATH)/private/lega/mq.env)

##############################

all: user upload submit

# $(FILE):
# 	@echo 'Hello' > $(FILE)

$(FILE).c4ga: $(FILE)
	lega-cryptor encrypt --pk $(PGP_PUB) -i $< -o $@

#	lega-cryptor encrypt -r Sweden -i $< -o $@

upload: $(FILE).c4ga
	cd $(<D) && sftp -P $(INSTANCE_PORT) -i $(SSH_KEY_PRIV) $(USER)@localhost <<< $$"put $(<F)"

$(FILE).c4ga.md5: $(FILE).c4ga
	printf '%s' $(shell md5 $< | cut -d' ' -f4) > $@

$(FILE).md5: $(FILE)
	printf '%s' $(shell md5 $< | cut -d' ' -f4) > $@

submit: $(FILE).c4ga $(FILE).c4ga.md5 $(FILE).md5
	@echo publish.py --connection amqp://[redacted]@$(lastword $(subst @, ,$(CEGA_MQ_CONNECTION))) $(USER) dir/$(FILE).c4ga --enc ...
	@python ~/_ega/extras/publish.py --connection $(subst cega-mq,localhost,$(CEGA_MQ_CONNECTION)) $(USER) $(FILE).c4ga --enc $(shell cat $(FILE).c4ga.md5) EGAF$(shell cat $(FILE).md5)

user: $(CEGA_USERS)/lega/$(USER).yml

$(CEGA_USERS)/lega/$(USER).yml: $(CEGA_USERS)/$(USER).yml
	-cd $(CEGA_USERS)/lega && ln -s ../$(USER).yml .
$(CEGA_USERS)/$(USER).yml:
	@echo --- > $@
	@echo "pubkey: $(shell cat $(SSH_KEY_PUB))" >> $@

clean:
	-unlink $(CEGA_USERS)/lega/$(USER).yml
	rm -rf $(FILE).c4ga $(FILE).c4ga.md5 $(FILE).md5 $(CEGA_USERS)/$(USER).yml

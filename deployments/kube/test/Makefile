.PHONY: upload submit user

# folder for the localegarepo
MAIN_REPO=~/csc/dev/LocalEGA
# the RSA keys need to be in ~/.ssh path
SSH_KEY_PUB=~/.ssh/dummy.key.pub
SSH_KEY_PRIV=~/.ssh/dummy.key

USER=ega-box-999
FILE=HG00458.unmapped.ILLUMINA.bwa.CHS.low_coverage.20130415.bam

##############################

DOCKER_PATH=$(MAIN_REPO)/deployments/kube
PGP_PUB=$(DOCKER_PATH)/auto/config/key.1.pub
# should be changed with remote ip, this is the default ip for kubernetes
DEPLOY_IP=192.168.99.100
PGP_EMAIL=local-ega@ega.eu
CEGA_PORT=$(shell kubectl describe svc cega-mq | grep "NodePort:" | awk '$$2=="amqp" {print substr($$3,1,5)}')
INBOX_PORT=$(shell kubectl describe svc inbox --namespace=testing | grep "NodePort:" | awk '{print substr($$3,1,5)}')
#needs the same password that the Lega-MQ conencted to CEGA-MQ
CEGA_PASWORD=lega
CEGA_MQ_CONNECTION=amqp://lega:$(CEGA_PASWORD)@$(DEPLOY_IP):$(CEGA_PORT)/lega

##############################

all: user upload submit

user: $(DOCKER_PATH)/yml/cega-users/$(USER).yml

$(DOCKER_PATH)/yml/cega-users/$(USER).yml:
	@echo --- > $@
	@echo "pubkey: $(shell cat $(SSH_KEY_PUB))" >> $@

# $(FILE):
# 	@echo 'Hello' > $(FILE)

$(FILE).c4ga: $(FILE)
	lega-cryptor encrypt --pk $(PGP_PUB) -i $< -o $@

#	lega-cryptor encrypt -r Sweden -i $< -o $@

upload: $(FILE).c4ga
	cd $(<D) && sftp -P $(INBOX_PORT) -i $(SSH_KEY_PRIV) $(USER)@$(DEPLOY_IP) <<< $$"put $(<F)"

$(FILE).c4ga.md5: $(FILE).c4ga
	printf '%s' $(shell md5 $< | cut -d' ' -f4) > $@

$(FILE).md5: $(FILE)
	printf '%s' $(shell md5 $< | cut -d' ' -f4) > $@

submit: $(FILE).c4ga $(FILE).c4ga.md5 $(FILE).md5
	@echo publish.py --connection amqp://[redacted]@$(lastword $(subst @, ,$(CEGA_MQ_CONNECTION))) $(USER) dir/$(FILE).c4ga --enc ...
	@python $(MAIN_REPO)/extras/publish.py --connection $(subst cega-mq,localhost,$(CEGA_MQ_CONNECTION)) $(USER) $(FILE).c4ga --enc $(shell cat $(FILE).c4ga.md5) EGAF$(shell cat $(FILE).md5)

clean:
	rm -rf $(FILE).c4ga $(FILE).c4ga.md5 $(FILE).md5

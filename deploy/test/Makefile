SHELL := /bin/bash

.PHONY: upload submit stable_id

HERE:=$(dir $(realpath $(lastword $(MAKEFILE_LIST))))
MAIN_REPO:=$(realpath $(HERE)/../..)

USER=dummy
FILE=testfile.txt
FILESIZE=10 # in MB

##############################

DOCKER_PATH=$(MAIN_REPO)/deploy

INSTANCE_PORT=$(shell awk -F= '/DOCKER_PORT_inbox/ {print $$2}' $(DOCKER_PATH)/bootstrap/settings.rc)
PUB_KEY=$(DOCKER_PATH)/private/ega.key.pub
CEGA_MQ_CONNECTION=$(shell cat $(DOCKER_PATH)/private/secrets/cega_connection)

SSH_KEY=$(MAIN_REPO)/tmp/dummy.sec

##############################

all: upload submit

$(FILE):
	dd if=/dev/zero of=$@ count=$(FILESIZE) bs=1048576
#	for i in {0..100000}; do echo $$i >> $@; done
#	dd if=/dev/urandom of=$@ count=$(FILESIZE) bs=1048576

$(FILE).c4gh: $(FILE) signing.key
	crypt4gh encrypt --pk $(PUB_KEY) --signing_key signing.key < $< > $@

upload: $(FILE).c4gh
	sftp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -P $(INSTANCE_PORT) -i $(SSH_KEY) $(USER)@localhost <<< $$"put $<"

####################################################################
## Signing key
####################################################################
signing.key:
	crypt4gh generate -o $@ --signing

####################################################################
## User's pub/sec keys
####################################################################
user.key:
	crypt4gh generate -o $@

####################################################################
## Publish messages
####################################################################

submit: $(FILE).c4gh
	python $(MAIN_REPO)/extras/cega_publish.py \
	--connection $(CEGA_MQ_CONNECTION) \
	'files' \
	"{ \"user\": \"$(USER)\", \"file_path\": \"/$(FILE).c4gh\"}"


# stable_id: STABLE_ID=$(shell uuidgen)
# stable_id:
# 	@read -p "File ID:" FILE_ID && \
# 	python $(MAIN_REPO)/extras/cega_publish.py \
# 	--connection $(CEGA_MQ_CONNECTION) \
# 	'stableIDs' \
# 	"{\"file_id\": \"$${FILE_ID}\", \"stable_id\": \"EGAF$(STABLE_ID)\"}" && \
# 	echo "Mapping file reference $${FILE_ID} to EGAF$(STABLE_ID)"

stable_id:
	python $(MAIN_REPO)/extras/publish_stable_id.py \
	--connection $(CEGA_MQ_CONNECTION) \
	'v1.files.completed' 'stableIDs' 'EGAF00001398602'

clean-mq:
	@python $(MAIN_REPO)/extras/clean_mq.py --connection $(CEGA_MQ_CONNECTION)


output.c4gh: user.key
	python outgest.py $@ $<.pub

output.txt: output.c4gh user.key
	crypt4gh decrypt --sk user.key < $< > $@

check: output.txt $(FILE)
	diff $^

####################################################################
## Cleaning
####################################################################
clean:
	rm -rf $(FILE){,.c4gh}
	rm -rf output.{txt,c4gh}
	rm -f signing.key{,.pub}
	rm -f user.key{,.pub}

cleanall: clean

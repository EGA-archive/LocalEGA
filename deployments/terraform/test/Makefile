
TERRAFORM_PATH=$(dir $(abspath $(lastword $(MAKEFILE_LIST))))..
SSH_KEY_PUB=~/.ssh/lega.pub
SSH_KEY_PRIV=~/.ssh/lega

CEGA_IP=$(shell cd ${TERRAFORM_PATH}/cega && terraform output address)
INBOX_IP=$(shell cd ${TERRAFORM_PATH} && terraform output -module=inbox address)

BULLET=$'\033[43m\033[30m          \xE2\x81\x8D
NOCOLOR=$'          \033[0m

##############################

PGP_PUB=$(TERRAFORM_PATH)/private/pgp/ega.pub
PGP_EMAIL=$(shell awk -F= '/PGP_EMAIL/ {print $$2}' $(TERRAFORM_PATH)/bootstrap/settings)

PREFIX_PATH=/
ifdef $(findstring 'hellgate',$(CEGA_CONNECTION))
PREFIX_PATH=/rabbitmq
endif

##############################
USER=ega-box-999
#FILE=HG00458.unmapped.ILLUMINA.bwa.CHS.low_coverage.20130415.bam
FILE=testfile

.PHONY: upload submit user rabbitmqadmin check vault

all: user upload submit rabbitmqadmin

echo:
	@echo TERRAFORM_PATH=$(TERRAFORM_PATH)
	@echo CEGA_IP=$(CEGA_IP)
	@echo INBOX_IP=$(INBOX_IP)

$(FILE).gpg: $(FILE)
	@echo "${BULLET} Encrypt $< into $@ ${NOCOLOR}"
	python ~/_ega/extras/encrypt.py $(PGP_PUB) $< > $@

$(FILE).gpg.md5: $(FILE).gpg
	@echo "${BULLET} Compute checksum of the encrypted file ${NOCOLOR} [algorithm: md5]"
	printf '%s' $(shell md5 $< | cut -d' ' -f4) > $@

$(FILE).md5: $(FILE)
	@echo "${BULLET} Compute checksum of the original file ${NOCOLOR} [algorithm: md5]"
	printf '%s' $(shell md5 $< | cut -d' ' -f4) > $@

upload: $(FILE).gpg $(FILE).gpg.md5 $(FILE).md5
	@echo "${BULLET} Upload files to the Swedish Local EGA inbox ${NOCOLOR}"
	cd $(<D) && sftp -i $(SSH_KEY_PRIV) -P 9000 $(USER)@${INBOX_IP} <<< $$'$(^F:%=put %\n)'

submit: $(FILE).gpg $(FILE).md5 $(FILE).gpg.md5
	@echo "${BULLET} Publish message to Central EGA for ingestion ${NOCOLOR}"
	python ~/_ega/extras/publish.py --connection $(subst cega_mq,$(CEGA_IP),$(CEGA_CONNECTION)) $(USER) $(FILE).gpg --unenc $(shell cat $(FILE).md5) --enc $(shell cat $(FILE).gpg.md5) EGAF$(shell cat $(FILE).md5)

user: $(USER).yml
	@echo "${BULLET} Add '$(USER)' to Central EGA ${NOCOLOR}"
	scp $< centos@${CEGA_IP}:$< &>/dev/null
	@echo "${BULLET} Grant '$(USER)' access to the Swedish Local EGA ${NOCOLOR}"
	ssh -l centos ${CEGA_IP} "[[ -L /var/lib/cega/users/swe1/$< ]] || sudo ln -s ~/$< /var/lib/cega/users/swe1/$<" &>/dev/null

$(USER).yml:
	@echo "${BULLET} Create user '${USER}' ${NOCOLOR}"
	@echo --- > $@
	@echo "pubkey: $(shell cat $(SSH_KEY_PUB))" >> $@

clean:
	rm -rf $(FILE).gpg $(FILE).md5 $(FILE).gpg.md5 $(USER).yml

check:
	@echo "${BULLET} Check the message broker in Central EGA ${NOCOLOR}"
	@echo "            Listing queues, vhost, name, node, messages on the Message Broker"
	@rabbitmqadmin -U $(subst cega_mq,$(CEGA_IP),$(CEGA_CONNECTION)) --prefix-path $(PREFIX_PATH) list queues vhost name node messages

vault:
	@echo "${BULLET} Check the vault ${NOCOLOR}"
	@echo "            Running 'ls -alR /ega/vault' in the vault"
	@ssh ${INBOX_IP} -At "ssh -o LogLevel=quiet  -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null ega_vault 'ls -alR /ega/vault'"

tell:
	@echo
	@echo   "\t---------------------------------------------------------------------------"
	@printf "\t|  \033[43m\033[30m 1 \033[0m %-65s  |\n" "Create a user named '$(USER)'"
	@printf "\t|  \033[43m\033[30m 2 \033[0m %-65s  |\n" "Add '$(USER)' to Central EGA [IP: ${CEGA_IP}]"
	@printf "\t|  \033[43m\033[30m 3 \033[0m %-65s  |\n" "Grant '$(USER)' access to the Swedish Local EGA"
	@echo   "\t---------------------------------------------------------------------------"
	@printf "\t|  \033[43m\033[30m 4 \033[0m %-65s  |\n" "Encrypt '$(FILE)' into '$(FILE).gpg'"
	@printf "\t|  \033[43m\033[30m 5 \033[0m %-65s  |\n" "Upload '$(FILE).gpg' to the Swedish Local EGA inbox [IP: ${INBOX_IP}]"
	@printf "\t|  \033[43m\033[30m 6 \033[0m %-65s  |\n" "Publish a message to Central EGA for ingestion of '$(FILE).gpg'"
	@printf "\t|  \033[43m\033[30m 7 \033[0m %-65s  |\n" "Check the result in Central EGA's message broker"
	@printf "\t|  \033[43m\033[30m 8 \033[0m %-65s  |\n" "Check the vault"
	@echo   "\t---------------------------------------------------------------------------"
	@echo

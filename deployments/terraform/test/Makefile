.PHONY: upload submit user rabbitmqadmin check vault

TERRAFORM_PATH=$(dir $(abspath $(lastword $(MAKEFILE_LIST))))..
GPG_EXEC=gpg
SSH_KEY_PUB=~/.ssh/lega.pub
SSH_KEY_PRIV=~/.ssh/lega

CEGA_IP=$(shell cd ${TERRAFORM_PATH}/cega && terraform output address)
INBOX_IP=$(shell cd ${TERRAFORM_PATH} && terraform output -module=inbox address)

BULLET=$'\033[43m\033[30m          \xE2\x81\x8D
NOCOLOR=$'          \033[0m

##############################

GPG_HOME=$(TERRAFORM_PATH)/private/gpg
GPG_EMAIL=$(shell awk -F= '/GPG_EMAIL/ {print $$2}' $(TERRAFORM_PATH)/bootstrap/settings)

PREFIX_PATH=/
ifdef $(findstring 'hellgate',$(CEGA_CONNECTION))
PREFIX_PATH=/rabbitmq
endif

##############################

all: user upload submit rabbitmqadmin

echo:
	@echo TERRAFORM_PATH=$(TERRAFORM_PATH)
	@echo CEGA_IP=$(CEGA_IP)
	@echo INBOX_IP=$(INBOX_IP)
	@echo CEGA_MQ_PASSWORD=$(CEGA_MQ_PASSWORD)
	@echo CEGA_MQ_CONNECTION=$(CEGA_MQ_CONNECTION)


org:
	@echo "${BULLET} Create a file named 'org' ${NOCOLOR}"
	@echo "Hello, Niclas!" > $@

enc: org
	@echo "${BULLET} Encrypt 'org' into 'enc' ${NOCOLOR}"
	$(GPG_EXEC) --homedir $(GPG_HOME) -r $(GPG_EMAIL) -e -o $@ $< 2>/dev/null

upload: user enc
	@echo "${BULLET} Upload 'enc' to the Swedish Local EGA inbox ${NOCOLOR}"
	sftp -i $(SSH_KEY_PRIV) toto@${INBOX_IP} <<< $$'put enc' &>/dev/null

enc.md5: enc
	@echo "${BULLET} Compute checksum for 'enc' ${NOCOLOR} [algorithm: md5]"
	md5 $< | cut -d' ' -f4 > $@

org.md5: org
	@echo "${BULLET} Compute checksum for 'org' ${NOCOLOR} [algorithm: md5]"
	md5 $< | cut -d' ' -f4 > $@

submit: enc enc.md5 org.md5
	@echo "${BULLET} Publish message to Central EGA for ingestion ${NOCOLOR}"
	python ~/_ega/extras/publish.py --connection $(subst cega-mq,localhost,$(CEGA_CONNECTION)) toto enc --unenc $(shell cat org.md5) --enc $(shell cat enc.md5)

user: toto.yml
	@echo "${BULLET} Add 'toto' to Central EGA ${NOCOLOR}"
	scp $< centos@${CEGA_IP}:$< &>/dev/null
	@echo "${BULLET} Grant 'toto' access to the Swedish Local EGA ${NOCOLOR}"
	ssh -l centos ${CEGA_IP} "[[ -L /var/lib/cega/users/swe1/$< ]] || sudo ln -s ~/$< /var/lib/cega/users/swe1/$<" &>/dev/null

toto.yml:
	@echo "${BULLET} Create user 'toto' ${NOCOLOR}"
	@echo --- > $@
	@echo "pubkey: $(shell cat $(SSH_KEY_PUB))" >> $@

clean:
	rm -rf org enc enc.md5 org.md5 toto.yml


check:
	@echo "${BULLET} Check the message broker in Central EGA ${NOCOLOR}"
	@echo "            Listing queues, vhost, name, node, messages on the Message Broker"
	@rabbitmqadmin -U $(subst cega-mq,localhost,$(CEGA_CONNECTION)) --prefix-path $(PREFIX_PATH) list queues vhost name node messages

vault:
	@echo "${BULLET} Check the vault ${NOCOLOR}"
	@echo "            Running 'ls -alR /ega/vault' in the vault"
	@ssh ${INBOX_IP} -At "ssh -o LogLevel=quiet  -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null ega_vault 'ls -alR /ega/vault'"

tell:
	@echo
	@echo   "\t---------------------------------------------------------------------------"
	@printf "\t|  \033[43m\033[30m 1 \033[0m %-65s  |\n" "Create a user named 'toto'"
	@printf "\t|  \033[43m\033[30m 2 \033[0m %-65s  |\n" "Add 'toto' to Central EGA [IP: ${CEGA_IP}]"
	@printf "\t|  \033[43m\033[30m 3 \033[0m %-65s  |\n" "Grant 'toto' access to the Swedish Local EGA"
	@echo   "\t---------------------------------------------------------------------------"
	@printf "\t|  \033[43m\033[30m 4 \033[0m %-65s  |\n" "Create a file 'org' with 'Hello, Niclas!' as content"
	@printf "\t|  \033[43m\033[30m 5 \033[0m %-65s  |\n" "Encrypt 'org' into 'enc'"
	@printf "\t|  \033[43m\033[30m 6 \033[0m %-65s  |\n" "Upload 'enc' to the Swedish Local EGA inbox [IP: ${INBOX_IP}]"
	@printf "\t|  \033[43m\033[30m 7 \033[0m %-65s  |\n" "Publish a message to Central EGA for ingestion of 'enc'"
	@printf "\t|  \033[43m\033[30m 8 \033[0m %-65s  |\n" "Check the result in Central EGA's message broker"
	@printf "\t|  \033[43m\033[30m 9 \033[0m %-65s  |\n" "Check the vault"
	@echo   "\t---------------------------------------------------------------------------"
	@echo

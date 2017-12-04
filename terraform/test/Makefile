.PHONY: upload submit user

TERRAFORM_PATH=~/_ega/terraform
GPG_EXEC=gpg
SSH_KEY_PUB=~/.ssh/lega.pub
SSH_KEY_PRIV=~/.ssh/lega

CEGA_IP=$(shell cd ${TERRAFORM_PATH}/cega && terraform output address)
INBOX_IP=$(shell cd ${TERRAFORM_PATH} && terraform output -module=inbox address)

##############################

GPG_HOME=$(TERRAFORM_PATH)/private/gpg
GPG_EMAIL=$(shell awk -F= '/GPG_EMAIL/ {print $$2}' $(TERRAFORM_PATH)/bootstrap/settings.rc)
CEGA_MQ_PASSWORD=$(shell awk -F' ' '/CEGA_swe1_MQ_PASSWORD/ {print $$3}' $(TERRAFORM_PATH)/cega/private/.trace)
CEGA_MQ_CONNECTION=amqp://cega_swe1:$(strip $(CEGA_MQ_PASSWORD))@localhost:5672/swe1

##############################

all: user upload submit

export ORG_FILE
org:
	@echo "Hello, Niclas!" > $@

enc: org
	$(GPG_EXEC) --homedir $(GPG_HOME) -r $(GPG_EMAIL) -e -o $@ $< 2>/dev/null

upload: user enc
	sftp -i $(SSH_KEY_PRIV) toto@${INBOX_IP} <<< $$'put enc' &>/dev/null

enc.md5: enc
	md5 $< | cut -d' ' -f4 > $@

org.md5: org
	md5 $< | cut -d' ' -f4 > $@

submit: enc enc.md5 org.md5
	ssh -l centos ${CEGA_IP} /var/lib/cega/publish --connection $(CEGA_MQ_CONNECTION) swe1 toto enc --unenc $(shell cat org.md5) --enc $(shell cat enc.md5) &>/dev/null

user: toto.yml
	scp $< centos@${CEGA_IP}:$< &>/dev/null
	ssh -l centos ${CEGA_IP} "[[ -L /var/lib/cega/users/swe1/$< ]] || sudo ln -s ~/$< /var/lib/cega/users/swe1/$<" &>/dev/null

toto.yml:
	@echo --- > $@
	@echo "pubkey: $(shell cat $(SSH_KEY_PUB))" >> $@

clean:
	rm -rf org enc enc.md5 org.md5 toto.yml

rabbitmqadmin:
	ssh -l centos ${CEGA_IP} "curl -sS -OL https://raw.githubusercontent.com/rabbitmq/rabbitmq-management/v3.7.0/bin/$@; chmod +x $@" &>/dev/null

check_mq:
	ssh -l centos ${CEGA_IP} ./rabbitmqadmin -u cega_swe1 -p ${CEGA_MQ_PASSWORD} list queues vhost name node messages

check_vault:
	ssh ${INBOX_IP} -At "ssh -o LogLevel=quiet  -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null ega_vault 'ls -al /ega/vault/000/000/000/000/000/000/'"

tell:
	@echo
	@echo   "\t----------------------------------------------------------------------------"
	@printf "\t|  %-70s  |\n" "1) Create a user named 'toto'"
	@printf "\t|  %-70s  |\n" "2) Add 'toto' to Central EGA [IP: ${CEGA_IP}]"
	@printf "\t|  %-70s  |\n" "3) Grant 'toto' access to the Swedish Local EGA"
	@echo   "\t----------------------------------------------------------------------------"
	@printf "\t|  %-70s  |\n" "4) Create a file 'org' with 'Hello, Niclas!' as content"
	@printf "\t|  %-70s  |\n" "5) Encrypt 'org' into 'enc'"
	@printf "\t|  %-70s  |\n" "6) Upload 'enc' to the Swedish Local EGA inbox [IP: ${INBOX_IP}]"
	@printf "\t|  %-70s  |\n" "7) Publish a message to Central EGA for ingestion of 'enc'"
	@printf "\t|  %-70s  |\n" "8) Check the result in Central EGA's message broker"
	@echo   "\t----------------------------------------------------------------------------"
	@echo

SHELL := /bin/bash


define error-inbox-lega-message
Please specify the group id via the LEGA_GID variable.
For example, by calling "make $@ LEGA_GID=$$(id -g lega)"
endef

image-inbox:
ifeq ($(LEGA_GID),)
	$(error $(error-inbox-lega-message))
endif
	make -C ../../src/inbox latest LEGA_GID=$(LEGA_GID)


image-handler:
	make -C ../../src/handler latest

image-vault:
	make -C ../../src/vault latest
init-vault:
	make -C ../../src/vault init

images: image-inbox image-handler image-vault

confs:
	for f in *.sample; do cp $$f $${f//.sample/}; done

init-vault:

up:
	@docker-compose up -d inbox mq vault-db
	@sleep 3 # wait a bit
	@docker-compose up -d handler

down:
	docker-compose down -v

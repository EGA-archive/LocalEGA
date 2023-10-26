


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


images: image-inbox image-handler image-vault


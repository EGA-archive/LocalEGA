SHELL := /bin/bash
COMMIT ?= $(shell git rev-parse HEAD)
ARGS = 

IMG=fega/handler:$(COMMIT)

.PHONY: latest build

all: latest

ARCH=$(shell uname -m)
ifeq ($(ARCH), arm64) # reset for MacOS
	ARCH=aarch64
endif

build: ARGS+=--target BUILD
latest build: 
ifeq ($(LEGA_UID),)
	$(error "Please specify the user id via the LEGA_UID variable")
endif
ifeq ($(LEGA_GID),)
	$(error "Please specify the group id via the LEGA_GID variable")
endif
	docker build $(ARGS) \
	       --build-arg ARCH=$(ARCH) \
	       --build-arg COMMIT=$(COMMIT) \
               --build-arg BUILD_DATE="$(shell date +%Y-%m-%d_%H.%M.%S)" \
               --build-arg LEGA_UID=$(LEGA_UID) \
               --build-arg LEGA_GID=$(LEGA_GID) \
	       -t $(IMG) .
	docker tag $(IMG) fega/handler:$@

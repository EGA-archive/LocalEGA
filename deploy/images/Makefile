SHELL := /bin/bash

TARGET_PREFIX=egarchive/lega-

LEGA_GID=1000

# Must find better, but working so far
MAIN_REPO := $(abspath $(dir $(abspath $(lastword $(MAKEFILE_LIST))))/../..)

ARGS=
# eg --no-cache

.PHONY: all erase purge base

all: base

base:
	cd $(MAIN_REPO) && \
	docker build -f Dockerfile ${ARGS} \
		   --build-arg LEGA_GID=$(LEGA_GID) \
		   --build-arg BUILD_DATE=$(shell date -u +'%Y-%m-%dT%H:%M:%SZ') \
		   --build-arg SOURCE_COMMIT=$(shell git rev-parse --short HEAD) \
		   --tag $(TARGET_PREFIX)$@:latest \
		   .

define remove_dangling
	docker images $(1) -f "dangling=true" -q | uniq | while read n; do docker rmi -f $$n; done
endef

erase:
	@$(call remove_dangling,$(TARGET_PREFIX)base)

purge:
	@$(call remove_dangling,)


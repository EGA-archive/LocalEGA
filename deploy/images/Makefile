SHELL := /bin/bash

TAG=$(shell git rev-parse --short HEAD)

ifdef TRAVIS_COMMIT
TAG=$(TRAVIS_COMMIT)
endif

IMGTAG=$(TAG)

TARGET_PREFIX=egarchive/lega-

LEGA_GID=1000

# Must find better, but working so far
MAIN_REPO := $(abspath $(dir $(abspath $(lastword $(MAKEFILE_LIST))))/../..)

.PHONY: all erase clean purge base push

all: base

base:
	cd $(MAIN_REPO) && \
	docker build -f Dockerfile.$@ \
	       --build-arg LEGA_GID=$(LEGA_GID) \
	       --cache-from $(TARGET_PREFIX)$@:latest \
               --tag $(TARGET_PREFIX)$@:$(TAG) \
               --tag $(TARGET_PREFIX)$@:latest \
               .

define clean_tag
    docker images $(1) --format "{{.Repository}} {{.Tag}}" | \
    awk '{ if ($$2 != "$(2)" && $$2 != "latest") print $$1":"$$2; }' | uniq | \
    while read n; do docker rmi $$n; done
endef

define remove_dangling
    docker images $(1) -f "dangling=true" -q | uniq | while read n; do docker rmi -f $$n; done
endef

clean:
	@$(call clean_tag,$(TARGET_PREFIX)base, $(TAG))

erase:
	@$(call remove_dangling,$(TARGET_PREFIX)base)

purge:
	@$(call remove_dangling,)


# Download images
pull-%:
	docker pull $(TARGET_PREFIX)$(@:pull-%=%):$(IMGTAG)

# Upload images
push-%:
	-@echo -n "$(DOCKER_PASSWORD)" | docker login -u "$(DOCKER_USER)" --password-stdin
	docker push $(TARGET_PREFIX)$(@:push-%=%):$(IMGTAG)

# Retag 
retag-%:
	docker tag $(TARGET_PREFIX)$(@:retag-%=%):$(IMGTAG) $(TARGET_PREFIX)$(@:retag-%=%):latest

clean-tag-%:
	@echo "No way to remove $(TARGET_PREFIX)$(@:clean-tag-%=%):$(TAG) from docker hub at the moment"

unit-tests:
	cd ../.. && tox

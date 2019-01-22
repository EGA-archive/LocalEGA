SHELL := /bin/bash

TAG=$(shell git rev-parse --short HEAD)

ifdef TRAVIS_COMMIT
TAG=$(TRAVIS_COMMIT)
endif

ifdef TRAVIS_PULL_REQUEST
TAG=PR$(TRAVIS_PULL_REQUEST)
endif

IMGTAG=$(TAG)

TARGET_PREFIX=egarchive/lega-

LEGA_GID=1000

# Must find better, but working so far
MAIN_REPO := $(abspath $(dir $(abspath $(lastword $(MAKEFILE_LIST))))/../..)

.PHONY: all erase clean purge base inbox push

all: base inbox

base inbox:
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
	@$(call clean_tag,$(TARGET_PREFIX)inbox, $(TAG))

erase:
	@$(call remove_dangling,$(TARGET_PREFIX)base)
	@$(call remove_dangling,$(TARGET_PREFIX)inbox)

purge:
	@$(call remove_dangling,)


# Check if 
check-%: $(MAIN_REPO)/Dockerfile.%
	git diff --exit-code --quiet origin/master -- $< || make $(@:check-%=%)

# Download images
pull-%:
	docker pull $(TARGET_PREFIX)$(@:pull-%=%):$(IMGTAG)

# Upload images
push-%:
	-@echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USER" --password-stdin
	docker push $(TARGET_PREFIX)$(@:push-%=%):$(IMGTAG)

# Retag 
retag:
	-@echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USER" --password-stdin
	docker tag $(TARGET_PREFIX)base:$(TAG) $(TARGET_PREFIX)base:latest
	docker tag $(TARGET_PREFIX)inbox:$(TAG) $(TARGET_PREFIX)inbox:latest

clean-tag:
	@echo "No way to remove $(TARGET_PREFIX)base:$(TAG) from docker hub at the moment"
	@echo "No way to remove $(TARGET_PREFIX)inbox:$(TAG) from docker hub at the moment"

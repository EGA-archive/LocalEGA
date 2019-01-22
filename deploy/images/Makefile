SHELL := /bin/bash

ifndef CHECKOUT
CHECKOUT=$(shell git rev-parse --abbrev-ref HEAD)
endif

TAG=$(shell git rev-parse --short HEAD)

ifdef TRAVIS_COMMIT
TAG=$(TRAVIS_COMMIT)
endif

ifdef TRAVIS_PULL_REQUEST
TAG=PR$(TRAVIS_PULL_REQUEST)
endif

TARGET_PREFIX=egarchive/lega-

.PHONY: all erase clean purge base inbox push

all: base inbox

base inbox:
	docker build \
	       --build-arg checkout=$(CHECKOUT) \
	       --cache-from $(TARGET_PREFIX)$@:latest \
               --tag $(TARGET_PREFIX)$@:$(TAG) \
               --tag $(TARGET_PREFIX)$@:latest \
               $@

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
check-%: %/Dockerfile
	git diff --exit-code --quiet origin/master -- $< || make $(@:check-%=%)

check: check-base check-inbox

pull: TAG=latest
pull pull-tag:
	docker pull $(TARGET_PREFIX)base:$(TAG)
	docker pull $(TARGET_PREFIX)inbox:$(TAG)

push: TAG=latest
push push-tag:
	docker push $(TARGET_PREFIX)base:$(TAG)
	docker push $(TARGET_PREFIX)inbox:$(TAG)

retag:
	docker tag $(TARGET_PREFIX)base:$(TAG) $(TARGET_PREFIX)base:latest
	docker tag $(TARGET_PREFIX)inbox:$(TAG) $(TARGET_PREFIX)inbox:latest

clean-tag:
	@echo "No way to remove $(TARGET_PREFIX)base:$(TAG) from docker hub at the moment"
	@echo "No way to remove $(TARGET_PREFIX)inbox:$(TAG) from docker hub at the moment"

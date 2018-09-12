
# Add those packages to the containers, in case DEV is defined
ifdef DEV
DEV_PACKAGES=nss-tools nc nmap tcpdump lsof strace bash-completion bash-completion-extras
endif

CHECKOUT=$(shell git rev-parse --abbrev-ref HEAD)
TAG=$(shell git rev-parse --short HEAD)
ifdef TRAVIS_COMMIT
TAG=$(TRAVIS_COMMIT)
CHECKOUT=$(TAG)
endif
ifdef TRAVIS_PULL_REQUEST_SHA
TAG=$(TRAVIS_PULL_REQUEST_SHA)
endif

TARGET_PREFIX=nbisweden/ega

BUILD_ARGS=--build-arg checkout=$(CHECKOUT)

.PHONY: all erase delete clean cleanall base inbox

all: base inbox

base: BUILD_ARGS+=--build-arg DEV_PACKAGES="$(DEV_PACKAGES)"
inbox: BUILD_ARGS+=--build-arg AUTH_BRANCH=cega-ids
base inbox:
	docker build ${BUILD_ARGS} \
                     --cache-from $(TARGET_PREFIX)-$@:latest \
                     --tag $(TARGET_PREFIX)-$@:$(TAG) \
										 --tag $(TARGET_PREFIX)-$@:dev \
                     --tag $(TARGET_PREFIX)-$@:latest \
                     $@

clean:
	@docker images $(TARGET_PREFIX)-* -f "dangling=true" -q | uniq | while read n; do docker rmi -f $$n; done

cleanall:
	@docker images -f "dangling=true" -q | uniq | while read n; do docker rmi -f $$n; done

delete:
	@docker images $(TARGET_PREFIX)-* --format "{{.Repository}} {{.Tag}}" | awk '{ if ($$2 != "$(TAG)" && $$2 != "latest") print $$1":"$$2; }' | uniq | while read n; do docker rmi $$n; done

erase: # erasing all including base
	@docker images $(TARGET_PREFIX)-* -q | uniq | while read n; do docker rmi -f $$n; done

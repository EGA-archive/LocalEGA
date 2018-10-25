
# Add those packages to the containers, in case DEV is defined
ifdef DEV
DEV_PACKAGES=nss-tools nc nmap tcpdump lsof strace bash-completion bash-completion-extras
endif

ifndef CHECKOUT
CHECKOUT=$(shell git rev-parse --abbrev-ref HEAD)
endif
TAG=$(shell git rev-parse --short HEAD)
ifdef TRAVIS_COMMIT
TAG=$(TRAVIS_COMMIT)
CHECKOUT=$(TAG)
endif
ifdef TRAVIS_PULL_REQUEST
TAG=PR$(TRAVIS_PULL_REQUEST)
CHECKOUT=$(TRAVIS_PULL_REQUEST_SHA)
endif

TARGET_PREFIX=nbisweden/ega

.PHONY: all erase delete clean cleanall base os inbox push

all: os base inbox

os:
	docker build --build-arg DEV_PACKAGES="$(DEV_PACKAGES)" \
                     --cache-from $(TARGET_PREFIX)-$@:latest \
                     --tag $(TARGET_PREFIX)-$@:latest \
                     $@

base:
	docker build --build-arg checkout=$(CHECKOUT) \
                     --cache-from $(TARGET_PREFIX)-$@:latest \
                     --tag $(TARGET_PREFIX)-$@:$(TAG) \
                     --tag $(TARGET_PREFIX)-$@:dev \
                     --tag $(TARGET_PREFIX)-$@:latest \
                     $@

inbox:
	docker build --cache-from $(TARGET_PREFIX)-$@:latest \
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

push:
	docker push $(TARGET_PREFIX)-base:latest
	docker push $(TARGET_PREFIX)-os:latest
	docker push $(TARGET_PREFIX)-inbox:latest

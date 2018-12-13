# Add those packages to the containers, in case DEV is defined
ifdef DEV
DEV_PACKAGES=nss-tools nc nmap tcpdump lsof strace bash-completion bash-completion-extras
endif

CHECKOUT=$(shell git rev-parse --abbrev-ref HEAD)
TAG=$(shell git rev-parse --short HEAD)
TARGET_PREFIX=egarchive/

BUILD_ARGS=--build-arg checkout=$(CHECKOUT)

.PHONY: all erase delete clean cleanall os base inbox

all: os base inbox

os: BUILD_ARGS+=--build-arg DEV_PACKAGES="$(DEV_PACKAGES)"
base: os
inbox: os
base: BUILD_ARGS+=--build-arg cryptor_checkout=master
os base inbox:
	docker build ${BUILD_ARGS} \
                     --cache-from $(TARGET_PREFIX)$@:latest \
                     --tag $(TARGET_PREFIX)$@:$(TAG) \
                     --tag $(TARGET_PREFIX)$@:latest \
                     $@

remove-%:
	@docker rmi $(TARGET_PREFIX)$(@:remove-%=%):latest

clean:
	@docker images $(TARGET_PREFIX)* -f "dangling=true" -q | uniq | while read n; do docker rmi -f $$n; done

cleanall:
	@docker images -f "dangling=true" -q | uniq | while read n; do docker rmi -f $$n; done

delete:
	@docker images $(TARGET_PREFIX)* --format "{{.Repository}} {{.Tag}}" | awk '{ if ($$2 != "$(TAG)" && $$2 != "latest") print $$1":"$$2; }' | uniq | while read n; do docker rmi $$n; done

erase:
	@docker images $(TARGET_PREFIX)inbox -q | uniq | while read n; do docker rmi -f $$n; done
	@docker images $(TARGET_PREFIX)lega -q | uniq | while read n; do docker rmi -f $$n; done
	@docker images $(TARGET_PREFIX)base -q | uniq | while read n; do docker rmi -f $$n; done

push pull:
	docker $@ $(TARGET_PREFIX)os:latest
	docker $@ $(TARGET_PREFIX)base:latest
	docker $@ $(TARGET_PREFIX)inbox:latest

os-check: os/Dockerfile
base-check: base/Dockerfile
inbox-check: inbox/Dockerfile
os-check base-check inbox-check:
	git diff --exit-code --quiet origin/master -- $< || make $(@:%-check=%)

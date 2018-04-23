
# Add those packages to the containers, in case DEV is defined
ifdef DEV
DEV_PACKAGES="nss-tools nmap tcpdump lsof strace bash-completion bash-completion-extras"
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

TARGET=nbisweden/ega

.PHONY: all erase delete clean cleanall base inbox

all: base inbox

base: PIP_EGA_PACKAGES=pika==0.11.0 psycopg2==2.7.4 cryptography==2.1.4 aiohttp==3.0.7 aiohttp-jinja2==0.13.0 pgpy fusepy aiopg==0.13.0
base inbox:
	docker build --build-arg checkout=$(CHECKOUT) \
                     --build-arg PIP_EGA_PACKAGES="$(PIP_EGA_PACKAGES)" \
                     --build-arg DEV_PACKAGES="$(DEV_PACKAGES)" \
                     --cache-from $(TARGET)-$@:latest \
                     --tag $(TARGET)-$@:$(TAG) \
                     --tag $(TARGET)-$@:latest \
                     $@

clean:
	@docker images $(TARGET)-* -f "dangling=true" -q | uniq | while read n; do docker rmi -f $$n; done

cleanall:
	@docker images -f "dangling=true" -q | uniq | while read n; do docker rmi -f $$n; done

delete:
	@docker images $(TARGET)-* --format "{{.Repository}} {{.Tag}}" | awk '{ if ($$2 != "$(TAG)" && $$2 != "latest") print $$1":"$$2; }' | uniq | while read n; do docker rmi $$n; done

erase: # erasing all but base
	@docker images $(TARGET)-inbox -q | uniq | while read n; do docker rmi -f $$n; done

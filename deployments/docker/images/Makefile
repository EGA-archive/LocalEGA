
# Add those packages to the containers, in case DEV is defined
ifdef DEV
DEV_PACKAGES="nss-tools nc nmap tcpdump lsof strace bash-completion bash-completion-extras"
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

EGA_IMAGES=mq inbox worker vault keys cega-users bootstrap

.PHONY: all push pull common erase delete clean cleanall $(EGA_IMAGES)

all: images

images: common
	@make -j 4 $(EGA_IMAGES)

common:
	docker build --build-arg checkout=$(CHECKOUT) \
                     --build-arg DEV_PACKAGES="$(DEV_PACKAGES)" \
                     --cache-from $(TARGET)-$@:latest \
                     --tag $(TARGET)-$@:$(TAG) \
                     --tag $(TARGET)-$@:latest \
                     $@


inbox:      PIP_EGA_PACKAGES=pika==0.11.0 fusepy
worker:     PIP_EGA_PACKAGES=pika==0.11.0 pycryptodomex==3.4.7 psycopg2==2.7.3.2 cryptography==2.1.3
keys:       PIP_EGA_PACKAGES=aiohttp==2.3.8 cryptography==2.1.3
vault:      PIP_EGA_PACKAGES=pika==0.11.0 psycopg2==2.7.3.2
bootstrap:  PIP_EGA_PACKAGES=pgpy
cega-users: PIP_EGA_PACKAGES=aiohttp==2.3.8 aiohttp-jinja2==0.13.0



$(EGA_IMAGES):
	docker build --build-arg checkout=$(CHECKOUT) \
                     --build-arg PIP_EGA_PACKAGES="$(PIP_EGA_PACKAGES)" \
                     --cache-from $(TARGET)-$@:latest \
                     --tag $(TARGET)-$@:$(TAG) \
                     --tag $(TARGET)-$@:latest \
                     $@

pull:
	for image in $(EGA_IMAGES); do docker pull $(TARGET)-$$image:latest; done

push:
	for image in $(EGA_IMAGES); do docker push $(TARGET)-$$image:latest; done

clean:
	@docker images $(TARGET)-* -f "dangling=true" -q | uniq | while read n; do docker rmi -f $$n; done

cleanall:
	@docker images -f "dangling=true" -q | uniq | while read n; do docker rmi -f $$n; done

delete:
	@docker images $(TARGET)-* --format "{{.Repository}} {{.Tag}}" | awk '{ if ($$2 != "$(TAG)" && $$2 != "latest") print $$1":"$$2; }' | uniq | while read n; do docker rmi $$n; done

erase:
	@docker images $(TARGET)-* -q | uniq | while read n; do docker rmi -f $$n; done

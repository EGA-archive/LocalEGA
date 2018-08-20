
CHECKOUT=$(shell git rev-parse --abbrev-ref HEAD)
TAG=$(shell git rev-parse --short HEAD)
TARGET_PREFIX=nbisweden/ega


BUILD_ARGS=--build-arg checkout=$(CHECKOUT)

.PHONY: all erase delete clean cleanall base inbox

all: base lega inbox

base: PIP_EGA_PACKAGES=pika==0.12.0 psycopg2-binary==2.7.5 cryptography==2.3 aiohttp==3.0.7 aiohttp-jinja2==0.13.0 pgpy boto3 aiohttp-jinja2==0.13.0
inbox: BUILD_ARGS+=--build-arg AUTH_BRANCH=cega-ids
base inbox:
	docker build ${BUILD_ARGS} \
                     --cache-from $(TARGET_PREFIX)-$@:latest \
                     --tag $(TARGET_PREFIX)-$@:$(TAG) \
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

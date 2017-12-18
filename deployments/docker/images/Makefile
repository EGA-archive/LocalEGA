TAG=$(shell git rev-parse --short HEAD)
ifdef TRAVIS_COMMIT
TAG=$(TRAVIS_COMMIT)
endif
ifdef TRAVIS_PULL_REQUEST_SHA
TAG=$(TRAVIS_PULL_REQUEST_SHA)
endif

TARGET=nbisweden/ega

EGA_IMAGES=mq inbox frontend worker vault keys cega_users cega_mq

.PHONY: all push pull common erase delete clean cleanall bootstrap $(EGA_IMAGES)

all: pull common images bootstrap

images: $(EGA_IMAGES)
common $(EGA_IMAGES):
	docker build --build-arg checkout=$(TAG) \
                     --cache-from $(TARGET)-$@:latest \
                     --tag $(TARGET)-$@:$(TAG) \
                     --tag $(TARGET)-$@:latest \
                     $@

bootstrap:
	docker build -f worker/Dockerfile.$@ --build-arg checkout=$(TAG) \
                     --cache-from $(TARGET)-$@:latest \
                     --tag $(TARGET)-$@:$(TAG) \
                     --tag $(TARGET)-$@:latest \
                     worker

pull:
	for image in common bootstrap $(EGA_IMAGES); do docker pull $(TARGET)-$$image:latest; done

push:
	for image in common bootstrap $(EGA_IMAGES); do docker push $(TARGET)-$$image:latest; done

clean:
	@docker images $(TARGET)-* -f "dangling=true" -q | uniq | while read n; do docker rmi -f $$n; done

cleanall:
	@docker images -f "dangling=true" -q | uniq | while read n; do docker rmi -f $$n; done

delete:
	@docker images $(TARGET)-* --format "{{.Repository}} {{.Tag}}" | awk '{ if ($$2 != "$(TAG)" && $$2 != "latest") print $$1":"$$2; }' | uniq | while read n; do docker rmi $$n; done

erase:
	@docker images $(TARGET)-* -q | uniq | while read n; do docker rmi -f $$n; done

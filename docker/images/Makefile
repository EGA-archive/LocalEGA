
EGA_IMAGES=common db mq inbox worker cega_users cega_mq monitors

TARGET=nbisweden/ega

ifndef CI_BUILD_REF
TAG=$(shell git rev-parse --short HEAD)
else
TAG=$(TRAVIS_COMMIT)
endif

all: $(EGA_IMAGES)

.PHONY: all push $(EGA_IMAGES)

all: $(EGA_IMAGES)

worker: common
cega_users: common

$(EGA_IMAGES):
	docker build --cache-from $(TARGET)-$@:latest --tag $(TARGET)-$@:$(TAG) --tag $(TARGET)-$@:latest $@

push:
	docker login
	for image in $(EGA_IMAGES); do docker push $(TARGET)-$$image:latest; done

clean:
	@docker images -f "dangling=true" -q | uniq | while read n; do docker rmi $$n; done

delete:
	@docker images $(TARGET)-* --format "{{.ID}} {{.Tag}}" | awk '{ if ($$2 != "$(TAG)" && $$2 != "latest") print $$1; }' | uniq | while read n; do docker rmi $$n; done

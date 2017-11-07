
EGA_IMAGES=common db mq inbox worker cega_users cega_mq monitors

TARGET=nbisweden/ega

TAG=$(shell git rev-parse --short HEAD)

all: $(EGA_IMAGES)

.PHONY: all push $(EGA_IMAGES)

all: $(EGA_IMAGES)

worker: common
cega_users: common

$(EGA_IMAGES):
	docker build --tag $(TARGET)-$@:$(TAG) $@
	docker tag $(TARGET)-$@:$(TAG) $(TARGET)-$@:latest

push:
	docker login
	for image in $(EGA_IMAGES); do docker push $(TARGET)-$image:latest; done

clean:
	docker images | awk '/none/{print $$3}' | while read n; do docker rmi $$n; done

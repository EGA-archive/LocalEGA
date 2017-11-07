
EGA_IMAGES=common db mq inbox worker cega_users cega_mq monitors

TARGET=nbisweden/ega

all: $(EGA_IMAGES)

.PHONY: all $(EGA_IMAGES) push

all: $(EGA_IMAGES)

$(EGA_IMAGES):
	docker build --cache-from $(TARGET):$@ --tag $(TARGET):$@ $@

push:
	docker login
	docker push $(TARGET)

clean:
	docker images | awk '/none/{print $$3}' | while read n; do docker rmi $$n; done

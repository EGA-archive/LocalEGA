
EGA_IMAGES=common db mq inbox frontend worker keys

all: $(EGA_IMAGES)

.PHONY: all $(EGA_IMAGES)

$(EGA_IMAGES):
	docker build -t nbis/ega:$@ $@

clean:
	docker images | awk '/none/{print $$3}' | while read n; do docker rmi $$n; done

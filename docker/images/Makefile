
EGA_IMAGES=common db inbox mq worker keys

NAMES=$(IMAGES:%=ega-%)

all: gpg2.1 $(EGA_IMAGES)

.PHONY: all $(EGA_IMAGES)

gpg%:
	docker build -t gpg:$(@:gpg%=%) -f common/$@.dockerfile common

$(EGA_IMAGES):
	docker build -t ega:$@ $@

clean-none:
	docker images | awk '/none/{print $$3}' | while read n; do docker rmi $$n; done

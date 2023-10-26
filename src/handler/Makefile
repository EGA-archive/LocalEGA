
VERSION=

.PHONY: latest build

all: latest

build: ARGS+=--target BUILD
latest build: 
	docker build $(ARGS) -t fega/handler:$@$(VERSION) .


.PHONY: all bootstrap

all: up

.env private:
	@docker run --rm -it --name ega_bootstrap -v ${PWD}:/ega nbisweden/ega-worker /ega/bootstrap/boot.sh

bootstrap: .env private

up: .env private
	@docker-compose up -d

down: #.env
	@docker-compose down -v

clean:
	rm -rf .env private


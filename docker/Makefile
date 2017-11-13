
.PHONY: all bootstrap

all: up

.env private:
	@docker run --rm -it --name ega_bootstrap -v ${PWD}:/ega nbisweden/ega-worker /ega/bootstrap/boot.sh

bootstrap: .env private

clean:
	rm -rf .env private

up: bootstrap
	@docker-compose up -d

ps:
	@docker-compose ps

down: #.env
	@docker-compose down -v



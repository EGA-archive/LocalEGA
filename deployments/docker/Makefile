
.PHONY: all bootstrap

all: up

.env private:
	@docker run --rm -it -v ${PWD}:/ega nbisweden/ega-bootstrap

bootstrap: .env private

clean:
	rm -rf .env private

up: bootstrap
	@docker-compose up -d

ps:
	@docker-compose ps

down: #.env
	@docker-compose down -v



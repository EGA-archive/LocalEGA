ARGS=

.PHONY: all bootstrap private

all: up

private:
	@docker run --rm -it -v ${PWD}:/ega -v ${PWD}/../../extras/db.sql:/tmp/db.sql nbisweden/ega-bootstrap ${ARGS}

bootstrap: private

clean:
	rm -rf .env private

up: bootstrap
	@docker-compose up -d

ps:
	@docker-compose ps

down: #.env
	@docker-compose down -v



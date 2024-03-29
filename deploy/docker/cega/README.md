# Fake Central EGA

We use 2 stubbing services in order to fake the necessary Central EGA components (mostly for local tests or github Actions).

| Container        | Role |
|-----------------:|------|
| `cega`           | Sets up a small list of test users, and consumes messages from the broker |
| `cega-mq`        | Sets up a RabbitMQ message broker with appropriate accounts, exchanges, queues and bindings |


We include 2 dummy users: `jane` and `john`.
> Their password and their ssh-key passphrase are their username.

You can start the Central EGA (fake) component with:

	# Start the Central EGA broker
	docker-compose up -d cega-mq

    # and after a few seconds, start the Central all-in-one service
	docker-compose up -d cega

The Central EGA services are at (and you can update `docker-compose.yml` accordingly)

| Service        | URL | Credentials | Example |
|---------------:|-----|-------------|---------|
| NSS            | `http://cega:8080` | `fega:testing` | `curl -u fega:testing http://localhost:8080/username/john` |
| RabbitMQ       | `amqp://cega-mq:5672/%2F` | `admin:secret` | `CEGA_CONNECTION=amqp://admin:secret@cega-mq:5672/%2F` |


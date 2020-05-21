# LocalEGA internal message broker in a docker image

We use [RabbitMQ 3.7.8](https://hub.docker.com/_/rabbitmq) including the management plugins.

## Configuration

The following environment variables can be used to configure the broker:

| Variable | Description |
|---------:|:------------|
| `MQ_USER` | Default user (with admin rights) |
| `MQ_PASSWORD_HASH` | Password hash for the above user |
| `CEGA_CONNECTION` | DSN URL for the shovels and federated queues with CentralEGA |

If you want persistent data, you can use a named volume or a bind-mount and make it point to `/var/lib/rabbitmq`.

## Sample Docker Compose definition

```
version: '3.3'

services:

  mq:
    image: egarchive/lega-mq:latest
    hostname: mq
    ports:
      - "5672:5672"
      - "15672:15672"
    environment:
      - MQ_USER=admin
      - MQ_PASSWORD_HASH=4tHURqDiZzypw0NTvoHhpn8/MMgONWonWxgRZ4NXgR8nZRBz
      - CEGA_CONNECTION

```

Run `docker-compose up -d` to test it.

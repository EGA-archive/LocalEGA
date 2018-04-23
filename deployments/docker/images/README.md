# LocalEGA docker images

`docker-compose` has a subcommand to build the images.

However, we created a Makefile to simplify the building process.

In the current folder, type `make` and the images are created in order.

It takes some time.

Later on, if the `nbisweden/ega-base` does not need to be recreated, one can type `make all`.

A typical build goes as follows:

	`make base`
	`make inbox`

## Results

`rabbitmq:management`, `postgres:latest`, `centos:7.4.1708` are pulled from the main Docker hub.

The following images are created locally:

| Repository | Tag      | Role |
|------------|:--------:|------|
| nbisweden/ega-inbox    | <HEAD commit> or latest | SFTP server on top of `nbisweden/ega-base:latest` |
| nbisweden/ega-base   | <HEAD commit> or latest | Base Image for all services including python 3.6.1 |


We also use 2 stubbing services in order to fake the necessary Central EGA components

| Repository | Tag      | Role |
|------------|:--------:|------|
| cega-users | <HEAD commit> or latest | Sets up a postgres database with appropriate tables |
| cega-mq | <HEAD commit> or latest | Sets up a RabbitMQ message broker with appropriate accounts, exchanges, queues and bindings |
| cega-eureka | <HEAD commit> or latest | Sets up a fake Eureka service discovery server in order to make the LocalEGA Keyserver register |

## Logging

We also make use of ELK stack for logging thus the `elasticsearch-oss` `logstash-oss` and `kibana-oss` will be pulled from Docker hub.

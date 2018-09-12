# LocalEGA docker images

`docker-compose` has a subcommand to build the images.

However, we created a Makefile to simplify the building process.

In the current folder, type `make` and the images are created in order.

It takes some time.

Later on, if the `nbisweden/ega-*` do not need to be recreated, one can type `make all`.

A typical build goes as follows:

	`make base`

## Results

`rabbitmq:management`, `postgres:9.6`, `centos:7.4.1708` are pulled from the main Docker hub.

The following images are created locally:

| Repository | Tag      | Role |
|------------|:--------:|------|
| nbisweden/ega-inbox  | `<HEAD commit>`, `latest` or `dev`  | SFTP server on top of `nbisweden/ega-base` |
| nbisweden/ega-base   | `<HEAD commit>`, `latest` or `dev` | Base Image for all services including python 3.6.1 |


We also use 2 stubbing services in order to fake the necessary Central EGA components

| Repository | Tag      | Role |
|------------|:--------:|------|
| cega-users | `<HEAD commit>` , `latest` or `dev` | Sets up a postgres database with appropriate tables, on top of `nbisweden/ega-base` |
| cega-mq | `rabbitmq:3.6.14-management` | Sets up a RabbitMQ message broker with appropriate accounts, exchanges, queues and bindings |
| cega-eureka | `<HEAD commit>`, `latest` or `dev` | Sets up a fake Eureka service discovery server in order to make the LocalEGA Keyserver register, on top of `nbisweden/ega-base` |

## Logging

ELK stack can be added as a logging solution using the `elasticsearch-oss` `logstash-oss` and `kibana-oss`. This requires adding the images to the `docker-compose` YML.

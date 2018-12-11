# LocalEGA docker images

`docker-compose` has a subcommand to build the images.

However, we created a Makefile to simplify the building process.

In the current folder, type `make` and the images are created in order.

It takes some time.

Later on, if the `egarchive/*` do not need to be recreated, one can type `make all`.

A typical build goes as follows:

	make base

## Results

`rabbitmq:3.7.8-management`, `postgres:11`, `centos:7.5.1804` are pulled from the main Docker hub.

The following images are created locally:

| Repository | Tag      | Role |
|------------|:--------:|------|
| `egarchive/base`   | `latest` | CentOS based image with necessary packages for running LocalEGA. |
| `egarchive/inbox`  | `latest` | SFTP server on top of `egarchive/base` |
| `egarchive/lega`   | `latest` | Base Image for all services includes `python 3.6` |


We also use 2 stubbing services in order to fake the necessary Central EGA components

| Repository | Tag      | Role |
|------------|:--------:|------|
| `cega-users` | `<HEAD commit>` , `latest` or `dev` | Sets up a postgres database with appropriate tables, on top of `nbisweden/ega-base` |
| `cega-mq` | `rabbitmq:3.7.8-management` | Sets up a RabbitMQ message broker with appropriate accounts, exchanges, queues and bindings |
| `cega-eureka` | `<HEAD commit>`, `latest` or `dev` | Sets up a fake Eureka service discovery server in order to make the LocalEGA Keyserver register, on top of `nbisweden/ega-base` |


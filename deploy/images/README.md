# LocalEGA docker images

`docker-compose` has a subcommand to build the images.

However, we created a Makefile to simplify the building process.

In the current folder, type `make` and the images are created in order.

It takes some time.

Later on, if the `nbisweden/ega-*` do not need to be recreated, one can type `make all`.

A typical build goes as follows:

	make base

## Results

`rabbitmq:3.6.14-management`, `postgres:9.6`, `centos:7.5.1804` are pulled from the main Docker hub.

The following images are created locally:

| Repository | Tag      | Role |
|------------|:--------:|------|
| `nbisweden/ega-os`   | `latest` | CentOS based image with necessary packages for running LocalEGA. |
| `nbisweden/ega-inbox`  | `<HEAD commit>`, `latest` or `dev`  | SFTP server on top of `nbisweden/ega-base` and `nbisweden/ega-openssh` |
| `nbisweden/ega-base`   | `<HEAD commit>`, `latest` or `dev` | Base Image for all services includes `python 3.6` |

`nbisweden/ega-inbox` is dependent on the OpenSSH image that is built in the https://github.com/NBISweden/LocalEGA-auth

| Repository | Tag      | Role |
|------------|:--------:|------|
| `nbisweden/ega-openssh`   | `latest` | OpenSSH SFTP server version `7.7p1` on top of `nbisweden/ega-base` patched in order to be used by `nbisweden/ega-inbox` |

We also use 2 stubbing services in order to fake the necessary Central EGA components

| Repository | Tag      | Role |
|------------|:--------:|------|
| `cega-users` | `<HEAD commit>` , `latest` or `dev` | Sets up a postgres database with appropriate tables, on top of `nbisweden/ega-base` |
| `cega-mq` | `rabbitmq:3.6.14-management` | Sets up a RabbitMQ message broker with appropriate accounts, exchanges, queues and bindings |
| `cega-eureka` | `<HEAD commit>`, `latest` or `dev` | Sets up a fake Eureka service discovery server in order to make the LocalEGA Keyserver register, on top of `nbisweden/ega-base` |

## Logging

ELK stack can be added as a logging solution using the `elasticsearch-oss` `logstash-oss` and `kibana-oss`. This requires adding the images to the `docker-compose` YML.

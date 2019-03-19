# LocalEGA docker images

`docker-compose` has a subcommand to build the images.

However, we created a Makefile to simplify the building process.

In the current folder, the images are created by executing:

	make

It takes some time.

The result is an image, named `egarchive/lega-base`, and containing `python 3.6` and the LocalEGA services.

## Dependencies

The following images are pulled from Docker Hub:

* `egarchive/lega-mq` (based on `rabbitmq:3.6.14-management`)
* `egarchive/lega-db` (based on `postgres:11.2`)
* `egarchive/lega-inbox` (based on OpenSSH version 7.8p1 and CentOS7)
* `nbisweden/lega-inbox` (based on Apache Mina)
* `python:3.6-alpine3.8` 

The [`egarchive/lega-inbox`](https://github.com/EGA-archive/LocalEGA-inbox) and [`nbisweden/lega-inbox`](https://github.com/NBISweden/LocalEGA-inbox) are LocalEGA inboxes, fetching user credentials from CentralEGA and sending file events notifications to the configured message broker. It is based on OpenSSH SFTP server version `7.8p1` 

## Testing

We use 2 stubbing services in order to fake the necessary Central EGA components (mostly for local or Travis tests).

| Repository   | Role |
|--------------|------|
| `cega-users` | Sets up a small list of test users, on top of `egarchive/lega-base` |
| `cega-mq`    | Sets up a RabbitMQ message broker with appropriate accounts, exchanges, queues and bindings |

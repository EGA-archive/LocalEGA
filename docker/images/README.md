# LocalEGA docker images

docker-compose has a subcommand to build the images.

However, we created a Makefile to simplify the building process.

In the current folder, type `make` and the images are created in order.

It takes some time.

Later on, if the `nbis/ega:common` does not need to be recreated, you
can type `make -j 4` (where `4` is an arbitrary number of parallel
builds: check the numbers of cores on your machine)

# Results

`rabbitmq:management`, `postgres:latest`, `centos:latest` are pulled from the main docker hub.

The following images are created locally:

| Repository | Tag      | Role |
|------------|:--------:|------|
| nbis/ega   | db       | Sets up a postgres database with appropriate tables |
| nbis/ega   | mq       | Sets up a RabbitMQ message broker with appropriate accounts, exchanges, queues and bindings |
| nbis/ega   | common   | Image including python 3.6.1, GnuPG 2.2.0 and OpenSSH 7.5 |
| nbis/ega   | inbox    | SFTP server on top of `nbis/ega:common` |

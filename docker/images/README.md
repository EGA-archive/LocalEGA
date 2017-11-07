# LocalEGA docker images

docker-compose has a subcommand to build the images.

However, we created a Makefile to simplify the building process.

In the current folder, type `make` and the images are created in order.

It takes some time.

Later on, if the `nbisweden/ega-common` does not need to be recreated, you
can type `make -j 4` (where `4` is an arbitrary number of parallel
builds: check the numbers of cores on your machine)

# Results

`rabbitmq:management`, `postgres:latest`, `centos:latest` are pulled from the main docker hub.

The following images are created locally:

| Repository | Tag      | Role |
|------------|:--------:|------|
| nbisweden/ega-db       | <HEAD commit> or latest | Sets up a postgres database with appropriate tables |
| nbisweden/ega-mq       | <HEAD commit> or latest | Sets up a RabbitMQ message broker with appropriate accounts, exchanges, queues and bindings |
| nbisweden/ega-common   | <HEAD commit> or latest | Image including python 3.6.1 |
| nbisweden/ega-inbox    | <HEAD commit> or latest | SFTP server on top of `nbisweden/ega-common:latest` |
| nbisweden/ega-worker   | <HEAD commit> or latest | Adding GnuPG 2.2.2 to `nbisweden/ega-common:latest` |
| nbisweden/ega-monitors | <HEAD commit> or latest | Including rsyslog or logstash |

We also use 2 stubbing images in order to fake the necessary Central EGA components

| Repository | Tag      | Role |
|------------|:--------:|------|
| nbisweden/ega-cega\_users | <HEAD commit> or latest | Sets up a postgres database with appropriate tables |
| nbisweden/ega-cega\_mq    | <HEAD commit> or latest | Sets up a RabbitMQ message broker with appropriate accounts, exchanges, queues and bindings |

# LocalEGA docker images

docker-compose has a subcommand to build the images.

However, the gpg upgrade to 2.1 is not included and should be created for the worker and keys images.

We created a Makefile to simplify the building process.

In the current folder, type `make` and the images are created in order.

It takes some time.

# Results

`rabbitmq:management`, `postgres:latest`, `centos:latest` are pulled from the main docker hub.

The following images are created locally:

| Repository  | Tag  | Role |
|-------------|:----:|------|
| ega | db     | Sets up a postgres database with appropriate tables |
| ega | mq     | Sets up a RabbitMQ message broker with appropriate accounts, exchanges, queues and bindings |
| ega | common | Image including python 3.6.1 and extra packages for the LocalEGA code |
| ega | inbox  | SFTP server and Python 3.6.1 |
| gpg | 2.1    | Upgrading to GnuPG 2.1.20 and OpenSSH 7.5 |
| ega | worker | LocalEGA code with a GPG upgrade |

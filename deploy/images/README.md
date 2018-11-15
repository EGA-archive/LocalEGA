# LocalEGA docker images

`docker-compose` has a subcommand to build the images.

However, we created a Makefile to simplify the building process.

In the current folder, type `make` and the images are created in order.

It takes some time.

Later on, if the `egarchive/*` do need to be recreated, one can type `make`.

`rabbitmq:3.6.16-management`, `postgres:11`, `centos:7.5.1804`,
`minio/minio:latest` are pulled from the main Docker hub.

The following images are created locally:

| Repository | Tag      | Role |
|------------|:--------:|------|
| egarchive/base   | <HEAD commit> or latest | Base Operating System, including python 3.6.1 and extra libraries |
| egarchive/lega   | <HEAD commit> or latest | All LocalEGA microservices on top of `egarchive/base:latest` |
| egarchive/inbox  | <HEAD commit> or latest | SFTP server on top of `egarchive/base:latest` |

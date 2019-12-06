# Deploy LocalEGA using Docker

## Bootstrap

You can then [generate the private data](bootstrap), with:

	make bootstrap

This requires `openssl` (>=1.1), `ssh-keygen` (=>6.5), `expect` and [`crypt4gh-keygen`](https://github.com/EGA-archive/crypt4gh).

The command will create a `.env` file and a `private` folder holding
the necessary data (ie the master keypair, the SSL
certificates for internal communication, passwords, default users,
etc...)

It will also create a docker network `cega` used by the (fake) CentralEGA instance,
separate from to network used by the LocalEGA instance.

These networks are reflected in their corresponding YML files
* `private/cega.yml`
* `private/lega.yml`

The passwords are in `private/.trace` and the errors (if any) are in `private/.err`.

The test user credentials are found in `private/.users`.

## Running

	make up

This is just a shortcut for `docker-compose up -d`

Use `docker-compose up -d --scale ingest=3 --scale verify=5` instead,
if you want to start 3 ingestion and 5 verification workers.

Note that, in this architecture, we use separate volumes, e.g. for
the inbox area, for the archive (here backed by S3). They
will be created on-the-fly by docker-compose.

## Stopping

	make down

This is just a shortcut for `docker-compose down -v` (removing networks and volumes).

## Status

	make ps

This is just a shortcut for `docker-compose ps`

## Cleaning

To clean up everything you can use the following commands

Remove the bootstrap stuff (including private data and certificates):

    make clean

Remove the volumes:

    make clean-volumes

Remove everything:

    make clean-all


----

# LocalEGA docker image

Create the base image by executing:

	make image

It takes some time. The result is an image, named `egarchive/lega-base`, and containing `python 3.6` and the LocalEGA services.

The following images are pulled from Docker Hub:

* `egarchive/lega-mq` (based on `rabbitmq:3.6.14-management`)
* `egarchive/lega-db` (based on `postgres:11.2`)
* `egarchive/lega-inbox` (based on OpenSSH version 7.8p1 and CentOS7)
* `python:3.6-alpine3.10` 

The [`egarchive/lega-inbox`](https://github.com/EGA-archive/LocalEGA-inbox) is an inbox, fetching user credentials from CentralEGA and sending file events notifications to the configured message broker. It is based on OpenSSH SFTP server version `7.8p1` 

----

# Fake Central EGA

We use 2 stubbing services in order to fake the necessary Central EGA components (mostly for local or Travis tests).

| Container    | Role |
|--------------|------|
| `cega-users` | Sets up a small list of test users |
| `cega-mq`    | Sets up a RabbitMQ message broker with appropriate accounts, exchanges, queues and bindings |

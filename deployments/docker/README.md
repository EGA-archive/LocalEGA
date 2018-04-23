# Deploy LocalEGA using Docker

## Bootstrap

First [create the EGA docker images](images) beforehand, with `make -C images`.

You can then [generate the private data](bootstrap), with either:

	make bootstrap

> Note: you can run `bootstrap/boot.sh` on your host machine but
> you need the required tools installed, including Python 3.6, GnuPG
> 2.2.2, OpenSSL 1.0.2, `readlink`, `xxd`, ...

The command will create a `.env` file and a `private` folder holding
the necessary data (ie the GnuPG key, the RSA master key pair, the SSL
certificates for internal communication, passwords, default users,
etc...)

It will also create a docker network `cega` used by CEGA,
network that is external (more precisely a pre-existing network) to localEGA-fin and localEGA-swe.
One can also create the network manually using `docker network create cega`.

These networks are reflected in their corresponding YML files
* `private/cega.yml`
* `private/ega_swe1.yml`
* `private/ega_fin1.yml`

The passwords are in `private/<instance>/.trace` and the errors (if
any) are in `private/.err`.

## Running

	docker-compose up -d

Use `docker-compose up -d --scale ingest_swe1=3` instead, if you want to
start 3 ingestion workers.

Note that, in this architecture, we use 3 separate volumes: one for
the inbox area, one for the staging area, and one for the vault. They
will be created on-the-fly by docker-compose.

## Stopping

	docker-compose down -v

## Status

	docker-compose ps

# Deploy LocalEGA using Docker

# Bootstrap

First [create the EGA docker images](images) beforehand, with `make -C images`.

You can then [generate the private data](bootstrap), with either:

	docker run --rm -it -v ${PWD}/bootstrap:/ega nbisweden/ega-worker /ega/boot.sh
	
> Note: you can run `bootstrap/boot.sh` on your host machine but
> you need the required tools installed, including Python 3.6, GnuPG
> 2.2.2, OpenSSL, `readlink`, `xxd`, ...
	
You can afterwards copy the settings into place with

	bootstrap/populate.sh

The passwords are in `bootstrap/private/.trace.*` and the errors (if any) are in `bootstrap/.err`.

Alternatively, you can setup all [configuration files by hand](bootstrap/yourself.md).

# Running

	docker-compose up -d
	
Use `docker-compose up -d --scale ingest=3` instead, if you want to
start 3 ingestion workers.

Note that, in this architecture, we use 3 separate volumes: one for
the inbox area, one for the staging area, and one for the vault. They
will be created on-the-fly by docker-compose.

## Stopping

	docker-compose down -v

## Status

	docker-compose ps

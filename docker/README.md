# Deploy LocalEGA using Docker

## Bootstrap

First [create the EGA docker images](images) beforehand, with `make -C images`.

You can then [generate the private data](bootstrap), with:

	make bootstrap

The command will create a `.env` file and a `private` folder holding
the necessary data (ie the PGP key, the Main LEGA password, the SSL
certificates for internal communication, passwords, default users,
etc...)

It will also create a docker network `cega` used by the (fake) CentralEGA instance,
separate from to network used by the LocalEGA instance.

These networks are reflected in their corresponding YML files
* `private/cega.yml`
* `private/lega.yml`

The passwords are in `private/lega/.trace` and the errors (if any) are in `private/.err`.

### Bootstrapping with advanced options

If you want to use the [keyserver from
ega-data-api](https://github.com/EGA-archive/ega-data-api/tree/master/ega-data-api-key) instead of the [LocalEGA keyserver](https://github.com/NBISweden/LocalEGA/blob/dev/lega/keyserver.py), bootstrap with 

    make "ARGS=--keyserver ega" bootstrap


## Running

	docker-compose up -d

Use `docker-compose up -d --scale ingest=3 --scale verify=5` instead,
if you want to start 3 ingestion and 5 verification workers.

Note that, in this architecture, we use separate volumes, e.g. for
the inbox area, for the vault (here backed by S3). They
will be created on-the-fly by docker-compose.

## Stopping

	docker-compose down -v

## Status

	docker-compose ps

## Cleaning

To clean up everything you can use the following commands

Remove the bootstrap stuff (including network):

    make clean

Remove the volumes:

    make clean-volumes

Remove everything:

    make clean-all

# Deploy LocalEGA using Docker

# Bootstrap

First [create the EGA docker images](images) beforehand, with `make -C images`.

You can then [generate the private data](bootstrap), with either:

	a) bootstrap/generate.sh
	b) docker run --rm -it -v ${PWD}/bootstrap:/ega nbis/ega:worker /ega/generate.sh -f
	
Choose `b` if you don't have the required tools installed on your machine.
	
Then you can copy the settings into place with `bootstrap/populate.sh`

The passwords are in `bootstrap/private/.trace`

Alternatively, you can [do it yourself](do_it_yourself.md)

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

# Deploy LocalEGA using Docker

## Preliminaries

It is necessary to also create a `.env` file with the following variables:
(mostly used to parameterize the docker-compose file itself)

	COMPOSE_PROJECT_NAME=ega
	CODE=<python/code/folder>    # path to folder where setup.py is
	CONF=<path/to/your/ini/file> # will be mounted in the containers as /etc/ega/conf.ini

	SSL_CERT=<path/to/ssl.cert>  # for the ingestion workers to communicate with the keys server

Moreover, there are settings to include regarding the
encryption/decryption for the keys server.  We locate those variables
(in order to not make them available to all containers) in the
subfolder (to be created in not already exisiting) `.env.d/keys`:

```
KEYS=<path/to/keys.conf>
SSL_KEY=<path/to/ssl.key>
RSA_SEC=<path/to/rsa/sec.pem>
RSA_PUB=<path/to/rsa/pub.pem>
PGP_SEC=<path/to/pgp/sec.key>
PGP_PUB=<path/to/pgp/pub.key>
PGP_PASSPHRASE='something'
PGP_PASSPHRASE=<something-complex>
```

For the database, we create `.env.d/db` containing:

```
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<some-password>
```

## Running

	docker-compose up -d
	
You probably should [create the images](images) beforehand, with `make -C images`.

Use `docker-compose up -d --scale ingest=3` instead, if you want to
start 3 ingestion workers.

Note that, in this architecture, we use 3 separate volumes: one for
the inbox area, one for the staging area, and one for the vault. They
will be created on-the-fly by docker-compose.

## Stopping

	docker-compose down -v

## Status

	docker-compose ps

## Example

<a href="https://asciinema.org/a/nhHCuLd7mYjL4UgKQDI7uRJHs">
<img src="https://asciinema.org/a/nhHCuLd7mYjL4UgKQDI7uRJHs.png" width="836" style="display:block;margin:0 auto;"/>
</a>

	1) docker-compose up -d

We now create a "user" message in the broker. For that, we use the frontend and ega-publisher.

	2) docker-compose exec frontend ega-publisher inbox --broker 'cega.broker' --routing 'sweden.user' 'test' 'ssh-pub-key' 'some-hash'

We upload an encrypted file (here named data1)

	3) sftp -P 2222 test@localhost
	sftp> put <absolute/or/relative/path/to/file/named/data1>
	
Finally, we create a "file" message, again using the frontend.
	
	4) docker-compose exec frontend ega-publisher ingestion --broker 'cega.broker' --routing 'sweden.file' --enc "<bla>" --enc_algo 'md5' --unenc "<bla...>" --unenc_algo 'md5' test data1

Check now that the vault has the file and the message broker sent a message back in the CentralEGA queue, named `sweden.v1.commands.completed`.

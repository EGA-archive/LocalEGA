# Deploy LocalEGA using Docker

## Preliminaries

It is necessary to create a `.env` file with the following variables:
(mostly used to parameterize docker-compose)

```
COMPOSE_PROJECT_NAME=ega
COMPOSE_FILE=ega.yml

CODE=<python/code/folder>    # path to folder where setup.py is
CONF=<path/to/your/ini/file> # will be mounted in the containers as /etc/ega/conf.ini

# settings regarding the encryption/decryption
KEYS=<path/to/keys.conf>
SSL_CERT=<path/to/ssl.cert>  # for the ingestion workers to communicate with the keys server
SSL_KEY=<path/to/ssl.key>
RSA_SEC=<path/to/rsa/sec.pem>
RSA_PUB=<path/to/rsa/pub.pem>
GPG_HOME=<path/to/gpg/homedir> # including pubring.kbx, trustdb.gpg, private-keys-v1.d and openpgp-revocs.d
```

For the database, we create `.env.d/db` containing:

```
POSTGRES_USER=<some-user>
POSTGRES_PASSWORD=<some-password>
```

For the keyserver, we create `.env.d/gpg` containing:

```
GPG_PASSPHRASE=the-correct-passphrase
```

The file pointed by `KEYS` should contain the information about the
keys and will be located _only_ on the keyserver. For example:

```
[DEFAULT]
active_master_key = 1

[master.key.1]
seckey = /etc/ega/rsa/sec.pem
pubkey = /etc/ega/rsa/pub.pem
passphrase = <something-complex>

[master.key.2]
seckey = /etc/ega/rsa/sec2.pem
pubkey = /etc/ega/rsa/pub2.pem
passphrase = <something-complex-too>
```

Docker will map the path from `RSA_PUB` in the `.env` file to
`/etc/ega/rsa/pub.pem` in the keyserver container, for example.

The file pointed by `CONF` should contain the values that reset those
from [defaults.ini](../src/lega/conf/defaults.ini). For example:

```
[DEFAULT]
# We want more output
log_conf = debug

[ingestion]
gpg_cmd = /usr/local/bin/gpg --homedir ~/.gnupg --decrypt %(file)s

## Connecting to Central EGA
[cega.broker]
host = cega_mq
username = <some-user>
password = <some-password>
vhost = <some-vhost>
heartbeat = 0

[db]
host = ega_db
username = <same-as-POSTGRES_USER-above>
password = <same-as-POSTGRES_PASSWORD-above>
```

All the other values will remain unchanged.<br/>
Use `docker-compose exec <some-container> ega-conf --list` in any container (but inbox).

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

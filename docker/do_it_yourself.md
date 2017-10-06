## The environment variables

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

# Temporarily faking Central EGA
CEGA_USERS=<path/to/users/folder> # containing one .yml file per user
```

You may get started with some extra instructions to create
the [private data](bootstrap/README.md).

For the database, we create `.env.d/db` containing:

```
POSTGRES_USER=<some-user>
POSTGRES_PASSWORD=<some-password>
```

For the keyserver, we create `.env.d/gpg` containing:

```
GPG_PASSPHRASE=the-correct-passphrase
```
## The CONF file

The file pointed by `CONF` should contain the values that reset those
from [defaults.ini](../src/lega/conf/defaults.ini). For example:

```
[DEFAULT]
# We want more output
log = debug

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

## The KEYS file

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

## A Central EGA user

We fake the CentralEGA message broker and user database, with 2
containers: `cega_mq` and `cega_users`.

The `cega_users` is a very simple file-based server, that reads from
the folder pointed by `CEGA_USERS`. The latter contains one file per user, of the following form:

```
---
password_hash: $1$xyz$sx8gPI05DJdJe4MJx5oXo0
pubkey: ssh-rsa AAAAB3NzaC1yc...balbla...MiFw== some.comment@lega.sftp
expiration: some interval
```

The file name `john.yml` is used for the user `john`. You must at
least specify a `password_hash` or a `pubkey`. Other values can be
empty or missing.

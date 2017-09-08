# Deploy LocalEGA using Docker

## Preliminaries

It is necessary to also create a `.env` file with the following variables:
(mostly used to parameterize the docker-compose file itself)

	COMPOSE_PROJECT_NAME=ega
	CODE=<python/code/folder>    # path to folder where setup.py is
	CONF=<path/to/your/ini/file> # will be mounted in the containers as /etc/ega/conf.ini
	
	RSA_HOME=<folder>         # mapped to /root/.rsa on the ega-workers
	GPG_HOME=<folder>         # Used on the agent-forwarder and the workers


The folder referenced by `GPG_HOME` should contain the following:

| Components | Used for... |
|----------:|------------|
| `pubring.kbx` | Access to the public ring by the workers and the gpg-agent master |
| `trustdb.gpg` | idem |
| `openpgp-revocs.d/` | Revoking keys. Only on the gpg-agent master |
| `private-keys-v1.d/`| idem |
| `certs/selfsigned.{cert,key}` | ... ssl encryption of the traffic between the workers and the gpg-agent master |

These files are created in advance by GPG (version 2.1+).

Moreover, some of the containers need extra variables. There are located in:
* `.env.d/gpg` with
```
GPG_PASSPHRASE=<something-complex>
```
* `.env.d/db`
```
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<some-password>
```

## Running

	docker-compose up -d
	
If the images are not created, they will be. <br/>
However, it is advised to [create them](images) beforehand.

Use `docker-compose up -d --scale worker=3` instead, if you want to start 3 workers.

Note that, in this architecture, we use 3 separate volumes: one for
the inbox area, one for the staging area, and one for the vault. They
will be created on-the-fly by docker-compose.

## Stopping

	docker-compose down

## Status

	docker-compose ps

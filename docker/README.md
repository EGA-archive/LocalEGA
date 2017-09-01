# Deploy LocalEGA using Docker

## Preliminaries

It is necessary to first create a `.env` file with the following variables:
(mostly used to parameterize the docker-compose file itself)

	COMPOSE_PROJECT_NAME=ega
	CODE=<python/code/folder> # path where setup.py is
	CONF=<path/to/your/ini/file>
	
	INBOX=<folder>            # mapped to /home on the ega-inbox
	STAGING=<folder>          # mapped to /ega/staging on the ega-workers
	VAULT=<folder>            # mapped to /ega/vault on the ega-vault and ega-verify>
	
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

## Stopping

	docker-compose down

## Status

	docker-compose ps

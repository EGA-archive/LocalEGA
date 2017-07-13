# Deploy LocalEGA using Docker

## Preliminaries

It is necessary to first create a `.env` file with the following variables:
(mostly used to parameterize the docker-compose file itself)

	COMPOSE_PROJECT_NAME=ega
	CODE=..                   # where setup.py is
	CONF=<path/to/your/ini/file>
	
	INBOX=<folder>            # mapped to /home on the ega-inbox
	STAGING=<folder>          # mapped to /ega/staging on the ega-workers
	VAULT=<folder>            # mapped to /ega/vault on the ega-vault and ega-verify>
	
	RSA_HOME=<folder>         # mapped to /root/.rsa on the ega-workers
	GPG_HOME=<folder>         # Used on the agent-forwarder and the workers


The `GPG_HOME` folder should contain the following:
* `pubring.kbx`
* `trustdb.gpg`
* `openpgp-revocs.d/`
* `private-keys-v1.d/`
* `certs/selfsigned.{cert,key}`


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

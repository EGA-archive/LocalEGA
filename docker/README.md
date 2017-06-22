# Deploy LocalEGA using Docker

## Preliminaries

It is necessary to first create a `.env` file with the following variables:
(mostly used to parameterize the docker-compose file itself)

	COMPOSE_PROJECT_NAME=ega
	CODE=..                   # where setup.py is
	CONF=<your-conf.ini-file>
	INBOX=<folder>            # mapped to /home on the ega-inbox
	STAGING=<folder>          # mapped to /ega/staging on the ega-workers
	VAULT=<folder>            # mapped to /ega/vault on the ega-vault and ega-verify>
	RSA_HOME=<folder>         # mapped to /root/.rsa on the ega-workers
	GPG_HOME=<folder>         # mapped to /root/.gnupg on the ega-gpg-agent
	GPG_PUBRING=<gpg-pubring> # mapped to /root/.gnupg/pubring.kbx on the ega-gpg-agent and ega-workers
	SSH_PUB_KEY=<ssh-key.pub> # mapped to /root/.ssh/ega.pub
	SSH_PRIV_KEY=<ssh-key>    # mapped to /root/.ssh/ega


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

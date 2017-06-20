# Deploy LocalEGA using Docker

## Preliminaries

It is necessary to first create a `.env` file with the following variables:
(mostly used to parameterize the docker-compose file itself)

	COMPOSE_PROJECT_NAME=ega
	CODE=..
	CONF=<your-conf.ini-file>
	INBOX=<its-location>
	STAGING=<its-location>
	VAULT=<its-location>
	GNUPGHOME=<its-location>
	RSAHOME=<its-location>
	

Moreover, some of the containers need extra variables. There are located in:
* `details/gpg.env` with
```
GNUPGHOME=/root/.gnupg # resetting the global env
PASSPHRASE=<something-complex>
```
* details/db.env
```
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<some-password>
```
* details/inbox.env
```
SSH_KEY=<your-key-to-login-onto-the-sftp-server>
```

## Running

	docker-compose up -d
	
If the images are not created, they will be. It takes some time.

## Stopping

	docker-compose down

## (re)build the images

	docker-compose build

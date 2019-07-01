# NeIC Local EGA

This is a fork of https://github.com/EGA-archive/LocalEGA adapted for NeIC use case.

[![Build Status](https://travis-ci.org/neicnordic/LocalEGA.svg?branch=master)](https://travis-ci.org/neicnordic/LocalEGA)
[![Documentation Status](https://readthedocs.org/projects/localega/badge/?version=latest)](https://localega.readthedocs.io/en/latest/?badge=latest)
[![Coverage Status](https://coveralls.io/repos/github/neicnordic/LocalEGA/badge.svg?branch=master)](https://coveralls.io/github/neicnordic/LocalEGA?branch=master)

The [code](lega) is written in Python (3.6+).

You can provision and deploy the different components, locally, using [docker-compose](deploy).

Other provisioning methods are provided by our partners:

* on a [Kubernetes/OpenShift cluster](https://github.com/NBISweden/LocalEGA-helm), using `kubernetes`;
* on a [Docker Swarm cluster](https://github.com/NBISweden/LocalEGA-deploy-swarm), using `gradle` and `docker swarm`.

# Architecture

LocalEGA is divided into several components, as docker containers.

| Components  | Role |
|-------------|------|
| db          | A Postgres database with appropriate schemas and isolations |
| mq          | A (local) RabbitMQ message broker with appropriate accounts, exchanges, queues and bindings, connected to the CentralEGA counter-part. |
| inbox       | SFTP server, acting as a dropbox, where user credentials are fetched from CentralEGA |
| ingesters   | Split the Crypt4GH header and move the remainder to the storage backend. No cryptographic task, nor access to the decryption keys. |
| verifiers   | Decrypt the stored files and checksum them against their embedded checksum. |
| archive     | Storage backend: as a regular file system or as a S3 object store. |
| finalizers  | Handle the so-called _Stable ID_ filename mappings from CentralEGA. |

Find the [NeIC LocalEGA documentation](https://neic-localega.readthedocs.io) hosted on [ReadTheDocs.org](https://readthedocs.org/).

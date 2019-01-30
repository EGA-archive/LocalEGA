# Local EGA main repository

[![Build Status](https://travis-ci.org/EGA-archive/LocalEGA.svg?branch=dev)](https://travis-ci.org/EGA-archive/LocalEGA)
[![Documentation Status](https://readthedocs.org/projects/localega/badge/?version=latest)](https://localega.readthedocs.io/en/latest/?badge=latest)
[![Coverage Status](https://coveralls.io/repos/github/EGA-archive/LocalEGA/badge.svg?branch=master)](https://coveralls.io/github/EGA-archive/LocalEGA?branch=master)

The [code](lega) is written in Python (3.6+).

You can provision and deploy the different components, locally, using [docker-compose](deploy).

Other provisioning methods are provided by our partners:

* on an [OpenStack cluster](https://github.com/NBISweden/LocalEGA-deploy-terraform), using `terraform`;
* on a [Kubernetes/OpenShift cluster](https://github.com/NBISweden/LocalEGA-deploy-k8s), using `kubernetes`;
* on a [Docker Swarm cluster](https://github.com/NBISweden/LocalEGA-deploy-swarm), using `gradle`.

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
| outgesters  | Front-facing checks for download permissions. |
| streamers   | Fetch the files from the archive and re-encrypt its header for the given requester. |

Find the [LocalEGA documentation](http://localega.readthedocs.io) hosted on [ReadTheDocs.org](https://readthedocs.org/).

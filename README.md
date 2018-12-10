# NBIS repository for the Local EGA project

[![Codacy Badge](https://api.codacy.com/project/badge/Grade/3dd83b28ec2041889bfb13641da76c5b)](https://www.codacy.com/app/NBIS/LocalEGA?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=NBISweden/LocalEGA&amp;utm_campaign=Badge_Grade)
[![Build Status](https://travis-ci.org/NBISweden/LocalEGA.svg?branch=dev)](https://travis-ci.org/NBISweden/LocalEGA)
[![Coverage Status](https://coveralls.io/repos/github/NBISweden/LocalEGA/badge.svg?branch=dev)](https://coveralls.io/github/NBISweden/LocalEGA?branch=dev)

The [code](lega) is written in Python (3.6+).

You can provision and deploy the different components:

* locally, using [docker-compose](docker);
* on an OpenStack cluster, using [terraform](https://github.com/NBISweden/LocalEGA-deploy-terraform);
* on a Kubernetes/OpenShift cluster, using [kubernetes](https://github.com/NBISweden/LocalEGA-deploy-k8s);
* on a Docker Swarm cluster, using [Gradle](https://github.com/NBISweden/LocalEGA-deploy-swarm).

# Architecture

LocalEGA is divided into several components, whether as docker
containers or as virtual machines.

| Components  | Role |
|-------------|------|
| db          | A Postgres database with appropriate schema |
| mq          | A RabbitMQ message broker with appropriate accounts, exchanges, queues and bindings |
| inbox       | SFTP server, acting as a dropbox, where user credentials come from CentralEGA |
| keyserver   | Handles the encryption/decryption keys |
| ingesters   | Split the Crypt4GH header and move the remainder to the storage backend. No cryptographic task, nor connection to the keyserver. |
| verifiers   | Connect to the keyserver (via SSL) and decrypt the stored files and checksum them against their embedded checksum. |
| vault       | Storage backend: as a regular file system or as a S3 object store. |
| Finalize    | Handles the so-called _Stable ID_ filename mappings from CentralEGA. |

Find the [LocalEGA documentation](http://localega.readthedocs.io) hosted on [ReadTheDocs.org](https://readthedocs.org/).

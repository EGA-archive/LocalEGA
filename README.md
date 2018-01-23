# NBIS repository for the Local EGA project

[![Codacy Badge](https://api.codacy.com/project/badge/Grade/3dd83b28ec2041889bfb13641da76c5b)](https://www.codacy.com/app/NBIS/LocalEGA?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=NBISweden/LocalEGA&amp;utm_campaign=Badge_Grade)
[![Build Status](https://travis-ci.org/NBISweden/LocalEGA.svg?branch=dev)](https://travis-ci.org/NBISweden/LocalEGA)

The [code](lega) is written in Python (3.6+).

You can provision and deploy the different components:

* locally, using [docker-compose](deployments/docker).
* on an OpenStack cluster, using [terraform](deployments/terraform).

# Architecture

LocalEGA is divided into several components, whether as docker
containers or as virtual machines.

| Components | Role |
|------------|------|
| db         | A Postgres database with appropriate schema |
| mq         | A RabbitMQ message broker with appropriate accounts, exchanges, queues and bindings |
| inbox      | SFTP server, acting as a dropbox, where user credentials come from CentralEGA |
| keyserver  | Handles the encryption/decryption keys |
| workers    | Connect to the keys component (via SSL) and do the actual re-encryption work |
| vault      | Stores the files from the staging area to the vault. It includes a verification step afterwards. |


Find the [LocalEGA documentation](http://localega.readthedocs.io) hosted on [ReadTheDocs.org](https://readthedocs.org/).

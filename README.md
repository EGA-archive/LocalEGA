# Local EGA implementation _using Python_

This repo contains python code to start a _Local EGA_.

There are 3 main components: ingestion, worker, vault

The ingestion, worker and vault modules can be respectively started as "_agents_" with:
* `python -m lega.ingestion --conf <file> --log <file>`
* `python -m lega.worker --conf <file> --log <file>`
* `python -m lega.vault --conf <file> --log <file>`

Several worker and vault _agents_ can be started.

The ingestion _agent_ start an asyncio web-server.

## Configuration

The `--conf <file>` allows the user to override the configuration settings.
The settings are loaded, in order:
* from the package's `defaults.ini`
* from `~/.lega/conf.ini`
* and finally from the file specified as the `--conf` argument.

## Logging

The `--log <file>` argument is used to configuration where the logs go.
Without it, there is no logging capabilities.
The `<file>` can be in `INI` or `YAML` format.

## Prior to running the Local EGA components

It is necessary to have the following, already running:
* a gpg-agent (with the `--homedir` properly set)
* a message broker, and
* a postgres database


The following scripts are suggestions to start the above components.

For the **database**, we can use a docker container and boot it with:

        #!/usr/bin/env bash

        CONTAINER=ega-db
        POSTGRES_USER=postgres
        POSTGRES_PASSWORD=mysecretpassword

        # Kill the previous container
        docker kill ${CONTAINER} || true #&& docker rm  ${CONTAINER}

        # Starting RabbitMQ with docker
        docker run -it --rm -d --hostname localhost -p 5432:5432 --name ${CONTAINER} postgres
        # The image includes EXPOSE 5432

For the **message broker**, we can use a docker container booting RabbitMQ (with the management plugin)

        #!/usr/bin/env bash

        CONTAINER=ingestion-mq
        DOCKER_EXEC="docker exec -it ${CONTAINER}"

        # Kill the previous container
        docker kill ${CONTAINER} || true #&& docker rm  ${CONTAINER}

        # Starting RabbitMQ with docker
        docker run -it --rm -d --hostname localhost -p 4369:4369 -p 5671:5671 -p 5672:5672 -p 15671:15671 -p 15672:15672 -p 25672:25672 --name ${CONTAINER} rabbitmq:management

        echo "Waiting 10 seconds for the container to start"
        sleep 10

        # Updating it
        ${DOCKER_EXEC} rabbitmqctl set_disk_free_limit 1GB

        # Create the exchange
        curl -i -u guest:guest -H "content-type:application/json" -X PUT -d '{"type":"topic","durable":true}' http://localhost:15672/api/exchanges/%2f/lega

        # Create the queues
        curl -i -u guest:guest -H "content-type:application/json" -X PUT -d '{"durable":true}' http://localhost:15672/api/queues/%2f/tasks
        curl -i -u guest:guest -H "content-type:application/json" -X PUT -d '{"durable":true}' http://localhost:15672/api/queues/%2f/completed
        curl -i -u guest:guest -H "content-type:application/json" -X PUT -d '{"durable":true}' http://localhost:15672/api/queues/%2f/errors
        #curl -i -u guest:guest -H "content-type:application/json" -X PUT -d '{"durable":true}' http://localhost:15672/api/queues/%2f/vault_errors

        # Binding them to the amq.topic exchange
        curl -i -u guest:guest -H "content-type:application/json" -X POST -d '{"routing_key":"lega.task.todo"}' http://localhost:15672/api/bindings/%2f/e/lega/q/tasks
        curl -i -u guest:guest -H "content-type:application/json" -X POST -d '{"routing_key":"lega.task.complete"}' http://localhost:15672/api/bindings/%2f/e/lega/q/completed
        curl -i -u guest:guest -H "content-type:application/json" -X POST -d '{"routing_key":"lega.errors"}' http://localhost:15672/api/bindings/%2f/e/lega/q/errors
        #curl -i -u guest:guest -H "content-type:application/json" -X POST -d '{"routing_key":"vault_errors"}' http://localhost:15672/api/bindings/%2f/e/amq.topic/q/vault_errors


The above curl calls simply set up the 3 queues, the exchange and the bindings.

Finally, the **gpg-agent** can be started ahead of time as follows:

        export GNUPGHOME=<LEGA_HOME>/private/gpg
        gpg-agent --daemon --homedir $GNUPGHOME
        gpg-preset-passphrase -P <PASSPHRASE> --preset <KEYGRIP>

The `KEYGRIP` is the fingerprint of the secret gpg key, and the `PASSPHRASE` is its associated ...hm...passphrase.
This only matters for the worker agents.
Note: make `GNUPGHOME` points to the right folder (the one containing the public and secret rings)

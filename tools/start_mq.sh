#!/usr/bin/env bash

CONTAINER=ega-mq
HERE="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
DOCKER_EXEC="docker exec -it ${CONTAINER}"

# Kill the previous container
docker kill ${CONTAINER} || true #&& docker rm  ${CONTAINER}

# Starting RabbitMQ with docker
docker run -it $* -d \
       --hostname localhost \
       -p 4369:4369 -p 5671:5671 -p 5672:5672 -p 15671:15671 -p 15672:15672 -p 25672:25672 \
       --name ${CONTAINER} \
       rabbitmq:management

       # -v $HERE/rabbitmq.config:/etc/rabbitmq/rabbitmq.config \
       # -v $HERE/rabbitmq.json:/etc/rabbitmq/defs.json \

sleep 6

#curl $PARAMS -X PUT -d "$(cat $HERE/rabbitmq.json)" http://localhost:15672/api/definitions

${DOCKER_EXEC} rabbitmqctl set_disk_free_limit 1GB

PARAMS='-i -u guest:guest -H "content-type:application/json"'

# Create the exchange, the queues and the bindings
curl $PARAMS -X PUT -d '{"type":"topic","durable":true}' http://localhost:15672/api/exchanges/%2f/lega
curl $PARAMS -X PUT -d '{"durable":true}' http://localhost:15672/api/queues/%2f/completed
curl $PARAMS -X PUT -d '{"durable":true}' http://localhost:15672/api/queues/%2f/archived
curl $PARAMS -X PUT -d '{"durable":true}' http://localhost:15672/api/queues/%2f/tasks
curl $PARAMS -X PUT -d '{"durable":true}' http://localhost:15672/api/queues/%2f/verified
curl $PARAMS -X PUT -d '{"durable":true}' http://localhost:15672/api/queues/%2f/users
curl $PARAMS -X POST -d '{"routing_key":"lega.tasks"}' http://localhost:15672/api/bindings/%2f/e/lega/q/tasks
curl $PARAMS -X POST -d '{"routing_key":"lega.complete"}' http://localhost:15672/api/bindings/%2f/e/lega/q/completed
curl $PARAMS -X POST -d '{"routing_key":"lega.archived"}' http://localhost:15672/api/bindings/%2f/e/lega/q/archived
curl $PARAMS -X POST -d '{"routing_key":"lega.verified"}' http://localhost:15672/api/bindings/%2f/e/lega/q/verified
curl $PARAMS -X POST -d '{"routing_key":"lega.users"}' http://localhost:15672/api/bindings/%2f/e/lega/q/users


${DOCKER_EXEC} rabbitmqctl add_user test dNAf3r9245XS
${DOCKER_EXEC} rabbitmqctl set_user_tags test administrator
${DOCKER_EXEC} rabbitmqctl add_vhost test
${DOCKER_EXEC} rabbitmqctl set_permissions -p / test ".*" ".*" ".*"
${DOCKER_EXEC} rabbitmqctl set_permissions -p test test ".*" ".*" ".*"
${DOCKER_EXEC} rabbitmqctl set_permissions -p / guest ".*" ".*" ".*"
${DOCKER_EXEC} rabbitmqctl set_permissions -p test guest ".*" ".*" ".*"

CRG_PARAMS='-i -u test:dNAf3r9245XS -H "content-type:application/json"'
curl $CRG_PARAMS -X PUT -d '{"durable":true}' http://localhost:15672/api/queues/test/sweden.v1.commands.file
curl $CRG_PARAMS -X PUT -d '{"durable":true}' http://localhost:15672/api/queues/test/sweden.v1.commands.completed
curl $CRG_PARAMS -X PUT -d '{"durable":true}' http://localhost:15672/api/queues/test/sweden.v1.commands.user
curl $CRG_PARAMS -X PUT -d '{"type":"topic","durable":true}' http://localhost:15672/api/exchanges/test/localega.v1
curl $CRG_PARAMS -X POST -d '{"routing_key":"sweden.file"}' http://localhost:15672/api/bindings/test/e/localega.v1/q/sweden.v1.commands.file
curl $CRG_PARAMS -X POST -d '{"routing_key":"sweden.user"}' http://localhost:15672/api/bindings/test/e/localega.v1/q/sweden.v1.commands.user
curl $CRG_PARAMS -X POST -d '{"routing_key":"sweden.file.completed"}' http://localhost:15672/api/bindings/test/e/localega.v1/q/sweden.v1.commands.completed


#!/usr/bin/env bash
set -e

echomsg "Generating fake Eureka server"

# Copy the Eureka server in an accessible place
if [[ -f /tmp/eureka.jar ]]; then
    # Running in a container
    cp /tmp/eureka.jar ${PRIVATE}/eureka.jar
else
    # Running on host, outside a container
    cp ${EXTRAS}/eureka/target/eureka-server.jar ${PRIVATE}/eureka.jar
fi

cat > ${PRIVATE}/eureka.yml <<EOF
version: '3.2'

networks:
    # user overlay in swarm mode
    # default is bridge
  eureka:
    driver: bridge

services:

  ############################################
  # Faking Eureka server
  ############################################
  eureka:
    hostname: eureka
    ports:
      - "8761:8761"
    image: openjdk:8-jre-slim
    container_name: eureka
    volumes:
       - ./eureka.jar:/eureka.jar
    restart: on-failure:3
    networks:
      - eureka
    entrypoint: ["/docker-java-home/bin/java","-jar","/eureka.jar"]
EOF

# For the compose file
echo -n "private/eureka.yml" >> ${DOT_ENV} # no newline

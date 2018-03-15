#!/usr/bin/env bash
set -e

echomsg "Generating fake Eureka server"

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
    image: nbisweden/ega-base
    container_name: eureka
    volumes:
      - ../images/eureka/server.py:/eureka/server.py
    restart: on-failure:3
    networks:
      - eureka
    command: ["python3.6", "/eureka/server.py"]
EOF

# For the compose file
echo -n "private/eureka.yml" >> ${DOT_ENV} # no newline

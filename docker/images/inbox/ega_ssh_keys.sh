#!/bin/bash

eid=${1%%@*} # strip what's after the @ symbol

query="SELECT pubkey from users where elixir_id = '${eid}' LIMIT 1"

PGPASSWORD=${POSTGRES_PASSWORD} psql -tqA -U postgres -h ega-db -d lega -c "${query}"

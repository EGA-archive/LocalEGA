#!/usr/bin/env bash

set -e

function usage {
    echo "Usage: $0 [--help|-h] [--as-ega] <file> [host] [port]"
    echo ""
    echo "Convert the <file> (in JSON format) into base64 and POSTs it to the ingestion endpoint"
    echo ""
    echo -e "--as-ega\tFake authenticate (using a header) as Central EGA"
}

AS_EGA='X-CentralEGA: no'
ENDPOINT=ingest

while [ $# -gt 0 ]; do
    case "$1" in
        --help|-h) usage; exit 0;;
	--as-ega) AS_EGA='X-CentralEGA: yes';;
	--endpoint|-e) ENDPOINT=$2; shift;;
        *)
	    DATA=$(cat $1 | base64)
	    HOST=${2-localhost}
	    PORT=${3-8888}
	    break;;
    esac
    shift
done

curl -H "$AS_EGA" -X POST -d "$DATA" http://${HOST}:${PORT}/$ENDPOINT

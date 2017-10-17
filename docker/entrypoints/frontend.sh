#!/bin/bash

set -e

pip3.6 install /root/ega

echo "Starting the frontend"
exec ega-frontend

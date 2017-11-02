#!/bin/bash

set -e

cp -r /root/ega /root/run
pip3.6 install /root/run

echo "Starting the frontend"
exec ega-frontend

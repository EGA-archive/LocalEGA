#!/bin/bash

set -e

sleep 6
pip install -e /root/ega
exec ega-worker

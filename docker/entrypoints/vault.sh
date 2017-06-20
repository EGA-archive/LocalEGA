#!/bin/bash

set -e

pip install -e /root/ega

sleep 6

exec ega-vault

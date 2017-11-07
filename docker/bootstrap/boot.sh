#!/usr/bin/env bash
set -e

SCRIPT=$(dirname ${BASH_SOURCE[0]})
HERE=$PWD/${SCRIPT#./}

$HERE/cega.sh -f
$HERE/generate.sh -f -- swe1
$HERE/generate.sh -f -- fin1

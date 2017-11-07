#!/usr/bin/env bash
set -e

SCRIPT=$(dirname ${BASH_SOURCE[0]})
HERE=$PWD/${SCRIPT#./}

$HERE/cega.sh -q -f
$HERE/generate.sh -q -f -- swe1
$HERE/generate.sh -q -f -- fin1

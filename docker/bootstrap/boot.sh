#!/usr/bin/env bash
set -e

SCRIPT=$(dirname ${BASH_SOURCE[0]})
HERE=$PWD/${SCRIPT#./}

$HERE/cega.sh $@
$HERE/generate.sh $@ -- swe1
$HERE/generate.sh $@ -- fin1

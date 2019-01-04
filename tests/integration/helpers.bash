#!/usr/bin/env bash

[ ${BASH_VERSINFO[0]} -lt 4 ] && echo 'Bash 4 (or higher) is required' 1>&2 && exit 1

HERE=$(dirname ${BASH_SOURCE[0]})
MAIN_REPO=${HERE}/../..

DEBUG_LOG=${HERE}/output.debug
rm -rf ${DEBUG_LOG}

function echo_output {
    [[ -z "$output" ]] || echo -e "********** $1\n$output" >> $DEBUG_LOG
}

function echo_status {
    echo -e "********** $1\nstatus: $status" >> $DEBUG_LOG
}


#!/bin/bash

set -e

for mnt in $1/*
do
    { umount ${mnt} &>/dev/null && rmdir ${mnt}; } || :
done

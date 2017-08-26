#!/bin/bash

# This script will kill java processes which've been running longer than 5 minutes
PIDS="`ps eaxo etimes,pid,comm | grep "java" | awk '{print $2}'`"

# Kill the parent processes also
for i in ${PIDS}; do { TIME=`ps o etimes -p $i | egrep "[0-9]+" | awk '{print $1}'`; if [ "$TIME" -gt "299" ]; then kill -9 `ps -o ppid= $i | awk '{print $1}'`; kill -9 $i; fi;}; done;

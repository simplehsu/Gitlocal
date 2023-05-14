#!/usr/bin/env bash

NOW=$(date +"%F-%H-%M-%S")

set +e

# run yubihsm-connector in deamon and cat log
((sudo yubihsm-connector -d 2>&1 | tee log/yubihsm_connector/log-$NOW-yubihsm_connector.log) > /dev/null &)

set -e
exec $@

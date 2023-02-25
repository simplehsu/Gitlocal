#!/usr/bin/env bash

WORK_DIR=ca-18952383
SCRIPT=/home/mt/cert_signer/ca_18952383/DeviceCertificateProvisioner383
YUBIHSM2_CONF_DIR=/home/mt/mt/src/embedded/hsm-$YUBIHSM2_KEY-config

# LOG PATH
LOG_PATH_PROVISION=/home/mt/mt/src/embedded/$WORK_DIR/log/provision
NOW=$(date +"%F-%H-%M-%S")

set -e

(sudo $SCRIPT \
 2>&1) | tee $LOG_PATH_PROVISION/log-$WORK_DIR-$NOW-provision.log

set +e


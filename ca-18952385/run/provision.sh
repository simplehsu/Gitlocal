#!/usr/bin/env bash
HSM_SERIAL=385
UART=/dev/ttyUSB0
#UART=/dev/ttyACM0
BAUDRATE=115200

WORK_DIR=ca-18952385
SCRIPT=/home/mt/cert_signer/ca_18952385/18952385_Provisioner
YUBIHSM2_CONF_DIR=/home/mt/mt/src/embedded/hsm-$YUBIHSM2_KEY-config

# LOG PATH
LOG_PATH_PROVISION=/home/mt/mt/src/embedded/$WORK_DIR/log/provision
NOW=$(date +"%F-%H-%M-%S")

set -e

(sudo $SCRIPT --hsm_serial=$HSM_SERIAL \
--baud=$BAUDRATE \
--com_port="$UART" \
--connector_url="http://127.0.0.1:12345" \
 2>&1) | tee $LOG_PATH_PROVISION/log-$WORK_DIR-$NOW-provision.log

set +e


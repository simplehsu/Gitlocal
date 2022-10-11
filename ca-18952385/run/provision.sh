#!/usr/bin/env bash

YUBIHSM2_KEY=18952385
CA_COMMON_NAME='Motive Firefly CA 18 952 385'
CA_KEY_ID=0xf8d5
AUDIT_KEY_ID=0x2dda
AUDIT_KEY_PASSWORD=uL80a8EafQDQ4yFYtcviGrNJ2
UART=/dev/ttyACM0

WORK_DIR=ca-18952385
SCRIPT=/Scripts/AGCertificateProvisioner/AGCertificateProvisioner.py
YUBIHSM2_CONF_DIR=/home/mt/mt/src/embedded/hsm-$YUBIHSM2_KEY-config

# LOG PATH
LOG_PATH_PROVISION=/home/mt/mt/src/embedded/$WORK_DIR/log/provision
NOW=$(date +"%F-%H-%M-%S")

set -e

printf "YUBIHSM2 Provision\n"

(sudo python $SCRIPT --com_port $UART --baud 115200 \
--ca_key_id="$CA_KEY_ID" \
--ca_common_name="$CA_COMMON_NAME" \
--ca_data_directory="$YUBIHSM2_CONF_DIR/ca" \
--audit_key_id="$AUDIT_KEY_ID" \
--audit_data_directory="$YUBIHSM2_CONF_DIR/audit" \
--openssl_conf="$YUBIHSM2_CONF_DIR/etc/tls-ca.conf" \
--connector_url="http://127.0.0.1:12345/api" \
--device_data_directory="$YUBIHSM2_CONF_DIR/device" \
--audit_key_password="$AUDIT_KEY_PASSWORD" \
--linux=1 2>&1) | tee $LOG_PATH_PROVISION/log-ca-18952385-$NOW-provision.log

set +e


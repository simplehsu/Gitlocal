# Must-Know

| Item                 | PC S/N:BTTN21000QN3 | PC S/N: BTTN21000Q35 |
| -------------------- | ------------------- | -------------------- |
| YubiHSM2 KEY ID      | 18952101            | 18952102             |
| User Name/Password   | mt/42971007         | mt/42971007          |
| CA ID                | ca-18952101         | ca-18952102          |

# Hardware Setup

```text
PC <-- UART(/dev/ttyACMx or /dev/ttyUSBx) --> AG31
```

* To change UART port in the script

If we need to change the UART port setting, we change line 8 from `<CA ID>/run/provision.sh`

```text
8 UART=/dev/ttyACM0   # It can be /dev/ttyACMx or /dev/ttyUSBx
```

# Provisioning

```text
# If it is first time to run, it takes ~10 minutes
$ ./run.sh provision ca-<YubiHSM2>
```

For example:

Input:

```bash
$ ./run.sh provision ca-18952102
```

Output:

```text
Running provision for ca-18952102
Running with interactive console
+ set +xe
+ tee log/yubihsm_connector/log-2022-09-16-18-45-58-yubihsm_connector.log
+ sudo yubihsm-connector -d
YUBIHSM2 Provision
engine "pkcs11" set.
Signature ok
subject=CN = A14-M3F-QUC
Getting CA Private Key
{
  "PROVISION": {
    "CMD": "PRINT_CERT_SERIAL",
      "MSG": {
        "IDENTIFIER": "A14-M3F-QUC",
        "CERT_SERIAL": "20b82ab3197ab7df8534d01ce18343b1438362c5"
      },
      "RESULT": "PASS",
      "ERRNO": "0"
  }
}
SUCCESS: Script finished successfully in Docker container.
```

When the command was be run, log-ca-18952102-yy-mm-dd-hour-minute-second-provision.log is created by the command.

```text
mt@SN-0Q35:~/workspace/provision_docker$ cat ca-18952102/log/provision/log-ca-18952102-2022-09-16-18-45-58-provision.log
engine "pkcs11" set.
Signature ok
subject=CN = A14-M3F-QUC
Getting CA Private Key
{
      "PROVISION": {
        "CMD": "PRINT_CERT_SERIAL",
        "MSG": {
          "IDENTIFIER": "A14-M3F-QUC",
          "CERT_SERIAL": "20b82ab3197ab7df8534d01ce18343b1438362c5"
        },
        "RESULT": "PASS",
        "ERRNO": "0"
      }
}

```

# Update Provision Docker

provision_docker-<VERSION>.zip is used to update the docker. The have 2 steps for update

```text
#1 To copy provision_docker-<VERSION>.zip to provision_docker/release/
#2 ./run.sh bash <CA ID>            # <CA ID> will be ca-18952101 or ca-18952102
#3 ./run/update.sh <VERSION>        # <VERSION> will be v1001, v1002, etc...
```

# Trouble Shooting

## CASE 1: Provision Failure

When the message outputs, we can do `./run.sh provision <CA ID>` again

```text
Running provision for ca-18952101
Running with interactive console
+ tee log/yubihsm_connector/log-2022-09-16-19-13-30-yubihsm_connector.log
+ sudo yubihsm-connector -d
+ set +xe
YUBIHSM2 Provision
{
      "PROVISION_CERTS": {
        "CMD": "RD_CSN",
          "MSG": {
            "ERR": "JSON decode error Expecting value: line 1 column 1 (char 0), data was Command not recognized. Enter 'HELP' to view list of available commands\r\n"
          },
          "RESULT": "FAIL",
          "ERRNO": 22
      }
}
SUCCESS: Script finished successfully in Docker container.

```

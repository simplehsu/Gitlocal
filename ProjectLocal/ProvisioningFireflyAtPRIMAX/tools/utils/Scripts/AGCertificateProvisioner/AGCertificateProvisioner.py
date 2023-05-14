# Copyright 2022 Motive Technologies, Inc.
# All rights reserved
import argparse
import datetime
import errno
import json
import os
import re
import secrets
import subprocess
import sys
from json import JSONDecodeError
from json.encoder import JSONEncoder
from pathlib import Path
import cryptography.x509
import serial
import yubihsm.exceptions
from serial import Serial
from yubihsm import YubiHsm
from yubihsm.core import LogData
from yubihsm.core import AuthSession
from yubihsm.exceptions import YubiHsmDeviceError


# Helper function to print a result.
def print_result(
    cmd: str, msg_key: str, msg_val: str, pass_fail: str, error_number: int
) -> None:
    result = JSONEncoder(indent=4).encode(
        {
            "PROVISION_CERTS": {
                "CMD": cmd,
                "MSG": {msg_key: msg_val},
                "RESULT": pass_fail,
                "ERRNO": error_number,
            }
        }
    )
    print(result)


class CertificateProvisioner:
    """Class to manage provisioning an AG with its TLS client auth certificates"""

    serial_port: Serial = None
    hsm: YubiHsm = None

    # AG CLI commands
    CRYPTO_CLI_MODULE_NAME = "CRYPTO"
    CMD_GEN_KEYS = "KEYS"
    CMD_GEN_CSR = "CSR"
    CMD_STORE_CERT = "CERT"
    CMD_PRINTSERIAL = "PRINTSERIAL"
    SN_CLI_MODULE_NAME = "SN"
    CMD_GET_IDENTIFIER = "RD_CSN"

    # General data
    CA_EXT_FILE: Path = Path("client_ext")
    VERSION = 2002

    # AG-specific data
    identifier: str = ""
    cert_serial: str = ""
    cert_serial_actual: str = ""
    csr_path: Path = None
    device_cert_path: Path = None

    # Timeouts in seconds
    DEFAULT_RD_TIMEOUT = 1

    def __init__(
        self,
        com_port,
        ca_cn: str,
        baud: int,
        ca_key_id: int,
        audit_key_id: int,
        audit_key_password: str,
        audit_data_dir: str,
        ca_data_dir: str,
        device_data_dir: str,
        connector_url: str,
        openssl_conf: str,
        debug: int,
        linux: int,
    ):
        ca_data_directory: Path = Path(os.path.expandvars(ca_data_dir))
        if not ca_data_directory.is_dir():
            print_result(
                "INIT",
                "ERR",
                f"Directory {ca_data_directory} does not exist.",
                "FAIL",
                errno.ENOENT,
            )
            sys.exit(errno.ENOENT)
        self.device_data_directory: Path = Path(os.path.expandvars(device_data_dir))
        if not self.device_data_directory.is_dir():
            print_result(
                "INIT",
                "ERR",
                f"Directory {self.device_data_directory} does not exist.",
                "FAIL",
                errno.ENOENT,
            )
            sys.exit(errno.ENOENT)
        audit_data_directory: Path = Path(os.path.expandvars(audit_data_dir))
        if not audit_data_directory.is_dir():
            print_result(
                "INIT",
                "ERR",
                f"Directory {audit_data_directory} does not exist.",
                "FAIL",
                errno.ENOENT,
            )
            sys.exit(errno.ENOENT)
        self.openssl_conf_path: Path = Path(os.path.expandvars(openssl_conf))
        if not self.openssl_conf_path.is_file():
            print_result(
                "INIT",
                "ERR",
                f"File {self.openssl_conf_path} does not exist.",
                "FAIL",
                errno.ENOENT,
            )
            sys.exit(errno.ENOENT)
        self.com_port = com_port
        self.baud = baud
        self.ca_ext_path: Path = ca_data_directory / self.CA_EXT_FILE
        self.ca_key_id = ca_key_id
        self.audit_key_id = audit_key_id
        self.audit_key_password = audit_key_password
        self.audit_data_name = Path(str(datetime.date.today()) + ".json")
        self.audit_data_path = audit_data_directory / self.audit_data_name
        self.ca_cert_name: Path = Path(ca_cn + ".crt")
        self.ca_srl_name: Path = Path(ca_cn + ".srl")
        self.ca_cert_path = ca_data_directory / self.ca_cert_name
        self.ca_srl_path: Path = ca_data_directory / self.ca_srl_name
        self.debug = debug
        self.linux = linux
        try:
            with open(self.ca_cert_path, "rb") as ca_cert_fd:
                ca_cert_data = cryptography.x509.load_pem_x509_certificate(
                    ca_cert_fd.read()
                )
                for attribute in ca_cert_data.subject:
                    if attribute.oid.dotted_string == "2.5.4.3":
                        self.CA_CN = attribute.value
                if ca_cn != self.CA_CN:
                    print_result(
                        "READ_CA_CERT",
                        "ERR",
                        "CA Cert Common Name did not match file name "
                        + ca_cn
                        + " vs "
                        + self.CA_CN,
                        "FAIL",
                        errno.EINVAL,
                    )
                    sys.exit(errno.EINVAL)
        except OSError as CaCertErr:
            print_result(
                "OPEN_CA_CERT",
                "ERR",
                f"Failed to open CA certificate at {self.ca_cert_path} for reading",
                "FAIL",
                CaCertErr.errno,
            )
            sys.exit(CaCertErr.errno)
        self.hsm = YubiHsm.connect(connector_url)
        hsm_serial: int = self.hsm.get_device_info().serial
        if "AG CA" in self.CA_CN:
            ca_cn_num: str = self.CA_CN[self.CA_CN.index("AG CA ") + len("AG CA ") :]
        elif "Motive Firefly CA" in self.CA_CN:
            ca_cn_num: str = self.CA_CN[
                self.CA_CN.index("Motive Firefly CA ") + len("Motive Firefly CA ") :
            ]
        else:
            sys.exit("Can not find CA CN number")
        if str(hsm_serial) != ca_cn_num.replace(" ", ""):
            print_result(
                "GET_HSM_SERIAL",
                "ERR",
                "CA CN Number did not match HSM Serial",
                "FAIL",
                errno.EINVAL,
            )
            sys.exit(errno.EINVAL)

    def __del__(self):
        if self.serial_port:
            if self.serial_port.isOpen():
                self.flush_serial()
                try:
                    self.serial_port.close()
                except TypeError:
                    pass
        if self.hsm:
            self.hsm.close()

    def flush_serial(self):
        if self.serial_port:
            try:
                self.serial_port.flushInput()
            except TypeError:
                pass
            try:
                self.serial_port.flushOutput()
            except TypeError:
                pass

    def connect_to_ag(self):
        try:
            self.serial_port = serial.Serial(
                port=self.com_port, baudrate=self.baud, timeout=self.DEFAULT_RD_TIMEOUT
            )
        except ValueError as serialError:
            print_result(
                "OPEN_SERIAL_PORT",
                "ERR",
                f"Invalid parameter, {serialError}",
                "FAIL",
                errno.EINVAL,
            )
            sys.exit(errno.EINVAL)
        except serial.SerialException as serialError:
            print_result(
                "OPEN_SERIAL_PORT",
                "ERR",
                f"Could not configure port, {serialError}",
                "FAIL",
                errno.ENOENT,
            )
            sys.exit(errno.ENOENT)
        # Clear the serial port input
        self.flush_serial()

    def send_cmd(self, cmd: str) -> None:
        """Send a CLI command to AG"""
        self.flush_serial()
        cmd = cmd + "\n"  # Add LF to complete command
        for wdata in cmd:  # read byte from string
            wdata = wdata.encode("charmap")  # encode byte
            self.serial_port.write(wdata)  # send byte
            rdata = self.serial_port.read(1)  # read the echoed byte
            if rdata != wdata:  # AG should have echoed the same byte back
                print_result(
                    "SERIAL",
                    "TIMEOUT",
                    f"AG failed to echo byte in {self.serial_port.timeout}s",
                    "FAIL",
                    errno.ETIMEDOUT,
                )
                sys.exit(errno.EINVAL)
        self.serial_port.readline()  # Read the new line printed on ending the command

    def read_response(self, timeout: int, command: str) -> object:
        """Read a response from an AG"""
        output: str = ""
        self.serial_port.timeout = timeout
        line = self.serial_port.readline()

        while True:
            if len(line) == 1 and line == b"$":  # Previous line was end of response
                try:
                    return json.loads(output)
                except JSONDecodeError as jsonError:
                    print_result(
                        command,
                        "ERR",
                        f"JSON decode error {jsonError}, data was {output}",
                        "FAIL",
                        errno.EINVAL,
                    )
                    sys.exit(errno.EINVAL)
            elif not line:
                # timeout error
                print_result(
                    command,
                    "TIMEOUT",
                    f"Failed to read line from AG in {self.serial_port.timeout}s",
                    "FAIL",
                    errno.ETIMEDOUT,
                )
                sys.exit(errno.ETIMEDOUT)
            else:
                # Got a line
                output += line.decode("charmap")
                line = self.serial_port.readline()

    def get_device_identifier(self):
        if self.serial_port:
            self.flush_serial()
            self.send_cmd(self.SN_CLI_MODULE_NAME + " " + self.CMD_GET_IDENTIFIER)
            resp = self.read_response(1, self.CMD_GET_IDENTIFIER)
            if isinstance(resp, dict):
                # Valid response, parsed json
                if resp["SN"]["RESULT"] == "PASS":
                    self.identifier = resp["SN"]["MSG"]["INFO"]
                    self.csr_path: Path = self.device_data_directory / Path(
                        str(self.identifier) + ".csr"
                    )
                    self.device_cert_path: Path = self.device_data_directory / Path(
                        str(self.identifier) + ".crt"
                    )
                    if self.debug == 1:
                        print("Got SN " + str(self.identifier) + " from device")
                else:
                    print_result(
                        "GET_DEVICE_IDENTIFIER",
                        "ERR",
                        "Unexpected Response Format",
                        "FAIL",
                        errno.EINVAL,
                    )
                    sys.exit(errno.EINVAL)
            else:
                print_result(
                    "GET_DEVICE_IDENTIFIER",
                    "ERR",
                    "Response wasn't a JSON dict",
                    "FAIL",
                    errno.EINVAL,
                )
                sys.exit(errno.EINVAL)
        else:
            print_result(
                "GET_DEVICE_IDENTIFIER",
                "ERR",
                "Not connected to AG",
                "FAIL",
                errno.ENOENT,
            )
            sys.exit(errno.ENOENT)

    def gen_keys(self):
        if self.serial_port:
            self.send_cmd(self.CRYPTO_CLI_MODULE_NAME + " " + self.CMD_GEN_KEYS)
            resp = self.read_response(1, self.CMD_GEN_KEYS)
            if isinstance(resp, dict):
                # Valid response, parsed JSON
                if resp["CRYPTO"]["RESULT"] != "PASS":
                    print_result(
                        "GENERATE_KEYS", "ERR", f"{resp}", "FAIL", errno.EINVAL
                    )
                    sys.exit(errno.EINVAL)
                else:
                    if self.debug == 1:
                        print("Got Keys from AG")
            else:
                print_result(
                    "GENERATE_KEYS",
                    "ERR",
                    "Response wasn't a JSON dict",
                    "FAIL",
                    errno.EINVAL,
                )
                sys.exit(errno.EINVAL)
        else:
            print_result(
                "GENERATE_KEYS", "ERR", "Not connected to AG", "FAIL", errno.ENOENT
            )
            sys.exit(errno.ENOENT)

    def get_csr(self):
        if self.serial_port:
            self.send_cmd(self.CRYPTO_CLI_MODULE_NAME + " " + self.CMD_GEN_CSR)
            resp = self.read_response(1, self.CMD_GEN_CSR)
            if isinstance(resp, dict):
                # Valid response, parsed json
                if resp["CRYPTO"]["RESULT"] == "PASS":
                    # It worked
                    if self.debug == 1:
                        print("Generate CSR worked")
                    try:
                        with open(self.csr_path, "w") as device_csr_file:
                            device_csr_file.write(resp["CRYPTO"]["MSG"]["PEM"])
                        if self.debug == 1:
                            print("Writing CSR to file worked")
                    except OSError as e:
                        print_result(
                            "GET_CSR",
                            "ERR",
                            f"Failed to open file: {e}",
                            "FAIL",
                            e.errno,
                        )
                        sys.exit(e.errno)
                else:
                    print_result(
                        "GET_CSR",
                        "ERR",
                        f"Response failed: {resp}",
                        "FAIL",
                        resp["CRYPTO"]["ERRNO"],
                    )
                    sys.exit(resp["CRYPTO"]["ERRNO"])
            else:
                print_result(
                    "GET_CSR",
                    "ERR",
                    "Response wasn't a JSON dict",
                    "FAIL",
                    errno.EINVAL,
                )
                sys.exit(errno.EINVAL)

    def generate_certificate_serial(self):
        try:
            with open(self.ca_srl_path, "w") as srl_file:
                self.cert_serial = "20" + secrets.token_hex(19)
                srl_file.write(self.cert_serial + "\n")
                if self.debug == 1:
                    print("Generate Certificate Serial worked")
        except OSError as e:
            print_result(
                "SERIAL",
                "ERR",
                f"Error, could not open {self.ca_srl_path} for writing, got error {e}",
                "FAIL",
                e.errno,
            )
            sys.exit(e.errno)

    def sign_device_certificate(self):
        # Check for file existence
        if not self.csr_path.exists():
            print_result(
                "SIGN_CERT",
                "ERR",
                f"Missing device CSR file {self.csr_path}",
                "FAIL",
                errno.ENOENT,
            )
            sys.exit(errno.ENOENT)
        if not self.ca_cert_path.exists():
            print_result(
                "SIGN_CERT",
                "ERR",
                f"Missing CA certificate file {self.ca_cert_path}",
                "FAIL",
                errno.ENOENT,
            )
            sys.exit(errno.ENOENT)
        if not self.ca_ext_path.exists():
            print_result(
                "SIGN_CERT",
                "ERR",
                f"Missing CA extensions file {self.ca_ext_path}",
                "FAIL",
                errno.ENOENT,
            )
            sys.exit(errno.ENOENT)
        if not self.ca_srl_path.exists():
            print_result(
                "SIGN_CERT",
                "ERR",
                f"Missing CA serial number file {self.ca_srl_path}",
                "FAIL",
                errno.ENOENT,
            )
            sys.exit(errno.ENOENT)
        if not self.openssl_conf_path.exists():
            print_result(
                "SIGN_CERT",
                "ERR",
                f"Missing Openssl Config file {self.openssl_conf_path}",
                "FAIL",
                errno.ENOENT,
            )
            sys.exit(errno.ENOENT)
        # Build up the OpenSSL command string
        openssl_cmd = 'openssl x509 -req -CAkeyform engine -engine pkcs11 -sha256 -in "'
        openssl_cmd += str(self.csr_path)
        openssl_cmd += '" -CA "'
        openssl_cmd += str(self.ca_cert_path)
        openssl_cmd += '" -CAkey 0:'
        openssl_cmd += hex(self.ca_key_id)[2:].zfill(4)
        openssl_cmd += ' -out "'
        openssl_cmd += str(self.device_cert_path)
        openssl_cmd += '" -days 3650'
        openssl_cmd += ' -extfile "'
        openssl_cmd += str(self.ca_ext_path)
        openssl_cmd += '" -CAserial "'
        openssl_cmd += str(self.ca_srl_path)
        openssl_cmd += '"'
        proc = None
        openssl_env = os.environ.copy()
        openssl_env["OPENSSL_CONF"] = str(self.openssl_conf_path)
        try:
            if self.linux == 1:
                # I don't know why this needs to be different on Linux but it works...
                proc = subprocess.run(
                    openssl_cmd, check=True, text=True, shell=True, env=openssl_env
                )
            else:
                proc = subprocess.run(
                    openssl_cmd,
                    check=True,
                    capture_output=True,
                    text=True,
                    env=openssl_env,
                )
        except subprocess.CalledProcessError as e:
            if proc:
                print_result(
                    "SIGN_CERT",
                    "OPENSSL_ERR",
                    "" + str(proc.stdout) + str(proc.stderr),
                    "FAIL",
                    e.returncode,
                )
                sys.exit(e.returncode)
            else:
                print_result(
                    "SIGN_CERT",
                    "OPENSSL_ERR",
                    f"Failed to run OpenSSL with command '{openssl_cmd}'",
                    "FAIL",
                    e.returncode,
                )
                sys.exit(e.returncode)
        except subprocess.SubprocessError as e:
            print_result(
                "SIGN_CERT",
                "SUBPROCESS_ERR",
                f"Failed to run OpenSSL with command '{openssl_cmd}', got error {e}",
                "FAIL",
                errno.EINVAL,
            )
            sys.exit(errno.EINVAL)

    def store_device_cert(self):
        """Store an AG's certificate to that AG"""
        try:
            with open(self.device_cert_path, "r") as device_cert_file:
                device_cert: str = device_cert_file.read()
                device_cert_json: str = JSONEncoder().encode(dict(device=device_cert))
                pattern = re.compile(r'": "')
                device_cert_json = re.sub(pattern, '":"', device_cert_json)
                self.send_cmd(
                    self.CRYPTO_CLI_MODULE_NAME
                    + " "
                    + self.CMD_STORE_CERT
                    + " "
                    + device_cert_json
                )
                resp = self.read_response(1, "DEVICE_" + self.CMD_STORE_CERT)
                if isinstance(resp, dict):
                    # Valid response, parsed JSON
                    if resp["CRYPTO"]["RESULT"] != "PASS":
                        print_result(
                            "STORE_DEVICE_CERT", "ERR", f"{resp}", "FAIL", errno.EINVAL
                        )
                        sys.exit(errno.EINVAL)
                else:
                    print_result(
                        "STORE_DEVICE_CERT",
                        "ERR",
                        "Response wasn't a JSON dict",
                        "FAIL",
                        errno.EINVAL,
                    )
                    sys.exit(errno.EINVAL)
        except OSError as e:
            print_result(
                "STORE_DEVICE_CERT",
                "ERR",
                f"Failed to read device cert from {self.device_cert_path}, got {e}",
                "FAIL",
                e.errno,
            )
            sys.exit(e.errno)

    def store_ca_cert(self):
        """Store the CA certificate to the AG"""
        try:
            with open(self.ca_cert_path, "r") as ca_cert_file:
                ca_cert: str = ca_cert_file.read()
                ca_cert_json: str = JSONEncoder().encode(dict(ca=ca_cert))
                pattern = re.compile(r'": "')
                ca_cert_json = re.sub(pattern, '":"', ca_cert_json)
                self.send_cmd(
                    self.CRYPTO_CLI_MODULE_NAME
                    + " "
                    + self.CMD_STORE_CERT
                    + " "
                    + ca_cert_json
                )
                resp = self.read_response(1, "CA_" + self.CMD_STORE_CERT)
                if isinstance(resp, dict):
                    # Valid response, parsed JSON
                    if resp["CRYPTO"]["RESULT"] != "PASS":
                        print_result(
                            "STORE_CA_CERT", "ERR", f"{resp}", "FAIL", errno.EINVAL
                        )
                        sys.exit(errno.EINVAL)
                else:
                    print_result(
                        "STORE_CA_CERT",
                        "ERR",
                        "Response wasn't a JSON dict",
                        "FAIL",
                        errno.EINVAL,
                    )
                    sys.exit(errno.EINVAL)
        except OSError as e:
            print_result(
                "STORE_CA_CERT",
                "ERR",
                f"Failed to read CA cert from {self.ca_cert_path}, got {e}",
                "FAIL",
                e.errno,
            )
            sys.exit(e.errno)

    def get_certificate_serial(self):
        self.send_cmd(self.CRYPTO_CLI_MODULE_NAME + " " + self.CMD_PRINTSERIAL)
        resp = self.read_response(1, self.CMD_PRINTSERIAL)
        if isinstance(resp, dict):
            self.cert_serial_actual = (
                resp["CRYPTO"]["MSG"]["PRINTSERIAL"].replace(":", "").upper()
            )
        else:
            print_result(
                "READ_CERT_SERIAL",
                "ERR",
                "Response wasn't a JSON dict",
                "FAIL",
                errno.EINVAL,
            )
            sys.exit(e.errno)

    def print_id_and_serial(self):
        result = JSONEncoder(indent=4).encode(
            {
                "PROVISION": {
                    "CMD": "PRINT_CERT_SERIAL",
                    "MSG": {
                        "IDENTIFIER": self.identifier,
                        "CERT_SERIAL": self.cert_serial_actual,
                        "TOOL_VERSION": self.VERSION,
                    },
                    "RESULT": "PASS",
                    "ERRNO": "0",
                }
            }
        )
        print(result)

    def get_audit_logs(self):
        try:
            audit_session = self.hsm.create_session_derived(
                self.audit_key_id, self.audit_key_password
            )
        except yubihsm.exceptions.YubiHsmAuthenticationError:
            print_result(
                "AUDIT",
                "ERR",
                f"Failed to authenticate with key ID {self.audit_key_id} and password "
                + "{self.audit_key_password}.",
                "FAIL",
                errno.EKEYREJECTED,
            )
            sys.exit(errno.EKEYREJECTED)
        if isinstance(audit_session, AuthSession):
            try:
                logs: LogData = audit_session.get_log_entries()
                audit_session.set_log_index(logs.entries[-1].number)
                logs_json: str = JSONEncoder().encode(
                    {
                        "AUDIT": {
                            "CMD": "GET_LOGS",
                            "MSG": {
                                "UNLOGGED_BOOTS": f"{logs.n_boot}",
                                "UNLOGGED_AUTH": f"{logs.n_auth}",
                                "LOG_ENTRIES": f"{logs.entries}",
                            },
                            "RESULT": "PASS",
                            "ERRNO": "0",
                        }
                    }
                )
                if self.audit_data_path.exists():
                    try:
                        with open(self.audit_data_path, "a") as audit_logs_file:
                            audit_logs_file.write(",\n" + logs_json)
                    except OSError as e:
                        print_result(
                            "AUDIT",
                            "ERR",
                            f"Failed to open {self.audit_data_path} for append",
                            "FAIL",
                            e.errno,
                        )
                else:
                    try:
                        with open(self.audit_data_path, "w") as audit_logs_file:
                            audit_logs_file.write(logs_json)
                    except OSError as e:
                        print_result(
                            "AUDIT",
                            "ERR",
                            f"Failed to open {self.audit_data_path} for append",
                            "FAIL",
                            e.errno,
                        )
                        sys.exit(e.errno)
            except YubiHsmDeviceError as e:
                print_result(
                    "AUDIT",
                    "ERR",
                    f"Failed to get audit logs, error {e}",
                    "FAIL",
                    e.code,
                )
                sys.exit(e.code)
            finally:
                audit_session.close()
        else:
            print_result(
                "AUDIT", "ERR", "Audit session not initialized", "FAIL", errno.ENOENT
            )
            sys.exit(errno.ENOENT)

    def delete_temporary_files(self):
        self.device_cert_path.unlink(missing_ok=True)
        self.csr_path.unlink(missing_ok=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Provision an Asset Gateway with keys & certificates."
    )
    parser.add_argument(
        "-c",
        "--com_port",
        nargs=1,
        required=True,
        type=str,
        help="COM port where the AG is connected",
    )
    parser.add_argument(
        "--ca_common_name",
        nargs=1,
        required=True,
        type=str,
        help="Common Name of the Certificate Authority associated with the HSM being used",
    )
    parser.add_argument(
        "-b",
        "--baud",
        nargs=1,
        required=False,
        type=int,
        help="Baud rate of the AG serial port",
        default=[115200],
    )
    parser.add_argument(
        "--ca_key_id",
        nargs=1,
        required=True,
        type=str,
        help="Hex Key ID of the signer asymmetric key in the HSM",
    )
    parser.add_argument(
        "--audit_key_id",
        nargs=1,
        required=True,
        type=str,
        help="Hex Key ID of the audit authentication key in the HSM",
    )
    parser.add_argument(
        "--audit_key_password",
        nargs=1,
        required=True,
        type=str,
        help="Passphrase of the audit authentication key in the HSM",
    )
    parser.add_argument(
        "--ca_data_directory",
        nargs=1,
        required=False,
        type=str,
        help="Full path to the Certificate Authority data directory",
        default=["%APPDATA%\\AGCertificateProvisioner\\ca"],
    )
    parser.add_argument(
        "--device_data_directory",
        nargs=1,
        required=False,
        type=str,
        help="Full path to the device data directory for temporary files",
        default=["%APPDATA%\\AGCertificateProvisioner\\device"],
    )
    parser.add_argument(
        "--audit_data_directory",
        nargs=1,
        required=False,
        type=str,
        help="Full path to the device data directory for temporary files",
        default=["%APPDATA%\\AGCertificateProvisioner\\audit"],
    )
    parser.add_argument(
        "--connector_url",
        nargs=1,
        required=False,
        type=str,
        help="URL of a running YubiHSM connector, eg http://127.0.0.1:12345/api",
        default=["http://127.0.0.1:12345/api"],
    )
    parser.add_argument(
        "--openssl_conf",
        nargs=1,
        required=True,
        type=str,
        help="Path to the OpenSSL Config file for the HSM",
    )
    parser.add_argument(
        "--debug",
        nargs=1,
        required=False,
        type=int,
        default=[0],
        help="Print Debug",
    )
    parser.add_argument(
        "--linux",
        nargs=1,
        required=False,
        type=int,
        default=[0],
        help="0 if running on Windows, 1 if running on Linux",
    )
    args = parser.parse_args()
    provisioner = CertificateProvisioner(
        com_port=args.com_port[0],
        ca_cn=args.ca_common_name[0],
        baud=args.baud[0],
        ca_key_id=int(args.ca_key_id[0], base=16),
        audit_key_id=int(args.audit_key_id[0], base=16),
        audit_key_password=args.audit_key_password[0],
        audit_data_dir=args.audit_data_directory[0],
        ca_data_dir=args.ca_data_directory[0],
        device_data_dir=args.device_data_directory[0],
        connector_url=args.connector_url[0],
        openssl_conf=args.openssl_conf[0],
        debug=args.debug[0],
        linux=args.linux[0],
    )
    # Connect to the AG serial port
    provisioner.connect_to_ag()
    # Read the AG's device identifier (CSN).
    provisioner.get_device_identifier()
    # Command the AG to generate a new key pair
    provisioner.gen_keys()
    # Get a Certificate Signing Request (CSR) from the AG
    provisioner.get_csr()
    # Make a new serial number for the device certificate
    provisioner.generate_certificate_serial()
    # Sign the device's CSR, resulting in a device certificate (cert)
    provisioner.sign_device_certificate()
    # Save device cert to AG
    provisioner.store_device_cert()
    # Save CA cert to AG
    provisioner.store_ca_cert()
    # Get audit logs
    provisioner.get_audit_logs()
    # Ask the ag what its cert serial is
    provisioner.get_certificate_serial()
    # Print a result message containing the identifier and certificate serial number generated
    provisioner.print_id_and_serial()
    # Delete the temporary device cert & CSR files.
    provisioner.delete_temporary_files()

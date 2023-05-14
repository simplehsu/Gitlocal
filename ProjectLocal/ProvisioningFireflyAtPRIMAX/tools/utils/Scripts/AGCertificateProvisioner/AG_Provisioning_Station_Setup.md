# AG Provisioning Station

## AG Provisioning Station Setup

### Install software

Boot the computer and log in.
Plug in the USB drive.
Open the USB drive.
Open the "Install" folder.
Run VC_redist.x64.exe, install it with default settings.
Run Win64OpenSSL_Light-1_1_1n.msi, install it with default settings.
Run yubihsm-connector-windows-amd64.msi, install it with default settings.
Run yubihsm-shell-x64.msi, install it with default settings.
Go up one folder to the USB drive root.
Open the "Copy Contents into C" folder.
Copy all files & folders found there into the "C:\" folder. Write into folders as needed, nothing should be overwritten for a fresh install.

### Install configuration

Open the USB drive.
Open the "Copy contents into %APPDATA%".
Copy all files & folders found there into the "%APPDATA%\" folder. Write into folders as needed, nothing should be overwritten for a fresh install.
Safely remove (eject) the USB drive.

### Configure Windows settings

Start→Settings→System→About (in the left side bar)→Advanced system settings
Click "Environment Variables..."
Under the user variables, click Path.
Under the user variables, click "Edit..."
Click "New"
Click "Browse...", and locate the OpenSSL-Win64 bin directory (defaults to `C:\Program Files\OpenSSL-Win64\bin`)
Click "Ok"
Click "New"
Click "Browse...", and locate the YubiHSM Shell bin directory (defaults to `C:\Program Files\Yubico\YubiHSM Shell\bin`)
Click "Ok"
Click "New"
Click "Browse...", and locate the AG Certificate Provisioner (defaults to `C:\Program Files\AG Certificate Provisioner`)
Click "Ok"

### Connect a USB-Serial adapter

Connect the USB-Serial adapter that will be used for communicating with the AG.
Note the COM port of that adapter, it can be found in the windows Device Manager under "Ports (COM & LPT). For example `COM8`.

### Reboot the computer for the changes to take effect

Reboot.

### Verify the HSM matches the configuration files provided

Note the 8-digit serial number printed on your HSM. For example "16 499 817". This will be noted as `<HSM SERIAL NUMBER>` below.
Plug the HSM into a USB port on the computer.
Open folder "%APPDATA%\AGCertificateProvisioner". There should be a folder for your HSM, For example "hsm-prod-1". Open that folder.
Open the "ca" folder.
There should be three files: An "`AG CA <HSM SERIAL NUMBER>.crt`" file, an "`AG CA <HSM SERIAL NUMBER>.srl`" file, and a "client_ext" file.
Go up one folder.
Open the "etc" folder.
There should be one file, an "`AG CA <HSM SERIAL NUMBER>.conf`".
Open that file.
Find the line beginning with "commonName". It should be
`commonName              = "AG CA <HSM SERIAL NUMBER>"`
That line should already contain your HSM's serial number. Note the value after the `=` sign, you'll need it later.
Find the line beginning with "MODULE_PATH". It should be
`MODULE_PATH = "C:\\Program Files\\Yubico\\YubiHSM Shell\\bin\\pkcs11\\yubihsm_pkcs11.dll`
if you installed yubihsm-shell-x64.msi to the default location. If you picked a different location, find the `yubihsm_pkcs11.dll` and put the full path to it in the MODULE_PATH, remembering to double all `\` characters.
Close that file.
Go up one folder.
There should be a file, "passwords.txt".
Open that file.
The first line should be `#<HSM SERIAL NUMBER>`.
The use of the provisioning station will require the AUDIT ID and PIN, and the CA ID.

## Using the AG provisioning station

### Getting help

`AgCertificateProvisioner --help` will print a description of all options.

### Normal use of the AG Certificate Provisioner

A PowerShell script that accepts the COM port to use has been provided. It assumes all files are in the locations described above. It is named Prod########.ps1, where ######## is the serial number of the HSM it's configured for.

For example, if the AG to be provisioned were on `COM8`, and the HSM were 16 499 818, one could run `.\Prod16499818.ps1 COM8` to provision the connected AG.

The certificate provisioner will output a JSON result. On success, it will print the AG's identifier and the certificate serial number. These must be stored and be used to create the assembly record. Example successful output:

```JSON
{
    "PROVISION": {
        "CMD": "PRINT_CERT_SERIAL",
        "MSG": {
            "IDENTIFIER": "AT4-945-58K",
            "CERT_SERIAL": "20982b31889ee711f91541b75d05978f4a488186"
        },
        "RESULT": "PASS",
        "ERRNO": "0"
    }
}
```

If an error occurs, that should also print a JSON error message.

### Advanced use of the AG Certificate Provisioner

You will need to specify the following options:
`--com_port` should have the COM port to which the USB-Serial adapter is connected. For example `--com_port COM8`
`--ca_key_id` should have the ID from the CA line in passwords.txt. For example `--ca_key_id="0x7a84"`
`--audit_key_id` should have the ID from the AUDIT line in passwords.txt. For example `--audit_key_id="0x3f62"`
`--ca_common_name` should have the commonName from the .conf file, which includes the HSM serial number. For example `--ca_common_name="AG CA 16 499 817"`
`--ca_data_directory` should have the full path to the "ca" directory. Forward slashes are fine if using PowerShell. For example `--ca_data_directory="%APPDATA%/AGCertificateProvisioner/hsm-prod-1/ca"`
`--device_data_directory` should have the full path to the "device" directory. For example `--device_data_directory="%APPDATA%/AGCertificateProvisioner/hsm-prod-1/device"`
`--audit_data_directory` should have the full path to the "audit" directory. For example `--audit_data_directory="%APPDATA%/AGCertificateProvisioner/hsm-prod-1/audit"`
`--openssl_conf` should be the full path to the .conf file for this HSM. For example `--openssl_conf="%APPDATA%/AGCertificateProvisioner/hsm-prod-1/etc/AG CA 16 499 817.conf"`
You may specify the following options, but don't have to if everything is in its default configuration.
`--connector_url` is optional. If you configured the YubiHSM connector to listen on a non-default port or IP address, it must be supplied here. For example `--connector_url="http://127.0.0.1:12345/api"`
`--baud` is optional. If the AG is not running at 115200 baud, you must supply the baud rate here. For example `--baud 115200`

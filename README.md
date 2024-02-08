# T.Nebula - FTP downloader for *** clients:

<!-- TOC -->
* [T.Nebula - FTP downloader for T-X clients:](#tnebula---ftp-downloader-for-t-x-clients)
  * [Description](#description)
  * [Requirements](#requirements)
  * [Usage](#usage)
    * [Launch arguments](#launch-arguments)
    * [Usage examples](#usage-examples)
    * [Useful tips](#useful-tips)
  * [Building executables with PyInstaller](#building-executables-with-pyinstaller)
<!-- TOC -->

## Description

This script allows downloading and installing/launching the latest build of a *** client based on the provided parameters:
* Product (TS or TG)
* Build type (Develop, Release candidate or Release)
* Branch (for Develop builds)

The parameters can be either provided as launch arguments or input at runtime.

The files are downloaded to the script's working directory following the `./<product>/<build_type>/<branch>` path pattern. The root directory can be overriden in the launch parameters (see Usage section).

Once the file is downloaded (or if it already exists), the script will suggest installing/running the app (the process depends on the client type and OS).


On the first run, the script will ask for the FTP server password. It can be input manually and is then stored locally

## Requirements

* Python 3.10

## Usage

1. Clone the repository
2. Run in terminal: `python3 <repository_path>/main.py`
   * If launched without arguments, the script will ask for product, build type and branch input
   * Argument options are provided below.
3. (On first launch) Provide FTP password for the server.

### Launch arguments

The arguments can be provided in any order

1. `-p {TS,TG}, --product {TS,TG}`:
   * Choose between T.S and T.G.
   * Valid values are TG ot TS.
2. `-t {DEV,RC,RELEASE}, --build_type {DEV,RC,RELEASE}`:
   * Set the type of the build.
   * Valid values are DEV,RC and RELEASE
3. `-b BRANCH, --branch BRANCH`:
   * Branch name, e.g. "TS-666" or "TG-1069".
   * Set to "develop" for the main develop build.
   * If provided, sets the product and build type automatically
4. `-y, --install`:
   * Install/launch the app once downloaded
   * For Android, `adb install` will be launched. If a downgrade is required, the app will be reinstalled.
5. `-d DIRECTORY, --directory DIRECTORY`:
   * Set the working directory for the script (root folder for downloads).
6. `--no_delete`:
   * Set this flag to leave the installation file on the disk after successful installation (the file is deleted by default)

### Usage examples

* Launch the script and input all parameters manually:
```shell
python3 ~/ftp-loader/main.py
```
* Install latest release version of T.S
```shell
python3 ~/ftp-loader/main.py -p TS -t RELEASE -y
```
* Download latest T.G dev build for TG-1150 branch to a custom directory:
```shell
python3 ~/ftp-loader/main.py -b TG-1150 -d ~/T/Clients
```

### Useful tips

1. On Mac or Linux, add the following to the `~/.zshrc`, `~/.bashrc` or other shell you are using. Change the `<repo_path>` to where the repository is cloned:
```shell
t.nebula() {
	python3 <repo_path>/ftp-loader/main.py "$@"
}
```
You can now launch the script by typing `t.nebula`, e.g. `t.nebula -p TG -t RELEASE -y`

## Building executables with PyInstaller

* **Windows:** `pyinstaller --onedir --uac-admin --add-binary adb\adb.exe:adb  .\main.py --distpath dist\Windows -n T.Nebula --noconfirm --hide-console minimize-early --add-data T-chan.png:. --add-data t-nebula.ico:. --icon t-nebula.ico --add-binary adb\AdbWinUsbApi.dll:adb --add-binary adb\AdbWinApi.dll:adb`
* **Linux:** ` python3 -m PyInstaller --onefile --add-binary adb/adb-linux:adb main.py --distpath bin -n t.nebula-linux \
--add-data T-chan.png:. --add-data t-nebula.gif:. --clean --hidden-import='PIL._tkinter_finder'`
* **MacOS:**

```shell
python3 -m PyInstaller --onefile --clean --add-binary adb/adb-mac:adb main.py --distpath dist/macOS -n T.Nebula --noconfirm --add-data T-chan.png:. --add-data t-nebula.gif:. --icon t-nebula.ico --windowed
create-dmg --overwrite dist/macOS/T.Nebula.app dist/macOS
mv dist/macOS/T.Nebula\ 0.0.0.dmg dist/macOS/T.Nebula.dmg
```

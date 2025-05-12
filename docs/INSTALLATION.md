# Installation and Getting Started

You have three options for using CyberCraft:
- **Pre-Compiled**: Download a pre-compliled executable for Windows or macOS. (_Planned: Summer 2025_)
- **Complile Yourself**: Complile the Python code to an executable for your Windows or macOS platform.
- **Native Python**: Run the native Python code on your Windows or macOS platform. 
  - _May work on Linux. Untested._

## Pre-Compiled (Planned: Summer 2025)
Download a pre-compliled executable for Windows or macOS.

### Getting Started
_Links will be provided here when available._

Pre-compiled CyberCraft is designed to run as a stand-alone executable. 
- There is no installer. 
- Administrative access is not necessary. 
- Once downloaded, an Internet connection is not required.

To run the pre-compiled CyberCraft executable you must be using one of the following operating systems:
- Windows 10 or greater; or
- macOS 13 or greater.

Contact your employer's IT department if CyberCraft is blocked from running on your workstation.

To install CyberCraft:
1. download the executable
2. move it from your Downloads folder to an appropriate location on your computer.

To run CyberCraft, either:
- double-click on the executable from your file explorer; or 
- run it from the command line.

Read the [File Locations](./FILE_LOCATIONS.md) information for details about where CyberCraft stores its files.

## Compiling Yourself

Complile the Python code to an executable for your Windows or macOS platform.





## Run CyberCraft Python Native

The following steps allow you to run the Python code without compiling it.

### Windows
Perform the following from the command line within the local CyberCraft repository folder:
1. CD to the `src` folder
2. Type `run` to execute the `run.bat` file

```
cd src
run
```

### macOS

#### Set Execute Permissions
After cloning the repository to your Mac, you must first give execute permissions to the following bash scripts:
  - `src/install-vent.sh`
  - `src/run.sh`
  - `src/compile-dev.sh`
  - `src/compile-prod.sh`
  - `src/resource/resources.sh`

Perform the following from the command line within the local CyberCraft repository folder:
1. CD to the `src` folder
2. Set permissions on the bash files.

```
cd src
chmod +x *.sh resource/*.sh
```

#### To run CyberCraft

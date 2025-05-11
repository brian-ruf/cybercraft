<div align="center">
    <h1 style="border:none; "><img style="vertical-align: middle;" src="./src/resource/img/CC_Logo3.svg" alt="CyberCraft Logo" width="50"/><span style="vertical-align: middle; font-style:bold;">&nbsp;CyberCraft</span></h1>
</div>
CyberCraft is a desktop graphical user interface (GUI) application for viewing, validating, and converting OSCAL content. It runs as a stand-alone, and while it can interact across a network, no network connectivity is required.

<br />

---
# CyberCraft Development

CyberCraft is based on Python 3.12, PySide6, and the SaxonC HE Python Library. It is designed to be compliled to a single executable file for Windows and Mac using PyInstaller.

The desktop application simulates a back-end web server and front-end browser entirely _within_ the application's execution space. Ports are not open. A network is not required. 

The code base for CyberCraft's architecture started with an [example desktop web browser application published by Qt](https://doc.qt.io/qtforpython-6.2/examples/example_webenginewidgets__tabbedbrowser.html).

For more information, check out the [Technical Details](./docs/TECHNICAL_DETAILS.md).

## Development Progress

**CYBERCRAFT IS STILL IN THE EARLY STAGES OF DEVELOPMENT**

## Current Status

- Application Framework Established
  - GUI and CLI capabilities
  - Robust logging
  - OS-appropriate application folders used
  - _Portable Mode_ to keep all application folders in the startup location
- Acquisition and management of NIST-published OSCAL support files:
  - NIST-published OSCAL schema validation files
  - NIST-publised OSCAL format convertion files
  - **all OSCAL versions and formats supported**
  - Ability to check for and acquire support files for new OSCAL versions when available
  - Use GUI for interactive management
  - Use CLI for unattended management

## In-Progress (Spring 2025)

- Project approach for managing a collection of related OSCAL content (i.e. AR -> AP -> SSP -> Controls)
  - Manage project metadata
  - Load OSCAL content into project
  - Auto-load related OSCAL artifacts 
  - Handle missing or unreachable content
  - Auto-validate OSCAL Content using NIST schema-validation files
  - Export OSCAL content in any OSCAL format using NIST format convertion files.
  - View OSCAL content metadata

## Planned
- Remote Sources
  - Access and load content from the OSCAL Content Registry ([https://registry.oscal.io](https://registry.oscal.io))
- View Specific OSCAL Content:
  - Control Catalogs and Baselines
  - Component Definitions
  - SSP
  - POA&M
  - AP and AR 
- Collaborative Viewing
  - Network shares of CyberCraft projects
  - Cloud drive shares of CyberCraft projects
  - Use of enterprise relational databases for shared project content 
- Load/process NIST-published OSCAL Metaschema for more robust OSCAL content validation
- Collaborative Reviewing
  - Attach review comments to OSCAL content
  - Threaded comment conversations
  - Comment resolution tracking
- OSCAL Content Authoring:
  - Baselines/Profiles
  - Component Definitions

---
# Installation and Getting Started

You have three options for using CyberCraft:
- **Pre-Compiled**: Download a pre-compliled executable for Windows or macOS.
  - _Planned: Summer 2025_
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

Read the [File Locations](./docs/FILE_LOCATIONS.md) information for details about where CyberCraft stores its files.

## Compiling Yourself


## Compiling or Running the Native Python Code

The following is required to either complie the CyberCraft Python code to an executable or run it as a native Python application:
- Local clone of the Cyber repository 
- Python 3.12+ 
  - 3.9 - 3.11 are likely to work, but have not been tested.
- An Internet connection

## Check Dependencies
After cloning the repository:
- switch to the `cybercraft` repository folder and type `python --version` to ensure Python is installed and accessible via the CLI


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

<br /><br />
---
<div align="center">
CyberCraft is created by

<img src="./src/resource/img/Ruf_Risk_Logo.png" alt="Ruf Risk Logo" width="100" /><br />
_Cybersecurity&nbsp;Automation_&nbsp;<img src="src/resource/img/icon_mini.png" width="10" height="10" />&nbsp;_OSCAL&nbsp;Enablement_<br />
_Consulting_&nbsp;<img src="src/resource/img/icon_mini.png" width="10" />&nbsp;_Proposal&nbsp;Support_&nbsp;<img src="src/resource/img/icon_mini.png" width="10" />&nbsp;_Training_<br />
<a href="https://RufRisk.com" style="font-style: normal;" target="_blank">https://RufRisk.com</a>
</div>

---


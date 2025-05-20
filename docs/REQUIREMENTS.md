# REQUIREMENMTS

The requirements discussed here are for self-compilied or native python execution of CyberCraft.

For pre-compiled CyberCraft executables, please see the [notes](#pre-compiled-cybercraft-executables) at the bottom. 

## Table of Contents

Please see each of the following sections for more information:
- [Requirements Summary](#requirements-summary)
- [Platforms](#platforms)
- [Python and PySide6](#python-and-pyside6)
- [Internet Connection](#internet-connection)
- [CyberCraft Pre-Compiled Executables](#pre-compiled-cybercraft-executables)

## Requirements Summary

CyberCraft is designed to run on Windows 10+ and macOS 13+ using Python 3.12+. At this time, it has only been tested on Windows.

CyberCraft may run on Linux and Android without much modification and these are target platforms for Q4 2025.

While an Internet connection is not required for normal op9eration, it is required to clone/update the repo, download Python dependencies. A few featurs application require an Internet connection, such as checking for new versions of OSCAL.j

# Platforms

CyberCraft is designed and developed for Windows 10+ and macOS 13+. It may also work on recent Linux distros.

## Windows:

CyberCraft is currently developed and tested on Windows 11. 

Testing on Windows 10 is planned for Summer 2025.

## macOS:

Testing on macOS 13, 14, and 15 is planned for Summer 2025.

## Linux:

CyberCraft is likely to work on newer versions of Linux.
As time permits, this may be tested in the latter part of 2025. 

The command for granting execution permission to the macOS build and run bash scripts will vary by Linux OS. 

Once execution permission is grated, the macOS bash scripts should work for Linux.

# Python and PySide6

CyberCraft is developed and tested using Windows 11, Python 3.12.4 and PySide6 6.9.0. 

On macOS, PySide6 requires Python 3.6 - 3.11 and does not install for 3.12+ as of May 15, 2025.

The current version of PySide6 requires Python 3.7 or later.While CyberCraft may work with Python versions earlier than 3.12, no testing has been conducted, nor is testing of earlier Python versions planned.

## Check Your Python Version
After cloning the repository:
- switch to the `cybercraft` repository folder and type `python --version` to ensure Python is installed and accessible via the CLI. 

```
cd cybercraft
python --version
```

# Internet Connection
An internet is required to:
- Clone the repository
- Acquire dependencies from [https://pypi.org/](https://pypi.org/) before compiling or running the native Python code
- Check for new OSCAL versions from [https://github.com/usnistgov/OSCAL](https://github.com/usnistgov/OSCAL)
- (**Future**) Acquire content from the OSCAL Content Repository ([https://registry.oscal.io](https://registry.oscal.io))

OSCAL support files from the NIST OSCAL GitHub repository are pre-loaded into CyberCraft. For this feature, an Internet connection is only necessary to check for new OSCAL versions or refresh/repair the support files for a current OSCAL version.

# Pre-Compiled CyberCraft Executables

The only requirement for pre-compiled CyberCraft executables is a supported [platform](#platforms). No other software is required.

- There is **no** installer. 
- Python is **not* required.
- Administrative access is **not** required. 
- Once downloaded, an Internet connection is **not** required for normal use.
  - Some features, such as checking for a new OSCAL version, require an Internet connection. 

Contact your employer's IT department if CyberCraft is blocked from running on your workstation.

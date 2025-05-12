# Installation and Getting Started

You have three options for using CyberCraft:
- **Pre-Compiled**: Download a pre-compliled executable for Windows or macOS. (_Planned: Summer 2025_)
- **Complile Yourself**: Complile the Python code to an executable for your Windows or macOS platform.
- **Native Python**: Run the native Python code on your Windows or macOS platform. 
  - _May work on Linux. Untested._

## Pre-Compiled (Planned: Summer 2025)
Download a pre-compliled executable for Windows or macOS.

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

See the [Starting](./STARTING.md) information for details about how to start CyberCraft.

See the [File Locations](./FILE_LOCATIONS.md) information for details about where CyberCraft stores its files.

## Compile Yourself or Run Native Python

The following steps allow you to compile CyberCraft to an executable for your platform or run the Python code natively without compiling it.

### 1. Clone the repository to your workstaton

From the command line interface (CLI) select an appropriate locaiton for the repository. 

```
cd /your/github/repositories/folder
git clone https://github.com/ruf-risk/cybercraft.git
```

### 2. Change directory (CD) into the `src` directory. If running on macOS, set execute permissions.

#### Windows
```
cd cybercraft\src
```

#### macOS
```
cd cybercraft/src
chmod +x *.sh resource/*.sh
```

### 3. Use the appropriate script to compile or run CyberCraft

#### Windows
Compile to a Windows binary:
```
compile.bat
```

Run Python code natively:
```
run.bat
```


#### macOS
Compile to a macOS binary:
```
./compile.sh
```

Run Python code natively:
```
./run.sh
```

### 4. Run CyberCraft

See [Starting](./STARTING.md) for information on how to start CyberCraft in normal or portable mode, as well as other command-line options.

# All Scripts
Each of the following scripts has a Windows version, ending in `.bat` and a macOS/Bash version ending in `.sh`. 

  - `src/run`: Runs the native CyberCraft Python code.
  - `src/test`: Runs the native CyberCraft Python code in porable mode with debugging enabled.

  - `src/compile`: Compiles CyberCraft to a stand-alone executable for your platform
  - `src/compile-dev`: Compiles CyberCraft to a stand-alone executable with additional debugging capabilities.

  - `src/install-venv`: Installs PyInstaller and all CyberCraft Python dependencies. This is called by the run, test and complile scripts, but may be run manually. 
  - `src/resource/resources`: Creates `src/resource_rc.py`, which includes all of the files in `src/resource` child folders, effectively embedding these files into the application code. This is a PySide6 capability, and is required to achieve a stand-alone executable. This is called by the run, test and complile scripts, but may be run manually.


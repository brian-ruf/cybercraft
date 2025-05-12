# TECHNICAL DETAILS


## DESIGN GOALS
The following design goals drive the development of CyberCraft:

- Stand-alone desktop application
- Fully functional in an air-gapped environment (No Internet connection required)
- One code base that runs on both Windowws and Mac
- Core/default functionality does not require open ports on the desktop application
  - Future optional functionality may require open ports at the user's discreation
- The ability to transition to a web-based solution in the future
- Single user initially using local SQLite3 database files
  - Short term future small-group collaboration using shared SQLite3 files
  - Long term future enterprise-level collaboration using existing enterprise database capabilities
- Ability to interact with other services via API calls, such as GitHub repositories, the OSCAL registry, and organization-specific resources.

## ARCHITECTURE CONCEPT

- A single desktop application acting as both a user web browser and a back-end server within a single application.
- Front-end logic uses HTML5/CSS/JavaScript 
- Back-end logic remains separate code  
- Simulate communication between a front and back end similar to web-sockets, but without opening ports.
- Requires asynchronous processing to enssure the front-end remains responsive while the back-end is performing long-running tasks
- With few exceptions, each application capability is exposed as a web interface within a tab.
  - Each tab has its own backend object and handler.
  - Tabs run completely independent of each other.
- The user is able to interact with the application's menus or the web content within each tab.

## DEVELOPMENT APPROACH

CyberCraft is built using Python 3.12 and the Pyside6 library for cross-platform desktop development
- PySide6 is based on Qt, a highly mature, cross-platform GUI library written in C.

The code base for CyberCraft's architecture started with an [example desktop web browser application published by Qt](https://doc.qt.io/qtforpython-6.2/examples/example_webenginewidgets__tabbedbrowser.html).

## KEY MODULES
- `src/cybercraft.py`: the main application. Handles startup parameters, application initialization, and determines whether to start the GUI or process at the command line.
- `src/cybercraft_gui.py`: the core GUI for cybercraft. This creates and maanges the primary desktop application, including menus and tab management.
- `src/backend.py`: simulates back-end processing of a web-server. Receives JSON messages sent by the front-end's JavaScript and either processes them directly, or routes them to the appropriate handler. 

- `src/tabs/`: (NOTE: the backend expects all tab modules to follow the same pattern of functions and async processing.)
  - `src/tabs/startup.py`: displays and manages the startup page with the CC logo and "Getting Started" button
  - `src/tabs/support.py`: displays and manages the list of supported OSCAL versions
  - `src/tabs/oscal_project.py`: displays and manages an OSCAL Project file  

### Resource Modules
All files in `src/resource/` sub-folders are embedded into the application via a PySide6 resource mechanism (described [here](https://doc.qt.io/qtforpython-6/tutorials/basictutorial/qrcfiles.html) and [here](https://www.pythonguis.com/tutorials/pyside6-qresource-system/)) and accessed via native PySide6 methods or the `load_resoure()` function in the `src/backend.py` module.



The `src/resource/resources.bat` file performs the following steps:
- runs the `src/resource/generate_qrc.py` python module, which generates a PySide6 `src/resource/resources.qrc` file
- runs the `src/venv/Scripts/pyside6-rcc` PySide6 utility, which creates the `src/resources_rc.py` file. This file contains all embedded resources.

The `src/run.bat` file calls the `src/resource/resources.bat`, ensuring the latest changes to resources are incorporated before the application runs.


### Tab Processing Setup
- Tab logic is defined in tab modules, found in the `src/tabs/` sub-folder. 
- Typically a tab moudle uses one or more associated templates, found in `src/resource/templates`.
  - The primary template (`src/resource/templates/primary.html`) has standard zones, and the ability to turn zones on and off. 
  - Some templates are full HTML files. Others are HTML fragments.

- In `cybercraft_gui.py`:
  - the `from tabs import ...` line must include the name of each tab module
  - The `TAB_STARTUP` dict on the next line must include an entry for each tab module 
  - A new tab is triggered via a call to the `MainWindow.show_new_tab("module-name")` method
    - "module-name" is the appropriate key-name from `TAB_STARTUP`
    - This allows the GUI to "know" about new tab modules simply by expanding the `from tabs import` and `TAB_STARTUP` informaiton at the top of `cybercraft-gui.py`. 
    - Typically the `MainWindow._create_menu()` method is updated as well.

### Tab Processing Flow
- A new tab is triggered via a call to the `MainWindow.show_new_tab("module-name")` method with the appriropate tab module reference in place of "module-name", such as "startup", "support", "project", etc.
- The module reference is pre-populated with:
  - the tab title
  - the `initial-display` function to call for the starting content within the tab; and
  - the `handler` function, which is where the `Backend` object forwards messages when received from the web page in the tab.   
- A new tab is created in the application.
- A communications `channel` is setup for communication between the web content in the tab and the application's `Backend` object. (This is the PySide6 internal alternative to websockets)
- A new `Backend` object is established and dedicated to the tab. (Each tab has its own `Backend` object)
- The `Backend` object is then registered with the `channel` as the communications handler.  

# File Locations

CyberCraft assigns folder locations based on what is industry standard for the detected operating system.

When operating in "portable" mode, all folders are stored relative in the startup folder.

The following locations are impacted by operating system in normal mode or by starting CyberCcraft in portable mode:
- Application configuration files
- Application support files
- Log files
- Temporary cache
- Application Content (OSCAL projects and content)


## Check Locations

Use `--info` to see where CyberCraft stores its content.

```
CyberCraft --info
```

If you are using CyberCraft in portable mode, use both `--info` and `--portable` together to verify application files are being saved in the application folder.
```
CyberCraft --info --portable
```

# OS-Specific Locations

CyberCraft assigns folder locations based on what is industry standard for the detected operating system
- Windows:
    - "content": "cybercraft" sub-folder in the user's "My Documents" folder
    - "appdata": "cybercraft" sub-folder in the user's %AppData% folder
- OSX / Linux:
    - "content": "~/cybercraft" ("cybercraft" sub-folder in the user's $HOME (~) folder)
    - "appdata": "~/.cybercraft" (".cybercraft" sub-folder in the user's $HOME (~) folder)
- Unrecognized:
    - "content": "content" sub-folder in the application's folder
    - "appdata": "appdata" sub-folder in the application's folder
- Mobile devices (iOS, Android) to be addressed in the future.


# Portable Mode

To keep all application logs, content, and support files in the application startup folder run CyberCraft in portable mode:

```
CyberCraft --portable
```

**IMPORTANT:** The application _startup_ folder is sometimes different from the application location itself. Please be mindful of startup folder context when lookikng for your files. Use the [Check Locations](#check-locations) instructions if needed. 

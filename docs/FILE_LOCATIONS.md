# File Locations

Normally, CyberCraft will store configuration, logs, temporary cache and content using the typical locations for your operating system. 


## Portable Mode

To keep all application logs, content, and support files in the application startup folder run CyberCraft in portable mode:

```
CyberCraft --portable
```

## Check Locations

Use `--info` to see where CyberCraft stores its content.

```
CyberCraft --info
```

If you are using CyberCraft in portable mode, use both `--info` and `--portable` together to verify application files are being saved in the application folder.
```
CyberCraft --info --portable
```

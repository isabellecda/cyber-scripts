# cyber-scripts
Scripts for automating cyber exploration.

## Scripts

### HTTP
* http-csrf-curl.sh - Tests forms with CSRF token. 

### PHP
* php-simple-host-expl.php - Simple host exploration using PHP.
* php-host-expl.php - Host exploration using PHP. Configures commands based on server OS and enabled functions.
* php-host-expl-js.php - Host exploration using PHP and converting commands to base 64 (using javascript) before sending to server.
* php-host-expl-js-b64.php - Host exploration using PHP and converting commands to base 64 (using javascript) before sending to server. Full script encoded in base 64 so that it can be used in possible injection attacks.

### SMB
* smb-check-shares-perms.sh - Checks SMB shares permissions.
* smb-ckeck-dir-perms.sh - Checks SMB directory permissions in every listed share.

### Buffer Overflow
* Help functions for exploting buffer overflow vulnerabilities in a Windows remote binary. 

### OSINT
* shodan-host-search.py - Shodan API example usage. Searches Shodan for hosts defined by IP blocks in CIDR notation (file input)


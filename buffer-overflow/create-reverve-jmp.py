#!/usr/bin/python3
#
# create_reverve_jmp.py
#
# https://github.com/isabellecda/cyber-scripts
#

import sys

# Creates backwards jmp instruction
# So as not to depend on external asm compilers or opcode generators, the following long jump code can only jump numbers divisible by 256. The following assembly code is used to jmp backwards (ref.: phrack #62 article 7, Aaron Adams):
#	fldz     		; D9EE
#	fnstenv [esp-12]  	; D97424F4
#	pop ecx    		; 59
#	add cl,10   		; 80C10A
#	nop     		; 90
#	dec ch    		; FECD (repeated to add 256*mult jmp size)
#	jmp ecx    		; FFE1  
def create_reverve_jmp(size):
	head = "D9EED97424F45980C10A90"
	tail = "FFE1"
	mult = int(size) % 256
	jmp=""

	for i in range(0, int(mult)):
		jmp = jmp + "FECD"

	jmpCmd = head + jmp + tail

	return jmpCmd
	

if __name__ == "__main__":
	if len(sys.argv) != 2:
		print("Error: missing input parameter")
		print("Usage: {} jmpSize".format(sys.argv[0]))
		print("	jmpSize: Jump size in bytes")
		sys.exit(1)
	
	print(create_reverve_jmp(sys.argv[1]))

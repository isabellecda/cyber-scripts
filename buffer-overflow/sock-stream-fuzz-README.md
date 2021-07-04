# sock-stream-fuzz.py

* Creates a testing buffer string of increased size (loop) to test for buffer overflow.

# Examples

slmail.exe
```
./ig-tcp-fuzzer.py --rhost=10.10.250.108 --rport=110 -v -f --buffstep=300 --interact="USER Charlie" --buffhead="PASS " --closecmd="QUIT"
```

dostackbufferoverflowgood.exe
```
./ig-tcp-fuzzer.py --rhost=10.10.250.108 --rport=31337 -v -f --norec --buffstep=10
```

brainpan.exe
```
./ig-tcp-fuzzer.py --rhost=10.10.250.108 --rport=9999 -v -f --buffstep=200
```

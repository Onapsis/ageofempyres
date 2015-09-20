Requirements
============

PyPy Sandbox

The easiest way is to build from source:

http://pypy.org/download.html#building-from-source

Make sure to use the sandbox building command:

python ../../rpython/bin/rpython -O2 --sandbox targetpypystandalone --withmod-_pypyjson --withmod-struct --withmod-_codecs --withmod-binascii

Once you have that done, change the PYPY_PATH variable in the file run_sandbox.py
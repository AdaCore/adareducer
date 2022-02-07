# adareducer

This program can be used to reduce an Ada code base to a smaller code base
while maintaining a base property. It is typically used for minimising a bug
reproducer.


## Installation

Get a Python 3.7+ interpreter, install
[Libadalang](https://github.com/AdaCore/libadalang)'s Python bindings and then
run:

    pip install /path/to/your/adareducer/clone


## Usage

The interface is similar to that of the
[C-Reduce](https://embed.cs.utah.edu/creduce/) program for C/C++ code bases:

    adareducer project_file oracle.sh

Where `project_file` is the path to a valid `.gpr` project file, and
`oracle.sh` is a bash script which returns `0` as long as the program satisfies
the base property that you are testing for, and non-zero otherwise.

For instance, if you are interested in reducing the program while maintaining
the property that a particular file contains the text "hello", the oracle might
contain something like this:

    grep "hello" foo.adb

If you are interested in getting the minimum program that compiles and prints
"hello", the oracle might look like this:

    # Build the program and exit if the program doesn't build
    # Note the -m2 switch: this tells gprbuild not to look at the
    # timestamps, but the checksum
    gprbuild -m2 -P p.gpr || exit 1

    # Launch the program and verify that it prints "hello"
    ./main | grep "hello"

### Dockerfile
To use the dockezrfile, you will currently need to build your own base images. Instructions for how to do this can be found in [AdaCore/gnat-docker](https://github.com/AdaCore/gnat-docker/).
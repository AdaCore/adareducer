# adareducer

This program can be used to reduce an Ada code base to a smaller code base
while maintaining a base property. It is typically used for minimising a bug
reproducer.

## Using the pre-built program

Adareducer is included in the GNAT Studio package. To access it in command
line mode, you can do:

    gnatstudio_cli adareducer <parameters>

## Installation in a Python environment

Get a Python 3.7+ interpreter, install
[Libadalang](https://github.com/AdaCore/libadalang)'s Python bindings and then
run:

    pip install /path/to/your/adareducer/clone


## Usage

Refer to the corresponding section in [the GNAT Studio documentation](https://docs.adacore.com/live/wave/gps/html/gps_ug/tools.html#the-automatic-code-reducer)

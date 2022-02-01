#!/bin/bash
set -x -e

# Put GNAT in the PATH
export PATH=`ls -d $PWD/$CACHED_GNAT/*/bin |tr '\n' ':'`$PATH
echo PATH=$PATH

# Make libadalang usable from Python
export PYTHONPATH=$LIBADALANG_INSTALL_PREFIX/python/:$PYTHONPATH
export LD_LIBRARY_PATH=$LIBADALANG_INSTALL_PREFIX/lib/:$LD_LIBRARY_PATH
export LD_LIBRARY_PATH=`gnatls -v | grep adalib | xargs`:$LD_LIBRARY_PATH
pip install -r requirements.txt

# Check that libadalang is visible from Python
python -c "import libadalang"

# Run the Makefile
make
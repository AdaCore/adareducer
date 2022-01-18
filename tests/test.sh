set -e

# Make a temporary directory
export ADAREDUCER_TEMP_DIR=` mktemp -d`

trap \
 "{ rm -rf "${ADAREDUCER_TEMP_DIR}" ; exit 255; }" \
 SIGINT SIGTERM ERR

# Copy the test to the temporary directory
cp -R tests/orig/* $ADAREDUCER_TEMP_DIR

# Run ada_reduce.py!
python ada_reduce.py $ADAREDUCER_TEMP_DIR/p.gpr tests/oracle.sh

# Clean up
rm -rf $ADAREDUCER_TEMP_DIR


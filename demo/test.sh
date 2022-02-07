set -e

# Make a temporary directory
export ADAREDUCER_TEMP_DIR=`mktemp -d`

trap \
 "{ rm -rf "${ADAREDUCER_TEMP_DIR}" ; exit 255; }" \
 SIGINT SIGTERM ERR

# Copy the test to the temporary directory
cp -R demo/orig/* $ADAREDUCER_TEMP_DIR

# Run adareducer!
bash adareducer $ADAREDUCER_TEMP_DIR/p.gpr demo/oracle.sh

# Clean up
rm -rf $ADAREDUCER_TEMP_DIR


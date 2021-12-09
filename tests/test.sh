set -e 

export ADAREDUCER_TEMP_DIR=` mktemp -d` 

trap \
 "{ rm -rf "${ADAREDUCER_TEMP_DIR}" ; exit 255; }" \
 SIGINT SIGTERM ERR EXIT

cp -R tests/orig/* $ADAREDUCER_TEMP_DIR
gprbuild -P $ADAREDUCER_TEMP_DIR/p.gpr
python adareducer.py --single-file $ADAREDUCER_TEMP_DIR/proc.adb --follow-closure $ADAREDUCER_TEMP_DIR/p.gpr tests/basic.sh
rm -rf $ADAREDUCER_TEMP_DIR

cd $ADAREDUCER_TEMP_DIR && \
gprbuild -m2 -q -Pp.gpr && \
./proc | grep "hello"

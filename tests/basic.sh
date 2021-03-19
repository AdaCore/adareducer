cd /tmp/_adareducer_test && \
gprbuild -f -q -Pp.gpr && \
./proc | grep "hello"

cd /tmp/_adareducer_test && \
gprbuild -m2 -q -Pp.gpr && \
./proc | grep "hello"

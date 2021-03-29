test:
	rm -rf /tmp/_adareducer_test
	cp -R tests/orig /tmp/_adareducer_test && \
    gprbuild -P /tmp/_adareducer_test/p.gpr && \
    python adareducer.py --single-file /tmp/_adareducer_test/proc.adb --follow-closure /tmp/_adareducer_test/p.gpr tests/basic.sh

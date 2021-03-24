test:
	rm -rf /tmp/_adareducer_test
	cp -R tests/orig /tmp/_adareducer_test && gprbuild -P /tmp/_adareducer_test/p.gpr && python adareducer.py /tmp/_adareducer_test/p.gpr tests/basic.sh

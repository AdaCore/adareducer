all: tests

demonstration:
	bash demo/test.sh

tests:
	cd testsuite ; bash run.sh

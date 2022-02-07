FROM libadalang:latest

RUN pip install e3-testsuite click

ENTRYPOINT ["/bin/bash"]

set -e
gprbuild -m2 -Pp
./hello | grep "hello"
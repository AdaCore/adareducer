set -e
set -x
gprbuild  -m2 -Pp hello
grep Foo hello.adb

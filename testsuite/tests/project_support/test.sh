# Reduce in directory dir1
(cd dir1 ; $ADAREDUCER p.gpr oracle.sh > /dev/null)

# Check that dir1/hello.adb has been minimized
grep "with P" dir1/hello.adb

# Check that dir2/p.adb has been suppressed
[ ! -e dir2/p.adb ] || echo "oh no dir2/p.adb still exists"
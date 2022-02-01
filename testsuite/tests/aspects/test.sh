$ADAREDUCER --single-file hello.adb p.gpr oracle.sh > /dev/null

# Verify that the procedure Check has been removed
cat hello.adb | grep Check || exit 0
set -e

# Build the external project once
gprbuild -q -P src_q/q.gpr -XEXTERNALLY_BUILT=false

cp src_q/a.ads src_q/a.ads.orig
# Try reducing a project that imports an externally built project
export EXTERNALLY_BUILT=true
$ADAREDUCER --single-file hello.adb --follow-closure p.gpr oracle.sh > /dev/null

# We should not have touched a.ads
diff -c src_q/a.ads.orig src_q/a.ads

# Now try reducing a project that imports the same project,
# this time it's not externally built
export EXTERNALLY_BUILT=false
$ADAREDUCER --single-file hello.adb --follow-closure p.gpr oracle.sh > /dev/null

# We should have processed a.ads: cat it, the driver will compare it to test.out
cat src_q/a.ads
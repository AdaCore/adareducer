# This tests against a case where
#  - we're brute-force deleting a.ads
#  - adareducer would crash when trying to process it
#    after it's been deleted
$ADAREDUCER p.gpr oracle.sh > /dev/null
ls | grep world

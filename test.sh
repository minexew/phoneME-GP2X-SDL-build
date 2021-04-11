#!/bin/sh

set -ex

# Test it
export LD_LIBRARY_PATH=/opt/gcc-3.4.6/lib:$LD_LIBRARY_PATH
export PATH=$(pwd)/phoneME-GP2X-SDL/phoneme_feature/build_output/midp/bin/i386/:$PATH
export MIDP_HOME=$(pwd)/phoneME-GP2X-SDL/phoneme_feature/build_output/midp

installMidlet file:///$(pwd)/jars/test.jar
listMidlets
runMidlet 2

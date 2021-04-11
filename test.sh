#!/bin/sh

set -ex

# Test it
export LD_LIBRARY_PATH=/opt/gcc-3.4.6/lib:$LD_LIBRARY_PATH
export PATH=$(pwd)/phoneME-GP2X-SDL/phoneme_feature/build_output/midp/bin/i386/:$PATH
export MIDP_HOME=$(pwd)/phoneME-GP2X-SDL/phoneme_feature/build_output/midp

pkill -KILL runMidlet || true

# https://gist.github.com/joerick/9e2d244f456c2431619e7063eda62e1d
./termfix /dev/tty0

ID=$(installMidlet file:///$(pwd)/jars/$1 | grep -E 'The suite was succesfully installed, ID: [0-9]+' | grep -o -E '[0-9]+')
#listMidlets.sh
runMidlet $ID

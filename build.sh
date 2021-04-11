#!/bin/sh

set -ex

# Install GCC 4 from packages
cd packages
dpkg -i *.deb
cd ..

# Build GCC 3
tar xfa tarballs/gcc-3.4.6.tar.bz2
mkdir -p gcc-3.4.6.build-hostbinutils
cd gcc-3.4.6.build-hostbinutils
../gcc-3.4.6/configure --prefix=/opt/gcc-3.4.6-hostbinutils --enable-languages=c,c++
make
make install
export PATH=/opt/gcc-3.4.6-hostbinutils/bin:$PATH
gcc --version
cd ..

# Build binutils
tar xfa tarballs/binutils-2.16.1.tar.bz2
mkdir -p binutils.build
cd binutils.build
../binutils-2.16.1/configure --prefix=/opt/gcc-3.4.6
make
make install
export PATH=/opt/gcc-3.4.6/bin:$PATH
ld --version
cd ..

# Build GCC 3 AGAIN with new (old) binutils
mkdir -p gcc-3.4.6.build
cd gcc-3.4.6.build
../gcc-3.4.6/configure --prefix=/opt/gcc-3.4.6 --enable-languages=c,c++
make
make install
gcc --version
cd ..

# Build SDL, SDL_image, SDL_mixer
tar xfa tarballs/SDL-1.2.15.tar.gz
cd SDL-1.2.15
./configure --prefix=/opt/gcc-3.4.6
make
make install
cd ..

tar xfa tarballs/SDL_image-1.2.12.tar.gz
cd SDL_image-1.2.12
./configure --prefix=/opt/gcc-3.4.6
make
make install
cd ..

tar xfa tarballs/SDL_mixer-1.2.12.tar.gz
cd SDL_mixer-1.2.12
./configure --prefix=/opt/gcc-3.4.6
make
make install
cd ..

# Install JDK
sed 's/^more <</cat <</' -i tarballs/j2sdk-1_4_2_19-linux-i586.bin
chmod +x tarballs/j2sdk-1_4_2_19-linux-i586.bin
yes | ./tarballs/j2sdk-1_4_2_19-linux-i586.bin

# Compile phoneME
cd phoneME-GP2X-SDL
sh ./compile-vanilla.sh
cd ..

# Pack output
7zr a build_output.7z phoneME-GP2X-SDL/phoneme_feature/build_output

# Configure VGA mode (GRUB1 only)
sed -i 's/^# defoptions=quiet$/# defoptions=quiet vga=0x311/' /boot/grub/menu.lst
update-grub

# Build termfix
gcc -o termfix termfix.c

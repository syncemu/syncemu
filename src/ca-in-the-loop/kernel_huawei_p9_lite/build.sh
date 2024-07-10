#!/bin/bash

LOCAL_DIR=`pwd`

echo "`which aarch64-linux-android-gcc`"
export CROSS_COMPILE="aarch64-linux-android-"
mkdir -p out
echo "Paths and Toolchain loaded!"
make ARCH=arm64 O=./out hisi_6250_defconfig
make ARCH=arm64 O=./out V=1 -j6
printf "\nDone! if it compiled correctly, you'll find the compiled Image at ../out/arch/arm64/boot/Image"
printf "\nThe modules are at out/(device)/*.ko\n"

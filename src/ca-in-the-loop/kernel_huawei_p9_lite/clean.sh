#!/bin/bash

make ARCH=arm64 distclean
echo "delete ../out"
rm -rf ../out
echo "remove modules"
rm -rf ../emui/hi6250/rusty/system/lib/modules/*
rm -rf ../pa/hi6250/rusty/system/lib/modules/*

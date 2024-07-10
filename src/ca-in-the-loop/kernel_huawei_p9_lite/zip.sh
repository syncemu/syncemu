#!/bin/bash


device=hi6250
echo "Input ROM (emui/pa)"
read rom

echo "remove old modules"
rm -rf ../$rom/$device/rusty/system/lib/modules/*


if [ $rom = "emui" ]
then
	echo "Creating EMUI4.1 boot.img"
	
	cd ../$rom
	echo "rm boot.extracted"
	rm -rf boot.extracted

	echo "clean boot.extracted from boot.img"
	mkbootimg_tools/mkboot boot.img boot.extracted
	
	echo "place Image.gz"
	cp ../out/arch/arm64/boot/Image.gz boot.extracted/kernel
	
	echo "create bootnew.img"
	mkbootimg_tools/mkboot boot.extracted bootnew.img


#	make dtbs
#	mkbootimg_tools/dtbTool -s 2048 -o ../out/arch/arm64/boot/dt.img -p mkbootimg_tools/dtc/ ../out/arch/arm64/boot/dts/auto-generate


	echo "finding and placing modules"

		rm -f ${device}/rusty/system/lib/modules/*
		cd ../out
		find -name "*.ko" -exec cp -f '{}'  ../$rom/${device}/rusty/system/lib/modules/ \;


	echo "Copying image to root of unzipped directory renaming it boot."
	cd ../$rom
	cp bootnew.img ${device}/rusty/boot.img
	cd ${device}/rusty

	echo "Creating flashable zip."

	zip -r RustyKernel-EMUI4.1_${device}-$(date +%F).zip . -x ".*"

	echo "move zip to root folder"
	mv RustyKernel-EMUI4.1_${device}-$(date +%F).zip ../../../

	echo "remove ../out"
	cd ../../../
cd kernel

fi

if [ $rom = "pa" ]
then
	echo "Creating PA6.0.1 boot.img"
	
	cd ../$rom
	echo "rm boot.extracted"
	rm -rf boot.extracted

	echo "clean boot.extracted from boot.img"
	mkbootimg_tools/mkboot boot.img boot.extracted
	
	echo "place Image.gz"
	cp ../out/arch/arm64/boot/Image boot.extracted/kernel
	
	echo "create bootnew.img"
	mkbootimg_tools/mkboot boot.extracted bootnew.img


	
#	make dtbs
#	mkbootimg_tools/dtbToolCM -s 2048 -o ../out/arch/arm64/boot/dt.img -p mkbootimg_tools/dtc/ ../out/arch/arm64/boot/dts/auto-generate


	echo "finding and placing modules"

		rm -f ${device}/rusty/system/lib/modules/*
		cd ../out
		find -name "*.ko" -exec cp -f '{}'  ../$rom/${device}/rusty/system/lib/modules/ \;


	echo "Copying image to root of unzipped directory renaming it boot."
	cd ../$rom
	cp bootnew.img ${device}/rusty/boot.img
	cd ${device}/rusty

	echo "Creating flashable zip."

	zip -r RustyKernel-PA6.0.1_${device}-$(date +%F).zip . -x ".*"

	echo "move zip to root folder"
	mv RustyKernel-PA6.0.1_${device}-$(date +%F).zip ../../../

	echo "remove ../out"
	cd ../../../
cd kernel

fi

#	rm -rf ../out

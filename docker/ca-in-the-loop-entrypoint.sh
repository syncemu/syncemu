#!/usr/bin/env bash
TARGET=${1:-virt-optee}

if [ $TARGET == "virt-optee" ]; then
    # we start two QEMU machines in this demo
    QEMU_SERIAL_LOG_PHYS=/out/qemu_serial_phys.log
    QEMU_SERIAL_LOG_EMU=/out/qemu_serial_emu.log

    # start receiver of QEMU's serial output in the background
    cd /src/syncemu-rehosting/scripts/helpers;
    poetry run python qemu-serial-receiver.py 2000 2002 >$QEMU_SERIAL_LOG_EMU 2>&1 &

    cd /src/syncemu-rehosting/scripts/helpers;
    poetry run python qemu-serial-receiver.py 2004 >$QEMU_SERIAL_LOG_PHYS 2>&1 &

    # run the requested target in its rehosting environment
    cd /src/syncemu-rehosting/scripts/helpers/;

    poetry run python boot-$TARGET-nw.py /in/devicetree.dtb /in/$TARGET.bin /in/original/ --avatar-output-dir /out/
fi

if [ $TARGET == "p9lite-tc" ]; then
    # intended to compile Huawei P9lite's kernel that needs to be flashed on the physical smartphone
    cd /src/ca-in-the-loop/kernel_huawei_p9_lite && ./build.sh
fi

chown -R 1000:1000 /out
#!/usr/bin/env bash
TARGET=${1:-virt-optee}

QEMU_SERIAL_LOG=/out/qemu_serial.log

# start receiver of QEMU's serial output in the background
cd /src/syncemu-rehosting/scripts/helpers;
poetry run python qemu-serial-receiver.py 2000 2002 >$QEMU_SERIAL_LOG 2>&1 &

# run the requested target in its rehosting environment
cd /src/syncemu-rehosting/scripts/tzos-rehosting/;

if [ $TARGET == "p9lite-tc" ]; then
    # for TC we only need the image
    poetry run python boot-$TARGET.py /in/$TARGET.bin --avatar-output-dir /out/
fi

if [ $TARGET == "virt-optee" ]; then
    # for OP-TEE we need the devicetree, image, and TA binaries
    poetry run python boot-$TARGET.py /in/devicetree.dtb /in/$TARGET.bin /in/optee_ta/ --avatar-output-dir /out/
fi

chown -R 1000:1000 /out
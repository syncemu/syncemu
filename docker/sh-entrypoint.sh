#!/usr/bin/env bash

QEMU_SERIAL_LOG=/out/qemu_serial.log

# start receiver of QEMU's serial output in the background
cd /src/syncemu-rehosting/scripts/helpers;
poetry run python qemu-serial-receiver.py 2000 2002 >$QEMU_SERIAL_LOG 2>&1 &

cd /src/syncemu-rehosting/scripts/helpers;
poetry run python qemu-serial-receiver.py 2004 >$QEMU_SERIAL_LOG 2>&1 &
/bin/bash

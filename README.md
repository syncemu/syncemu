# SyncEmu
SyncEmu is a toolkit enabling rehosting of (proprietary) TrustZone OS binaries with a special focus on analyzing Trusted Applications. The main highlights are an extendable rehosting framework for running TrustZone OS and Trusted Applications binaries in an emulated environment and SyncEmu's CA-in-the-loop technique that allows synchronizing the execution of Trusted Applications with Client-Applications on a physically attached device.
Please have a look at our [SysTEX'24 paper](https://systex24.github.io/papers/systex24-final28.pdf) for more details.

## Requirements
We tested SyncEmu on Ubuntu 22.04 and require docker with the `compose` plugin to create and run containers.

Additionally, you may require TrustZone OS and Trusted Application binaries.
In our evaluation set, we used the open-source TEE implementation OP-TEE for the target [QEMUv8](https://optee.readthedocs.io/en/latest/building/devices/qemu.html#qemu-v8) and `version 4.2.0 (2024-04-12)`. 
We build OP-TEE with `CFG_CORE_DYN_SHM=n CFG_CORE_ASLR=n`.
As closed-source TEE, we included Huawei's TEE `TrustedCore` powering P9lite smartphones (`Release Version iCOS_MAIN_2.9.0_EVA_1.6, Nov  9 2016.18:32:24`).
We provide compiled binaries for OP-TEE, but you may have to extract TrustedCore's binary from a vendor update or directly from a rooted device.
Place the binaries in `in/TARGET`.

SyncEmu is build upon [avatar2](https://github.com/avatartwo) and avatar2's configurable machine provided in its QEMU fork.

## Building with Docker
We recommend building SyncEmu using our Dockerfile at `docker/Dockerfile`. We provide a `Makefile` that helps to build SyncEmu. You can build the container with `make build`.
If successful you may run `make run-sh` to spawn a shell in the docker container for testing. 


## SyncEmu's Rehosting Framework
You can find the source code in `src/syncemu-rehosting`. Scripts to start a rehosted TZOS binary can be found in `src/scripts/tzos-rehosting`.
We provide a make target to start a rehosted TZOS in its rehosting environment.
For example, you may run `make run-rehost TARGET=virt-optee` to boot up OP-TEE.
You can find the rehosting environments in `src/syncemu-rehosting/common/avatar2/convenience/TARGET`.
You may add a new TZOS target by implementing the necessary dependencies (minimal bootloader, peripheral callbacks, and secure monitor callbacks).

For output look into `out/TARGET`.
| File | Description |
| :--- | :--- |
| `boot.bin` | Minimal bootloader placed into memory. That's the first code being executed. Do not edit manually. |
| `qemu_conf.json` | Generated config file passed to avatar2's configurable machine in QEMU. Do not edit manually. |
| `qemu_err.txt` | Logging output of rehosted target's execution by QEMU. Highly interesting during iterative refinement for analyzing crashes. |
| `qemu.log` | Meta log output. |
| `qemu_out.txt` | Logging output of configurable machine in QEMU. If avatar2 has problems starting QEMU you may find error messages here. |
| `qemu_serial.log` | Serial output of rehosted target if serial device correctly installed. Highly interesting during iterative refinement for analyzing crashes. |

## CA-in-the-loop
SyncEmu's CA-in-the-loop technique requires a physical device for forwarding requests of Client Applications running on a physical device to Trusted Applications running in the rehosting environment. For OP-TEE we provide a proof-of-concept using two emulated devices.

### Demo with OP-TEE and QEMU's virt machine

For showcasing SyncEmu's CA-in-the-loop technique without the need for a physical device, we implemented a proof-of-concept using OP-TEE running in QEMU's virt machine instead.
You can start this experiment with `make run-ca-in-the-loop TARGET=virt-optee`.
This will (1) start a first instance of only OP-TEE OS in a rehosted environment, (2) start a second instance of OP-TEE with Linux in QEMU's virt machine mimicing the physical device, and (3) forward CA requests send by the virt machine to the rehosted OP-TEE instance.

Detailed commands:
```
make run-ca-in-the-loop
# Wait until you see "Port 2003: Connect serial for physical device normal world..."

# spawn a second terminal and attach to docker container and spawn a shell
docker exec -it "containername" /bin/bash

# connect to virt machine serial port 2003 via netcat
nc localhost 2003

# press enter in the first terminal, booting both the rehosted and physical instance
# you can use the "physical" instance via the second terminal and execute CAs
# e.g., execute /usr/bin/optee_example_hello_world
```
With updating SyncEmu to a newer OP-TEE version, the loading process for CAs is currently not working. This is a known issue and we work on a fix.

### Huawei P9lite smartphone

In this scenario we provide details on how to get SyncEmu's ca-in-the-loop technique running with a real-world smartphone.
You may find the modified kernel for a Huawei P9lite smartphone at `src/ca-in-the-loop/kernel_huawei_p9_lite`.
Our changes are described in `src/ca-in-the-loop/kernel_huawei_p9_lite/drivers/hisi/smc_forwarder/README.md`.
When running `make run-ca-in-the-loop TARGET=p9lite-tc`, the kernel will be compiled and ready to be flashed on a rooted device. Then follow these steps:

1. Make sure no adb server is running on the host machine -> `adb kill-server`
2. Run docker container in privileged mode with `make run-connect-device TARGET=p9lite-tc`
3. Inside the container the compiled Linux kernel can be found at `/src/ca-in-the-loop/kernel_huawei_p9_lite/out/arch/arm64/boot/Image.gz` which must be flashed onto the physical connected device.
4. Make a backup of the physical device's Image by using a custom recovery (e.g., [TWRP](https://twrp.me/)).
5. Inject the compiled kernel from docker into the backup partition `boot.emmc.win` by using `abootimg -u boot.emmc.win -k <path_to_new_kernel>/Image.gz`
6. Reboot the device into recovery mode `adb reboot recovery` and transfer backup with injected kernel `adb push <backup_file> /data/media/0/TWRP/BACKUPS/VNS/`
7. In the TWRP recovery choose to restore the now pushed backup. Then reboot the device.
8. Inside the container in directory run `cd /src/syncemu-rehosting/ && poetry run python scripts/helpers/qemu-serial-receiver.py 2000 2002 | tee /out/emulator_uart`. This will initalize the uart output of the rehosted TZOS.
9. Check that an adb session can be established from the container by running `adb devices`
10. If problem occur concerning adb try to kill the adb server in the container and retry and check if a dialogue on the device poped up.
11. Open another terminal inside docker (or put the qemu-serial-receiver in background) and run `cd /src/syncemu-rehosting/ && poetry run python scripts/tzos-rehosting/boot-p9lite-tc.py /in/p9lite-tc.bin --ca_in_the_loop on --avatar-output-dir /out/` to start TrustedCore in the rehosting environment.
12. Use the physical device to trigger an SMC (e.g. Unlock, Fingerprint, App,...)

As results you will find output files in `out`. For example, `smc_history` holds all received, executed and returning SMCs with all their payload. In `smc_compare.csv` a table with all SMCs executed, forwarded on the physical device and emulator with additional comparison can be found. In `emulator_uart` the output of the emulator should be written.
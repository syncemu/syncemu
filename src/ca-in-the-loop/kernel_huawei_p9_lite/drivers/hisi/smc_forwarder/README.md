# SMC forwarding kernel module for huaweip9_hisi_kernel_driver

Includes the directory `<kernelbase>/drivers/hisi/`
Especially the tzdriver (TEE Driver) is part of it

added files are in directory `<kernelbase>/drivers/hisi/smc_forwarder`

## How-To build/add module to driver/kernel

- create Makefile in smc_forwarder directory with `obj-y	+= smc_forwarder.o`
- add smc_forwarder directory to driver Makefile `<kernelbase>/drivers/hisi/Makefile` with `obj-y += smc_forwarder/`
- For building pick correct compiler by setting `export PATH=<pathtotoolchains>/aarch64-linux-android-4.9/bin:$PATH` and `export CROSS_COMPILE=aarch64-linux-android-`
- run configure (needs to be done only once) `make ARCH=arm64 O=./out hisi_6250_defconfig`
- compile `make ARCH=arm64 O=./out V=1 -j10`
- inject compiled kernel into a backup image by using abootimg -u boot.emmc.win -k `<kernelbase/out/arch/arm64/boot/Image.gz>`
- push backup img on device with `adb push <backup_folder> /data/media/0/TWRP/BACKUPS/VNS/`
- boot into TWRP recovery and restore pushed backup image

## How it works

The main goal of this module is to enable the synchronized execution the TZOS of a real device (Huawei P9 lite) with a rehosted TZOS in an emulator (QEMU with avatar2).
For that, we need to implement a an SMC forwarding mechanism running inside the NW-kernel:
SMC forwarding (for NW data) - capability to observe/record/manipulate SMC data sent between NW and SW at N-EL1 to EL3 on the device.

The smc_forwarder.c registers a device with proc-entry at `/proc/smc_forwarder` which can be interacted with by reading/writing from/to it.

### SMC forwarding
The goal of smc_forwarder is to enable observation and injection of data which is part of SMCs executed from N-EL1. Data which is exchanged between kernel and TZOS can be divided between data which is part of a `smc_cmd struct` and additional data like `parameters` which can be present. For synchronization both need to be forwarded. The module offers two functions which can be added to the tzdriver source at any point:

- `int smc_write_out(TC_NS_SMC_CMD *smc_cmd)`
    Can be called at any point in the tzdriver. The given smc_cmd will be recorded/saved in a queue. From the queue can be read by accessing `proc/smcforwarder`.
    By calling this function in `smc_send_func` of the file `smc.c` all SMCs done during execution will be saved to an internal smc_ring_buffer. In that way every smc_cmd_struct with its additional data is recorded and saved until it gets read.

- `TC_NS_SMC_CMD *smc_read_in(TC_NS_SMC_CMD *smc_cmd)`
    Can be called at any point in the tzdriver. The execution of SMCs will pause depending on the `smc_exec_status` value. If `smc_exec_status == 0` we run in normal mode, else if `smc_exec_status == 1` the function blocks, so no SMCs will get executed. The given smc_cmd (TODO: changed in code) can be manipulated/changed to values returning from a rehosted TZOS running in an emulator. By writing to `proc/smc_forwarder` the `smc_exec_status` can be changed.
    (TODO: maybe this function could be divided into two: one only for read_in smc data and the other as "sync_barrier"/"smc_pause" function that only halts execution depending on smc_exec_status)

In TrustedCore powering the HuaweiP9 lite, a struct called `TC_NS_SMC_CMD` is used to set up memory for interaction between the kernel and the TZOS. During execution `smc_forwarder` saves every SMC data sent by the kernel to memory by using a ring buffer. This is done by allocating memory with `kmalloc` and `__get_free_pages`. Depending on the `TEEC_ParamType` the `TC_Operation` contains different data. To save SMCs send from NW to SW, parameter with type `TEEC_VALUE_INPUT, TEEC_VALUE_INOUT, TEEC_MEMREF_TEMP_INPUT, TEEC_MEMREF_TEMP_INOUT` need to be saved.
If reading from `/proc/smc_forwarder` the ring buffer gets returned depending on a value pointing to the current SMCs to be read. The send data has the following structure:
```
SMC_START
uuid:<17 byte as hexstring>,uuid_phys:<4 byte address>,cmd_id:<hex_int>,dev_file:<hex_int>,context_id:<hex_int>,agent_id:<hex_int>,operation_phys:<hex_int>,operation_paramTypes:<hex_int>,login_method:<hex_int>,login_data:<hex_int>,err_origin:<hex_int>,ret_val:<hex_int>,event_nr:<hex_int>,remap:<hex_int>,uid:<hex_int>,started:<hex_int>
# up to four parameters (x is 0-3) containing value or buffer
param_<x>:size:<hex_int>,buffer:<hexstring>
param_<x>:value_a:<hex_int>,value_b:<hex_int>
SMC_END
```
The data can be parsed and then injected into a qemu-emulator.
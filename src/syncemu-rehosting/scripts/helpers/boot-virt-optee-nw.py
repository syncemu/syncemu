import subprocess
import threading

# The TargetLauncher is ripped from the avatar1-example
# It is used to spawn and stop a qemu instance which is independent of avatar2.
from typing import NamedTuple, Optional

import click
from avatar2 import ARM, QemuTarget, os, GDBTarget, sys

from common.avatar2.convenience.optee.optee_boot_patcher import OpteeBootPatcher
from common import install_logging
from common.avatar2.convenience import ConvenientAvatar
from common.avatar2.convenience.optee.factories import OpteeQemuv8AvatarFactory
from common.avatar2.convenience.optee.optee_secure_monitor_forwarder import OpteeSecureMonitorForwarder
from common.avatar2.convenience import BreakpointHandlingRunner

class TargetLauncher(object):
    def __init__(self, cmd):
        self._cmd = cmd
        print(' '.join(cmd))
        self._process = None
        self._thread = threading.Thread(target=self.run)
        self._thread.start()

    def stop(self):
        if self._process:
            print(self._process.kill())

    def run(self):
        print("TargetLauncher is starting process %s" %
              " ".join(['"%s"' % x for x in self._cmd]))
        self._process = subprocess.Popen(self._cmd)

def get_sync_runner(avatar: ConvenientAvatar, rehost_runner: BreakpointHandlingRunner, gdb_target: GDBTarget):
    # the SMC calls seem to always end up in the following address, by default (at least in OP-TEE)
    # in order to react properly to SMCs, we map some memory there, and pass it to the runner
    # this way, the runner can write custom code into that section
    # TODO: this adress can apparently be configured by the secure monitor, maybe we should do so to make sure we
    #    don't influence whatever else the caller might want to do with the target
    smc_emulator_hook = 0x400 # TODO: change this if other binary

    # also for the NW physical device we need a hook address
    # here we take an address where the first instruction in EL3 right after the SMC is
    smc_physical_device_hook = 0x0e101788 # TODO: change this if other binary
    # here it is "__thread_std_smc_entry"
    
    # note: we seem to have to set up the shared memory here, before the SMC handler stub is created
    # FIXME: investigate why this is the case
    runner = OpteeSecureMonitorForwarder(
        avatar,
        rehost_runner,
        gdb_target,
        smc_emulator_hook,
        smc_physical_device_hook,
        0x42000000,
        avatar.output_directory,
    )

    return runner

@click.command()
@click.argument("dtb_path")
@click.argument("bl32_path")
@click.argument("qemu_optee_dir_path")
@click.option("--avatar-output-dir", type=click.Path(exists=False))
def main(dtb_path, bl32_path, qemu_optee_dir_path , avatar_output_dir):
    # hide spam of avatar2, pygdbmi and all that stuff
    # also, set up some colors, which make reading logs a lot easier
    # note that we intentionally disable avatar2's own logging below, as it conflicts with this setup
    # most likely, the avatar2 logging configuration is flawed, since it causes issues with our own logging
    install_logging()

    if avatar_output_dir:
        print("Using output dir {} with avatar2".format(avatar_output_dir), file=sys.stderr)

        # create directory if it doesn't exist
        # that saves the user from creating it beforehand
        os.makedirs(avatar_output_dir, exist_ok=True)

    # setup runner for rehosted optee - "emulator"
    factory = OpteeQemuv8AvatarFactory()
    # we pass None as trusted_apps_dir indicating that no shared memory should be mapped
    context = factory.get_rehosting_context(dtb_path, bl32_path, None, avatar_output_dir=avatar_output_dir)
    rehost_runner = BreakpointHandlingRunner(context.target)
    boot_patcher = OpteeBootPatcher(context)
    rehost_runner.register_handler(boot_patcher)

    # setup runner for original optee - "physical device"
    os.chdir(qemu_optee_dir_path)
    # next step is to boot up a normal world optee which is the physical device

    """
qemu-system-aarch64 -machine virt,secure=on,gic-version=3 -cpu cortex-a57 -m 1057 -smp 2 -netdev user,id=eth0 -device virtio-net-device,netdev=eth0 -bios bl1.bin -gdb tcp:127.0.0.1:1234 -serial tcp:127.0.0.1:2003,server,nowait -serial tcp:127.0.0.1:2004 -kernel Image -no-acpi -S -d exec,cpu_reset,guest_errors,int,cpu,in_asm,mmu -D /out/qemu_physical.log -semihosting-config enable,target=native -nographic -monitor telnet:127.0.0.1:2005,server,nowait -initrd rootfs.cpio.gz
    """

    target_runner = TargetLauncher(["qemu-system-aarch64",
                                    "-machine",  "virt,secure=on,gic-version=3",
                                    "-cpu", "cortex-a57",
                                    "-m", "1057",
                                    "-smp", "2",
                                    "-bios", "bl1.bin",
                                    "-gdb", "tcp:127.0.0.1:1234",
                                    "-serial","tcp:127.0.0.1:2003,server,nowait",
                                    "-serial","tcp:127.0.0.1:2004",
                                    "-kernel", "Image",
                                    "-no-acpi",
                                    "-S",
                                    "-d", "unimp", # ,in_asm,cpu
                                    "-D", "/out/qemu_physical.log",
                                    "-semihosting-config", "enable,target=native",
                                    "-nographic",
                                    "-monitor", "telnet:127.0.0.1:2005,server,nowait",
                                    "-initrd", "rootfs.cpio.gz"
                                    ])
    gdb_target = context.avatar.add_target(GDBTarget, gdb_port=1234)

    sync_runner = get_sync_runner(context.avatar, rehost_runner, gdb_target)


    context.avatar.init_targets()
    input("Port 2003: Connect serial for physical device normal world...")
    
    while True:
        # return emulator with optee TZOS
        sync_runner.cont_emulator()
        print("World Switch SW -> NW")

        # return the physical device with NW
        sync_runner.cont_physical_device()
        print("World Switch NW -> SW")
    

if __name__ == "__main__":
    main()
import os
from typing import Optional

from avatar2 import AARCH64, Target

from .optee_boot_patcher import OpteeBootPatcher
from .optee_tee_driver_emulator import OpteeTeeDriverEmulator
from .optee_call_into_tzos_strategy import OpteeCallIntoTzosStrategy
from ..secure_monitor_emulator import SecureMonitorEmulator
from ..target_bridge import TargetBridge, DefaultTargetBridge
from ..tzos_runner import TzosRunner
from ... import ConvenientAvatar
from .. import BreakpointHandlingRunner, TemporaryCodeExecutionHelper
from ..avatar_factory_memory_mapping import AvatarFactoryMemoryMapping
from ..rehosting_context import RehostingContext
from ...keystone import aarch64_asm


class OpteeAvatarFactory:
    """
    Abstract factory.
    """

    def __init__(self):
        # default values for factory methods

        # can be optionally set by concrete factories
        # avatar-qemu otherwise falls back to a default value
        self._avatar_cpu: Optional[str] = None

        # some randomly chosen value that appears to be outside any of the other memory ranges
        self._entry_address = 0xABCDEF00

        # memory mappings
        # most of these must be provided by concrete factories, as they vary across the builds
        self._secure_mem: Optional[AvatarFactoryMemoryMapping] = None
        self._tee_ram: Optional[AvatarFactoryMemoryMapping] = None
        self._ta_ram: Optional[AvatarFactoryMemoryMapping] = None
        self._nw_ram: Optional[AvatarFactoryMemoryMapping] = None
        self._nsec_shared_memory: Optional[AvatarFactoryMemoryMapping] = None

        # the SMC calls seem to always end up in the following address, by default (at least in OP-TEE)
        # in order to react properly to SMCs, we map some memory there, and pass it to the runner
        # this way, the runner can write custom code into that section
        # TODO: this adress can apparently be configured by the secure monitor, maybe we should do so to make sure we
        #    don't influence whatever else the caller might want to do with the target
        self._smc_entrypoint_address = 0x400

    def _add_minimal_optee_bootloader(self, avatar: ConvenientAvatar):
        # TODO: actually, we'd like to avoid using a tempfile, but rather mount some avatar2 peripheral instead
        # however, this doesn't work at the moment, and avatar2 doesn't tell us why

        bootloader_code = f"""
            mov x1, #0x3c5
            mov x0, #{hex(self._tee_ram.address)}
            msr spsr_el3, x1
            msr elr_el3, x0
            mov x1, #0x30cd
            lsl x1, x1, #16
            mov x2, #0x183f
            orr x1,x1,x2
            and x1, x1, #0xfffffffffffffffe
            msr sctlr_el3, x1
            mov x1, 0xe30
            msr scr_el3, x1
            mov x0, #{hex(self._ta_ram.address)}
            mov x1, 0x0
            mov x2, #{hex(self._nw_ram.address)}
            eret
        """

        boot_bin_path = os.path.join(avatar.output_directory, "boot.bin")

        with open(boot_bin_path, "wb") as f:
            f.write(aarch64_asm(bootloader_code))

        return avatar.add_memory_range(self._entry_address, 0x00001000, name="bootloader_stub", file=boot_bin_path)

    def _add_serial_devices(self, avatar: ConvenientAvatar):
        """
        Should be provided by concrete factories.
        """

        raise NotImplementedError()

    def _create_target_bridge(self, target: Target) -> TargetBridge:
        """
        Should be provided by concrete factories.
        """

        raise NotImplementedError()

    def get_rehosting_context(
        self, dtb_path: str, bl32_path: str, trusted_apps_dir: str, avatar_output_dir: str = None
    ):
        # as it can be quite cumbersome to work with the auto-generated temporary directories in order to get the logs
        # of QEMU and other subprocesses, we allow the user to specify their own path
        # if it is not provided, avatar_output_dir will be None, and thus an auto-generated tempdir will be used
        avatar = ConvenientAvatar(
            arch=AARCH64, output_directory=avatar_output_dir, log_to_stdout=False, cpu_model=self._avatar_cpu
        )

        # this should be the same for all possible boards
        # the entry address can be overwritten as a member variable
        # enabling semihosting should not cause issues even if it isn't needed, so we enable it always
        qemu_target = avatar.add_qemu_target(self._entry_address, enable_semihosting=True)

        # map TZOS aka bl32 into memory
        avatar.add_memory_range(self._tee_ram.address, self._tee_ram.size, name="tee_ram", file=bl32_path)

        # set up TA ram (TAs will be loaded into this memory range)
        avatar.add_memory_range(self._ta_ram.address, self._ta_ram.size, name="ta_ram")

        # hook up serial devices
        # this is typically very device-specific, so we'll leave that to concrete factory implementations
        self._add_serial_devices(avatar)

        # add normal world RAM
        # a device tree is expected to be available in this location, otherwise the TZOS won't boot w/o any serial
        # output
        avatar.add_memory_range(self._nw_ram.address, self._nw_ram.size, name="nw_ram", file=dtb_path)

        # in this range, the TZOS can allocate shared memory via a TEE driver RPC
        # this memory is then used to pass data between TA (SW) and CA (NW)
        shared_memory = None
        if trusted_apps_dir is not None:
            shared_memory = avatar.add_in_memory_buffer_peripheral(
                self._nsec_shared_memory.address, self._nsec_shared_memory.size, name="nsec_shared_memory", permissions="rw"
            )

        # load bootloader stub last -- this should ensure that, wherever we map it, the stub is ensured to be available
        # there, even if any other memory range was mapped before in that range
        self._add_minimal_optee_bootloader(avatar)

        # add ARM global interrupt controller
        # might be used later on when interfacing with real hardware, right now it doesn't bring us any further
        # SMCs are "synchronous exceptions", i.e., they're not using interrupts
        # instead the CPU jumps to some address defined in a register to handle the call
        # avatar.add_arm_gic_v2()

        # note: this memory range must be large enough for all potential code you'd want to put in there
        avatar.add_memory_range(self._smc_entrypoint_address, 0x10000, permissions="rx", name="smc_handler_stub")
        # we create some "shared memory" which we use to pass information to SMC calls that interact with trusted apps
        # the address was chosen arbitrarily; it just has to be in some range that isn't occupied otherwise
        # TODO: actually check that there's no such range yet, perhaps even in add_in_memory_buffer_peripheral(...)
        # the size was chosen arbitrarily, too; just has to be large enough for everything we plan to put in there
        # make memory bigger so we can allocate requested shared memory for TZOS
        #shared_memory = avatar.add_in_memory_buffer_peripheral(
        #    0x7D9A1000, 0x1000000, name="shared_mem", permissions="rw"
        #)

        # used to conveniently run some assembler code in a separate memory region
        # we can just put that directly after the other range
        temporary_code_execution_helper = None
        if shared_memory is not None:
            temporary_code_execution_helper = TemporaryCodeExecutionHelper(
                qemu_target, avatar, (shared_memory.address + shared_memory.size), 0x10000
            )

        target_bridge = self._create_target_bridge(qemu_target)

        rehosting_context = RehostingContext(
            avatar,
            qemu_target,
            self._smc_entrypoint_address,
            shared_memory,
            temporary_code_execution_helper,
            target_bridge,
            0x600003C4,
            0xBE000000,
            0xBE000005,
            nsec_shared_memory_address=self._nsec_shared_memory.address,
            trusted_apps_dir=trusted_apps_dir,
        )

        return rehosting_context

    def get_runner(self, rehosting_context: RehostingContext):
        runner = BreakpointHandlingRunner(rehosting_context.target)

        boot_patcher = OpteeBootPatcher(rehosting_context)
        runner.register_handler(boot_patcher)

        tee_driver_emulator = OpteeTeeDriverEmulator(
            rehosting_context.target,
            rehosting_context.nsec_shared_memory_address,
            rehosting_context.trusted_apps_dir,
            rehosting_context.avatar.output_directory,
        )

        tzos_execution_strategy = OpteeCallIntoTzosStrategy(rehosting_context)

        sm_emulator = SecureMonitorEmulator(rehosting_context, tee_driver_emulator, tzos_execution_strategy)
        runner.register_handler(sm_emulator)

        tzos_runner = TzosRunner(runner, tzos_execution_strategy)

        return tzos_runner


class OpteeQemuv8AvatarFactory(OpteeAvatarFactory):
    def __init__(self):
        super().__init__()

        self._tee_ram = AvatarFactoryMemoryMapping(0xE100000, 0x200000)
        self._ta_ram = AvatarFactoryMemoryMapping(0xE300000, 0xD00000)
        self._nw_ram = AvatarFactoryMemoryMapping(0x40000000, 0x2000000)
        self._nsec_shared_memory = AvatarFactoryMemoryMapping(0x42000000, 0x200000)

    def _add_serial_devices(self, avatar: ConvenientAvatar):
        avatar.add_memory_range(0x08000000, 0x01000000, name="gic")
        
        avatar.add_pl011(0x09000000, 0x00001000, "uart", 0)
        avatar.add_pl011(0x09040000, 0x00001000, "secure_uart", 1)

    def _create_target_bridge(self, target: Target) -> TargetBridge:
        return DefaultTargetBridge(target)


class OpteeHiKey620AvatarFactory(OpteeAvatarFactory):
    def __init__(self):
        super().__init__()

        self._tee_ram = AvatarFactoryMemoryMapping(0x3F000000, 0x200000)
        self._ta_ram = AvatarFactoryMemoryMapping(0x3F200000, 0xE00000)
        self._nw_ram = AvatarFactoryMemoryMapping(0x40000000, 0x10000000)
        self._nsec_shared_memory = AvatarFactoryMemoryMapping(0x3EE00000, 0x200000)

    def _add_serial_devices(self, avatar: ConvenientAvatar):
        # this is IO_NSEC in there are uart mapped
        avatar.add_memory_range(0xF8000000, 0x00200000, name="io_nsec")
        avatar.add_memory_range(0xF7000000, 0x00200000, name="io_nsec_1")

        # for the hikey board it seems like we only have one uart output (default is 3 which is mapped at that address)
        # this is PL011_UART3_BASE (the default build value)
        avatar.add_pl011(0xF7113000, 0x00001000, "secure_uart", 1)

    def _create_target_bridge(self, target: Target) -> TargetBridge:
        return DefaultTargetBridge(target)

import os
from typing import Optional, NamedTuple

from avatar2 import AARCH64, Target

from .trustedcore_boot_patcher import TrustedCoreBootPatcher
from .trustedcore_call_into_tzos_strategy import TrustedCoreCallIntoTzosStrategy
from .trustedcore_exception_handler import TrustedCoreExceptionHandler
from .trustedcore_exception_interpreter import TrustedCoreExceptionInterpreter
from .trustedcore_progress_monitor import TrustedCoreProgressMonitor
from .trustedcore_tee_driver_emulator import TrustedCoreTeeDriverEmulator
from ..tzos_runner import TzosRunner
from ..colored_register_printer import ColoredRegistersPrinter
from ..secure_monitor_emulator import SecureMonitorEmulator
from ... import ConvenientAvatar
from .. import BreakpointHandlingRunner, TemporaryCodeExecutionHelper
from ..avatar_factory_memory_mapping import AvatarFactoryMemoryMapping
from ..rehosting_context import RehostingContext
from ..target_bridge import AArch64Compat32TargetBridge
from ...keystone import aarch64_asm


class TrustedCoreAvatarFactory:
    """
    Abstract factory.
    """

    def __init__(self):
        # can be optionally set by concrete factories
        # avatar-qemu otherwise falls back to a default value
        self._avatar_cpu: Optional[str] = None

        # some randomly chosen value that appears to be outside any of the other memory ranges
        self._entry_address = 0xABCDEF00
        # TODO: snapshot not part of code?
        # as we directly inject snapshot now we do not need to use bootloader code
        # self._entry_address = 0x600

        # memory mappings
        # most of these must be provided by concrete factories, as they vary across the builds
        self._secure_mem: Optional[AvatarFactoryMemoryMapping] = None

        # location into which the TZOS parts shall be mapped (namely, Rtosck, globaltask and the tasks)
        # realized by writing a temp file of that size, containing the files at the right offsets
        self._teeos: Optional[AvatarFactoryMemoryMapping] = None

        self._ta_ram: Optional[AvatarFactoryMemoryMapping] = None
        self._nw_ram: Optional[AvatarFactoryMemoryMapping] = None

        self._tzos_start_address = 0x36208000

        self._smc_entrypoint_address = 0x600

    def _add_serial_devices(self, avatar: ConvenientAvatar):
        """
        Should be provided by concrete factories.
        """

        raise NotImplementedError()

    def _create_target_bridge(self, target: Target):
        """
        Should be provided by concrete factories.
        """

        raise NotImplementedError()

    def _create_mappable_file_from_teeos(self, output_file: str, teeos_dump_path: str):
        class FileToMemoryMapping(NamedTuple):
            file_offset: int
            memory_offset: int
            bytes_to_copy: Optional[int]

        # this list allows mapping sections from the teeos image into a ca. 30 MiB
        mappings = [
            # Rtosck (TZOS)
            FileToMemoryMapping(0x400, 0x8000, 0x7ED24),
            # "tasks directory"
            FileToMemoryMapping(0x0, 0xD00000, 0x400),
            # remainder of the teeos partition (i.e., everything after the Rtosck) including globaltask and the other
            # tasks
            FileToMemoryMapping(0x7F124, 0xD00400, None),
        ]

        # sorting by memory offset allows us to more easily write the output file below
        mappings.sort(key=lambda mapping: mapping.memory_offset)

        with open(output_file, "wb") as of:

            def write_padding(length: int, char: bytes = b"\x00"):
                """
                Little helper that efficiently writes larger sections of padding by operating chunk wise.
                """

                chunk_size = 0x1000
                chunks = length // chunk_size
                remainder = length % chunk_size

                chunk_data = b"".join([char for _ in range(chunk_size)])

                for i in range(chunks):
                    of.write(chunk_data)

                if remainder > 0:
                    of.write(b"".join([b"\x00" for _ in range(remainder)]))

            with open(teeos_dump_path, "rb") as teeos:
                for mapping in mappings:
                    # insert leading padding
                    current_offset = of.tell()
                    leading_padding_size = mapping.memory_offset - current_offset
                    # of.write(b"".join([b"\x00" for i in range(leading_padding_size)]))
                    write_padding(leading_padding_size)

                    assert of.tell() == current_offset + leading_padding_size

                    # insert data from teeos image
                    teeos.seek(mapping.file_offset, os.SEEK_SET)

                    if mapping.bytes_to_copy is not None:
                        data = teeos.read(mapping.bytes_to_copy)
                        assert len(data) >= mapping.bytes_to_copy
                    else:
                        data = teeos.read()

                    of.write(data)

                    if mapping.bytes_to_copy is not None:
                        assert of.tell() == current_offset + leading_padding_size + mapping.bytes_to_copy

            # write tailing padding
            current_offset = of.tell()
            trailing_padding_size = self._teeos.size - current_offset
            write_padding(trailing_padding_size)

            # make sure output file has the expected size
            of.seek(0, os.SEEK_END)
            assert of.tell() == self._teeos.size

    def _add_minimal_bootloader(self, avatar: ConvenientAvatar, tzos_address: int):
        # TODO: actually, we'd like to avoid using a tempfile, but rather mount some avatar2 peripheral instead
        # however, this doesn't work at the moment, and avatar2 doesn't tell us why

        bootloader_code = f"""
            # we got this value from robert
            mov x1, #0xC0
            lsl x1,x1, #0x10
            movk x1, #0x818
            msr sctlr_el1, x1

            # we dont need to set any bit, especially [10] must be 0 for aarch32
            mov x1, 0x0
            msr scr_el3, x1

            # set ELR_EL3 to entry address of TZOS image
            mov x0, #{hex(tzos_address)[:6]}
            lsl x0, x0, #0x10
            movk x0, #0x{hex(tzos_address)[6:]}
            msr elr_el3, x0

            # M[3:0] = 0011 for supervisor (=EL1) and M[4] = 1 for aarch32
            # bit 8, 7, 6 set for interrupt mask
            mov x1, #0x1D3
            msr spsr_el3, x1  

            # still from optee boot information -> might need to be changed for huawei
            # x0 is TA_RAM
            mov x0, #{hex(self._ta_ram.address)[:6]}
            lsl x0, x0, #0x10
            movk x0, #0x{hex(self._ta_ram.address)[6:]}

            # x1 must be zero (its part of the RAM address?)
            mov x1, 0x0

            # x2 to NW_RAM
            mov x2, #{hex(self._nw_ram.address)}

            # eret will restore spsr_el3 -> cpsr and elr_el3 -> pc
            eret
        """

        boot_bin_path = os.path.join(avatar.output_directory, "boot.bin")

        with open(boot_bin_path, "wb") as f:
            f.write(aarch64_asm(bootloader_code))

        return avatar.add_memory_range(self._entry_address, 0x00001000, name="bootloader_stub", file=boot_bin_path)

    def get_rehosting_context(self, teeos_dump_path: str, avatar_output_dir: str = None):
        # as it can be quite cumbersome to work with the auto-generated temporary directories in order to get the logs
        # of QEMU and other subprocesses, we allow the user to specify their own path
        # if it is not provided, avatar_output_dir will be None, and thus an auto-generated tempdir will be used
        avatar = ConvenientAvatar(
            arch=AARCH64, output_directory=avatar_output_dir, log_to_stdout=False, cpu_model=self._avatar_cpu
        )

        # this should be the same for all possible boards
        # the entry address can be overwritten as a member variable
        # enabling semihosting should not cause issues even if it isn't needed, so we enable it always
        qemu_target = avatar.add_qemu_target(
            self._entry_address,
            enable_semihosting=True,
            additional_args=[
                "-d",
                "cpu_reset,guest_errors,int,cpu,in_asm,mmu",
            ],
        )

        # the TEEOS components are mapped by the bootloader from a partition called teeos, which can be dumped on the
        # phone
        # the layout is a bit special and not page-aligned, therefore we can't simply use avatar2's
        # file_offset/file_bytes parameters to create the mapping
        # to solve the issue, we write a larger (~ 30 MiB) temp file that contains sections of the teeos partition at
        # the correct offsets, which are currently hardcoded in the helper function
        # start address and total size of the section are defined by the actual factory
        output_file = os.path.join(avatar.output_directory, "teeos.img")
        self._create_mappable_file_from_teeos(output_file, teeos_dump_path)
        avatar.add_memory_range(self._teeos.address, self._teeos.size, name="teeos", file=output_file)

        # set up TA ram (TAs will be loaded into this memory range)
        avatar.add_memory_range(self._ta_ram.address, self._ta_ram.size, name="ta_ram")

        # hook up serial devices
        # this is typically very device-specific, so we'll leave that to concrete factory implementations
        self._add_serial_devices(avatar)

        # load bootloader stub last -- this should ensure that, wherever we map it, the stub is ensured to be available
        # there, even if any other memory range was mapped before in that range
        self._add_minimal_bootloader(avatar, self._tzos_start_address)

        # note: this memory range must be large enough for all potential code you'd want to put in there
        avatar.add_memory_range(self._smc_entrypoint_address, 0x10000, permissions="rx", name="smc_handler_stub")

        # added as a snapshot wanted to access these regions
        # add from 0x34000000 - 0x36200000
        #avatar.add_memory_range(0x34000000, 0x2200000, name="test_snapshot")

        # other memory
        avatar.add_memory_range(0x38000000, 0x6D000000, name="range0")
        # our bootloader stub is located at 0xABCDE000
        avatar.add_memory_range(0xAC000000, 0x33000000, name="range1")
        avatar.add_memory_range(0xE1100000, 0x1F000000, name="range2")

        # memory 0xF0000000 - 0xFFFFFFFF
        # 0xF0000000 - 0xFDF02000
        avatar.add_memory_range(0xF0000000, 0xDF02000, name="range3")

        avatar.add_memory_range(0xFDF03000, 0x202F000, name="range4")
        avatar.add_memory_range(0xFFF33000, 0xCD000, name="range5")

        # TODO: check if necessary
        # 0xFDF02000 - 0xFDF03000 uart
        # 0xFDF03000 - 0xFF100000 memory for crypto cell 0xff011f08
        #avatar.add_in_memory_buffer_peripheral(0xFDF03000, 0x11FD000, "crypto_cell")
        # 0xFF100000 - 0xFFF32000
        #avatar.add_memory_range(0xFF100000, 0xE32000, name="test4")
        # 0xFFF32000 - 0xFFF33000 secure uart
        #avatar.add_memory_range(0xFFF33000, 0xCD000, name="test5")

        # we create some "shared memory" which we use to pass information to SMC calls that interact with trusted apps
        # the address was chosen arbitrarily; it just has to be in some range that isn't occupied otherwise
        # TODO: actually check that there's no such range yet, perhaps even in add_in_memory_buffer_peripheral(...)
        # the size was chosen arbitrarily, too; just has to be large enough for everything we plan to put in there
        # make memory bigger so we can allocate requested shared memory for TZOS
        shared_memory = avatar.add_in_memory_buffer_peripheral(
            0xE0000000, 0x1000000, name="shared_mem", permissions="rw"
        )

        # used to conveniently run some assembler code in a separate memory region
        # we can just put that directly after the other range
        temporary_code_execution_helper = TemporaryCodeExecutionHelper(
            qemu_target, avatar, (shared_memory.address + shared_memory.size), 0x10000
        )

        target_bridge = self._create_target_bridge(qemu_target)

        colored_register_printer = ColoredRegistersPrinter(target_bridge)

        rehosting_context = RehostingContext(
            avatar,
            qemu_target,
            self._smc_entrypoint_address,
            shared_memory,
            temporary_code_execution_helper,
            target_bridge,
            0x20000113,
            0xB2000000,
            0xB2000009,
            colored_register_printer=colored_register_printer,
        )

        return rehosting_context

    def get_runner(self, rehosting_context: RehostingContext):
        runner = BreakpointHandlingRunner(rehosting_context.target)

        progress_monitor = TrustedCoreProgressMonitor(rehosting_context)
        runner.register_handler(progress_monitor)

        boot_patcher = TrustedCoreBootPatcher(rehosting_context)
        runner.register_handler(boot_patcher)

        # SWI/SVC interpreter is not working yet
        exception_interpreter = TrustedCoreExceptionInterpreter(rehosting_context)
        # runner.register_handler(exception_interpreter)

        # exception_handler = TrustedCoreExceptionHandler(rehosting_context)
        # runner.register_handler(exception_handler)

        tee_driver_emulator = TrustedCoreTeeDriverEmulator()

        tzos_execution_strategy = TrustedCoreCallIntoTzosStrategy(rehosting_context)

        sm_emulator = SecureMonitorEmulator(rehosting_context, tee_driver_emulator, tzos_execution_strategy)
        runner.register_handler(sm_emulator)

        tzos_runner = TzosRunner(runner, tzos_execution_strategy)
        return tzos_runner


class TrustedCoreHuaweiP9LiteAvatarFactory(TrustedCoreAvatarFactory):
    def __init__(self):
        super().__init__()

        # these are mapped from a single dump of a partition called teeos
        self._teeos = AvatarFactoryMemoryMapping(0x36200000, 0x38000000 - 0x36200000)

        self._ta_ram = AvatarFactoryMemoryMapping(0x20000, 0x1000)
        self._nw_ram = AvatarFactoryMemoryMapping(0x40000000, 0x2000000)

        # virtual hardware configuration
        self._avatar_cpu = "cortex-a53"

    def _create_target_bridge(self, target: Target):
        return AArch64Compat32TargetBridge(target)

    def _add_serial_devices(self, avatar: ConvenientAvatar):
        avatar.add_pl011(0xFDF02000, 0x00001000, "uart", 0)
        avatar.add_pl011(0xFFF32000, 0x00001000, "secure_uart", 1)

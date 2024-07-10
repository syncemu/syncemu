from typing import TYPE_CHECKING, Optional

from avatar2 import Target, MemoryRange

from .colored_register_printer import ColoredRegistersPrinter
from .target_bridge import TargetBridge
from ..keystone import aarch64_asm

if TYPE_CHECKING:
    from .. import TemporaryCodeExecutionHelper, ConvenientAvatar


class RehostingContext:
    """
    Common state shared between multiple components.
    Further implements some convenience functionality needed by some of the components.
    """

    def __init__(
        self,
        avatar: "ConvenientAvatar",
        target: Target,
        smc_entrypoint_address: int,
        shared_memory: MemoryRange,
        temporary_code_execution_helper: "TemporaryCodeExecutionHelper",
        target_bridge: TargetBridge,
        smc_spsr_register_value: int,
        smc_return_from_tzos_boot_identifier: int,
        smc_normal_world_call_identifier: int,
        nsec_shared_memory_address: Optional[int] = None,
        tzos_eret_entrypoint: Optional[int] = None,
        trusted_apps_dir: Optional[str] = None,
        colored_register_printer: Optional[ColoredRegistersPrinter] = None,
    ):
        self.avatar = avatar
        self.target = target
        self.smc_entrypoint_address = smc_entrypoint_address
        self.nsec_shared_memory_address = nsec_shared_memory_address
        self.trusted_apps_dir = trusted_apps_dir
        self.shared_memory = shared_memory
        self.temporary_code_execution_helper = temporary_code_execution_helper

        self.target_bridge: TargetBridge = target_bridge

        self.smc_spsr_register_value = smc_spsr_register_value
        self.smc_return_from_tzos_boot_identifier = smc_return_from_tzos_boot_identifier
        self.smc_normal_world_call_identifier = smc_normal_world_call_identifier

        # used to track the execution state of the TZOS (at least to some extent)
        self.tzos_eret_entrypoint = tzos_eret_entrypoint

        self.colored_register_printer = colored_register_printer

    def write_aarch64_smc_return_assembly(self, assembler_code: str):
        assembly = aarch64_asm(assembler_code)
        return self._write_smc_return_assembly(assembly)

    def _write_smc_return_assembly(self, assembly: bytes):
        self.target.write_memory(self.smc_entrypoint_address, len(assembly), assembly, raw=True)
        return len(assembly)

    def write_system_register(self, system_register: str, value: int):
        """
        Little helper to set a system register by first setting a general register, then using some on-the-fly compiled
        assembler to write the actual system register.
        """

        # in AArch64, we have the general-purpose registers x0...x30
        # as we can't write directly into system registers, we store our value in one of them, and then mov the value
        # from there into the target register
        temp_general_register = "x0"

        # first, we back up the old value, so we can restore it later
        # this way, we can avoid side effects on other code
        old_value = self.target.read_register(temp_general_register)

        # next, we write the value into said register
        self.target.write_register(temp_general_register, value)

        # now, we can generate the code to move the value from the temp register into the actual register
        code = f"msr {system_register}, {temp_general_register}"

        # next, we use the temporary code execution helper to actually execute the whole thing
        self.temporary_code_execution_helper.assemble_and_store_aarch64(code)

        executor = self.temporary_code_execution_helper.make_executor()
        with executor:
            executor.run()

        # finally, we restore the backed up value
        self.target.write_register(temp_general_register, old_value)

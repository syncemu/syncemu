from .structs import OpteeMsgArg
from ..struct import Struct
from ..call_into_tzos_strategy import CallIntoTzosStrategyBase
from ..tzos_runner import TzosCommandFailed


class OpteeCallIntoTzosStrategy(CallIntoTzosStrategyBase):
    def parse_return_value(self) -> "Struct":
        rv = OpteeMsgArg.from_memory(self._context.target, self._context.shared_memory.address)
        print(rv)

        if rv.ret != 0:
            raise TzosCommandFailed(rv)

        return rv

    def execute_tzos_command(self, struct: Struct):
        # make sure OP-TEE has booted properly
        assert self._context.tzos_eret_entrypoint is not None

        print(struct)

        # pass arg to TZOS
        shared_memory_content = struct.to_bytes()
        self._context.shared_memory.forwarded_to.write_into_buffer(shared_memory_content)

        # we at the last smc call of tzos -> now set up a TA call
        # from diary: set spsr_el3 = 0x600003c4 (copied from virt) and elr_el3 = entry for TZOS (0xE1018FC)
        # note that we can't set system registers with gdb directly, that's why combine the forces of GDB and asm code

        # hardcode spsr_el3 to OPTEE_SMC_CALL_WITH_ARG via x2
        self._context.write_system_register("spsr_el3", self._context.smc_spsr_register_value)
        # elr_el3 needs to be set to the
        self._context.write_system_register("elr_el3", self._context.tzos_eret_entrypoint)

        # from diary: for a TA call, set x0 to OPTEE_SMC_CALL_WITH_ARG, x1 and x2 are the address of the shared memory
        self._context.target.write_register("x0", 0x32000004)
        self._context.target.write_register("x2", self._context.shared_memory.address)

        # for good measure, we reset the remaining general purpose registers that could be
        # we just need to clear x1, really, though
        for reg in ["x1", "x3", "x4", "x5", "x6"]:
            self._context.target.write_register(reg, 0x0)

        # pass control back to TZOS with an eret instruction
        self._context.write_aarch64_smc_return_assembly("eret")

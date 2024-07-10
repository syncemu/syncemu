from .structs import TC_NS_SMC_CMD
from ..struct import Struct
from ..call_into_tzos_strategy import CallIntoTzosStrategyBase
from ..tzos_runner import TzosCommandFailed


class TrustedCoreCallIntoTzosStrategy(CallIntoTzosStrategyBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.counter: int = 0x0
        self.current_event_nr = 0x0

    def parse_return_value(self) -> "Struct":

        i = 0
        # as we do not know where the result will be just search the entire output queue for the sent event_nr
        # TODO for agent smcs event_nr is not a unique identifier
        rv = TC_NS_SMC_CMD.from_memory(
            self._context.target, self._context.shared_memory.address + 0x4 + 0x4 + 0x7DE + i * 0x35
        )
        while rv.event_nr != self.current_event_nr:
            i += 1
            if i > 0x26:
                print("Nothing found!")
                return rv
            rv = TC_NS_SMC_CMD.from_memory(
                self._context.target, self._context.shared_memory.address + 0x4 + 0x4 + 0x7DE + i * 0x35
            )

        return rv

    def execute_tzos_command(self, tc_ns_smc_struct: TC_NS_SMC_CMD):
        # make sure OP-TEE has booted properly
        assert self._context.tzos_eret_entrypoint is not None

        # pass arg to TZOS
        shared_memory_content = tc_ns_smc_struct.to_bytes()

        # save the event_nr to find the result later in the output queue
        self.current_event_nr = tc_ns_smc_struct.event_nr

        # write index/counter at the start
        self._context.target.write_memory(self._context.shared_memory.address, 0x4, self.counter + 1)
        # write tc_ns_smc_struct to memory
        self._context.target.write_memory(
            self._context.shared_memory.address + 0x4 + self.counter * 0x35, 0x35, shared_memory_content, raw=True
        )

        self.counter += 1
        # 0x26 smc cmds fit in the queue started by counter 0x1 - 0x26 but use less and TC will just skip zeroed memory
        # TODO fix this to work with the correct value... seems to break
        if self.counter >= 0x24:
            self.counter = 0

        # we at the last smc call of tzos -> now set up a TA call
        # note that we can't set system registers with gdb directly, that's why combine the forces of GDB and asm code

        self._context.write_system_register("spsr_el3", self._context.smc_spsr_register_value)
        # elr_el3 needs to be set to the
        self._context.write_system_register("elr_el3", self._context.tzos_eret_entrypoint)

        # from diary: for a TA call, set x0 to TSP_REQUEST, x1 is the address of the shared memory, x2 is cmd flag
        self._context.target.write_register("x0", 0xB2000008)
        self._context.target.write_register("x1", self._context.shared_memory.address)
        # for now hardcoded 0xF... maybe we need to change that?
        self._context.target.write_register("x2", 0xF)

        # for good measure, we reset the remaining general purpose registers that could be
        # we just need to clear x1, really, though
        # for reg in ["x3", "x4", "x5", "x6"]:
        #    self._context.target.write_register(reg, 0x0)

        # pass control back to TZOS with an eret instruction
        self._context.write_aarch64_smc_return_assembly("eret")

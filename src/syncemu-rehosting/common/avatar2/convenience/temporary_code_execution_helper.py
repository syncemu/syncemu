import time

from avatar2 import MemoryRange, Target, TargetStates

from .convenient_avatar import ConvenientAvatar
from .peripherals import InMemoryBufferPeripheral
from ..keystone import aarch64_asm


class SafeCodeExecutor:
    """
    A little companion class for TemporaryCodeExecutionHelper that implements the with pattern.

    Note that this class does not store the pre-execution state in any way. It's the caller's responsibility to store
    the values of, e.g., registers they modify before the execution.
    """

    def __init__(self, target: Target, memory_range: MemoryRange, code_size: int):
        """
        :param target: used to control the execution of the code via breakpoints (typically a QemuTarget)
        :param memory_range: memory containing the assembly we shall execute
        :param code_size: size of the code (i.e., pointer to the final instruction)
        :param suspend: controls whether we suspend execution after executing the code
        """

        # check preconditions
        assert memory_range.size > 0

        # make sure there's at least some code assembled
        # (safety net, in case the user forgets to actually put in some assembly)
        assert code_size > 0

        self.memory_range = memory_range
        self.target = target
        self.code_size = code_size

        # initialized in __enter__
        self.old_pc = None

    def _sleep_if_necessary(self):
        # a temporary workaround (programmer language for "bad hack")
        while self.target.state != TargetStates.STOPPED:
            time.sleep(0.1)

    def _breakpoint_location(self):
        # subtracting 4 bytes aka one instruction
        return self.memory_range.address + self.code_size - 4

    def __enter__(self):
        # class invariant
        assert self.old_pc is None

        # don't ask me why, but it seems like there's some issues with the state management in avatar2
        # pausing for a bit here works fine
        self._sleep_if_necessary()

        # store PC so we can restore (no pun intended) it after executing the temporary code
        self.old_pc = self.target.read_register("pc")

        # continue execution in our range containing the assembly
        self.target.write_register("pc", self.memory_range.address)

        # furthermore, we want a temporary breakpoint to be set at the end of the temporary code
        # we start while execution is suspended in a breakpoint, and want to pass back control after executing our own
        # code
        self.target.set_breakpoint(self._breakpoint_location())

    def __exit__(self, exc_type, exc_val, exc_tb):
        # class invariant
        assert self.old_pc is not None

        # don't ask me why, but it seems like there's some issues with the state management in avatar2
        # pausing for a bit here works fine
        self._sleep_if_necessary()

        # restore old PC
        self.target.write_register("pc", self.old_pc)

        # remove temporary breakpoint again, as it's not needed anymore
        self.target.remove_breakpoint(self._breakpoint_location())

    def run(self):
        # continue until final instruction
        self.target.cont()
        self.target.wait()

        # as we suspend before the final instruction is executed, we have to stepi once to execute it
        self.target.step()


class TemporaryCodeExecutionHelper:
    """
    Maps and manages a memory area used to run just-in-time assembled code. Useful to set, e.g., system registers,
    which can't be done from GDB directly.
    """

    def __init__(self, target: Target, avatar: ConvenientAvatar, address: int, size: int):
        # target is used to actually control the execution using temporary breakpoints
        self.target = target

        # create some in-memory buffer at the specified address and with the specified size
        self.memory_range = avatar.add_in_memory_buffer_peripheral(address, size, name="temp_code_execution")
        self.peripheral: InMemoryBufferPeripheral = self.memory_range.forwarded_to

        # track size of assembled code in the buffer
        self.code_size = 0

    def assemble_and_store_aarch64(self, assembler_code: str):
        """
        Just-in-time assemble some AArch64 assembler and insert it into our memory buffer

        :param assembler_code: AArch64 assembler code to compile and store
        """

        # returns a byte string
        assembly = aarch64_asm(assembler_code)

        # calculate the size, which is basically the offset of the last instruction
        # needed by the SafeCodeExecutor
        self.code_size = len(assembly)

        self.peripheral.write_into_buffer(assembly)

    def make_executor(self) -> SafeCodeExecutor:
        """
        Factory function to create a SafeCodeExecutor.
        """

        return SafeCodeExecutor(self.target, self.memory_range, self.code_size)

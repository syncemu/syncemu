from .call_into_tzos_strategy import CallIntoTzosStrategy
from . import BreakpointHandlingRunner
from .secure_monitor_emulator import TzosBooted, TzosCommandFinished
from .struct import Struct


class NonTzosBreakpointHit(Exception):
    pass


class TzosCommandFailed(Exception):
    """
    Thrown when an OP-TEE command execution appears to have failed (i.e., returns a non-zero return value).
    The actual optee_msg_arg returned can be found in the optee_msg_arg param.
    """

    def __init__(self, struct: Struct):
        super().__init__()
        self.struct = struct

    def __repr__(self):
        return f"<{self.__class__.__name__} struct={self.struct}>"


class TzosRunner:
    """
    Adapter for BreakpointHandlingRunner to provide the previously available workflow to the script. Handles exceptions
    raised by secure monitor breakpoint handler.
    """

    def __init__(self, runner: BreakpointHandlingRunner, call_into_tzos_strategy: CallIntoTzosStrategy):
        self._call_into_tzos_strategy = call_into_tzos_strategy
        self._runner = runner

    def cont(self):
        """
        Continue execution until one of the following events occurs:

        - TZOS booted (returns None)
        - OP-TEE TZOS command finished (returns parsed result)

        Note: this method is usually just used once in scripts to boot the TZOS. Once booted, execute_tzos_command(...)
        shall be used to set up a command execution and continue execution until it's finished.
        Only when using custom breakpoints, when a breakpoint is hit that is not managed by the emulator, causing an
        exception to be raised, the execution may be continued with cont() afterwards.

        :param fail_silently: whether to raise an exception if the command was unsuccessful
        :raises TzosCommandFailed: in case OP-TEE returns a non-zero value (result can be found in the exception's
            value attribute)
        :raises NonTzosBreakpointHit: if a breakpoint is hit that is not managed by the emulator
        """

        # TODO: refactor with a generator instead of a loop, so we don't have to (ab)use an exception to receive the
        #   return value
        try:
            self._runner.cont()

        except TzosCommandFinished:
            return self._call_into_tzos_strategy.parse_return_value()

        except TzosBooted:
            # the boot does not return any data we could read out (makes sense, as the address of the shared
            # memory is passed upon command execution only), so there's nothing we could return here
            # as far as we could observe, this won't be reached if the TZOS hasn't been able to complete the boot,
            # though, so false positives *should* not occur
            return

        # raising an exception is an easy-to-understand and -implement way to pass back control to the caller
        raise NonTzosBreakpointHit()

    def execute_tzos_command(self, msg_arg: Struct, fail_silently: bool = False):
        """
        Execute a TZOS command, continue execution and return result (unless interrupted by a breakpoint).

        :param optee_msg_arg: command to be executed by the TZOS, which will be put into a shared memory range
        :param fail_silently: whether to raise an exception if the command was unsuccessful
        :raises NonTzosBreakpointHit: if a breakpoint was hit that is not managed by this or a child class
        :raises TzosCommandFailed: in case OP-TEE returns a non-zero value (result can be found in the exception's
            value attribute)
        """

        self._call_into_tzos_strategy.execute_tzos_command(msg_arg)

        # continue execution until command finished, then parse and return the result
        try:
            return self.cont()

        except TzosCommandFailed as e:
            if fail_silently:
                return e.struct

            raise

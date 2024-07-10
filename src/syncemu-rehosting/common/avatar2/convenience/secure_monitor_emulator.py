from typing import Dict, TYPE_CHECKING

from .call_into_tzos_strategy import CallIntoTzosStrategy
from .rehosting_context import RehostingContext
from . import BreakpointHandlerBase
from .tee_driver_emulator import TeeDriverEmulator

if TYPE_CHECKING:
    from common.avatar2.convenience import InMemoryBufferPeripheral

from common import get_logger


class TzosBooted(Exception):
    # TODO: replace exceptions with a more elegant solution
    #   should be fixed once the generator is implemented instead of that while loop
    #   see TEE driver emulator for more information
    pass


class TzosCommandFinished(Exception):
    """
    Signalizes to the TZOS runner that the last request to the TZOS has worked as intended.
    Used to, e.g., signalize that the hello world TA has been opened successfully, or that a command invoked on it has
    finished.

    It contains a response argument, representing the result of the TZOS call.

    The concept of using an exception to handle to return values originates from the good ol' days, when Python
    generators haven't been able to return values yet.
    TODO: refactor so that we use a generator for handling SMCs, and use return values as intended
    """

    pass


class SecureMonitorEmulator(BreakpointHandlerBase):
    """
    This class manages an OP-TEE TZOS QEMU target. While under its management, the runner adds a breakpoint on
    OP-TEE's default SMC callback address. This allows it to read the registers, recognize SMCs and react properly.
    """

    def __init__(
        self,
        rehosting_context: RehostingContext,
        tee_driver_emulator: TeeDriverEmulator,
        call_into_tzos_strategy: CallIntoTzosStrategy,
    ):
        """
        Initialize the SMC-handling runner.

        :param avatar: used to set up a "shared memory" buffer which will be used to pass parameters along with SMCs
        :param qemu_target: QEMU object representing the emulated TZOS
        :param smc_entrypoint_address: address
        """

        super().__init__()

        self._context = rehosting_context

        self._logger = get_logger("optee_secure_monitor")

        # convenience: allow easier access to actual in-memory buffer
        self._shared_memory_buffer: InMemoryBufferPeripheral = self._context.shared_memory.forwarded_to

        # normal world emulation
        self._tee_driver_emulator = tee_driver_emulator

        # the implementation of the actual exception return code is decoupled from the secure monitor emulation in
        # order to be able to use the latter for multiple TZOSs
        self._call_into_tzos_strategy = call_into_tzos_strategy

        # set up callbacks that shall be registered in the runner
        self._register_handler_for_breakpoint(self._context.smc_entrypoint_address, self._handle_smc_from_tzos)

    def _handle_smc_from_tzos(self):
        # we use a system of callbacks to handle SMCs
        # these are defined in a dict which can later be queried
        # each of these handlers has full access to the instance's state, and can e.g., write to memory, or read
        # registers
        smc_handlers: Dict[int, callable] = {
            # value detected by trial-and-error
            self._context.smc_return_from_tzos_boot_identifier: self._handle_return_from_tzos_boot,
            # optee returns that func-identifier after initializing to load a TA
            # seems to be some sort of "switch to NW" and request RPC-Service
            self._context.smc_normal_world_call_identifier: self._handle_call_from_tzos_to_normal_world,
        }

        # there can be passed up to 7 64-bit arguments in registers x0-x6
        # results are returned in x0-x3
        # x18-x30 and SP_ELx are callee-saved (must be preserved over smc)

        # first argument in w0 is always the function identifier -> see calling convetion for more info
        # unknown function identifier return is 0xffffffff

        # for now we only need the function identifier
        function_identifier = self._context.target.read_register("x0")

        # in case we don't find a registered callback, we fall back to the default handler
        try:
            smc_callback = smc_handlers[function_identifier]
        except KeyError:
            smc_callback = self._handle_default_smc

        self._logger.info(f"SMC {hex(function_identifier)} received, handler: {smc_callback.__name__}")

        # run callback
        smc_callback()

    def _handle_default_smc(self):
        self._context.write_aarch64_smc_return_assembly("eret")

    def _handle_return_from_tzos_boot(self):
        # the address which we use to pass control back to the TZOS through eret is sent to us once in this SMC
        # we have to memorize it therefore
        assert self._context.tzos_eret_entrypoint is None
        self._context.tzos_eret_entrypoint = self._context.target.read_register("x1")
        self._logger.debug(f"tee_entry_std address (used to reply to eret): {hex(self._context.tzos_eret_entrypoint)}")

        # pass back control to calling script
        raise TzosBooted()

    def _handle_call_from_tzos_to_normal_world(self):
        # forward call to TEE driver emulator (normal world EL1 component)
        self._tee_driver_emulator.handle_rpc()

        # reply with default params (unless the RPC handler reports that the session has opened)
        self._context.write_system_register("spsr_el3", self._context.smc_spsr_register_value)
        self._context.write_system_register("elr_el3", self._context.tzos_eret_entrypoint)

        # continue with an eret instruction
        self._context.write_aarch64_smc_return_assembly("eret")

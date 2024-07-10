from ..exception_interpreter import AArch32ExceptionInterpreter
from .... import get_logger
from .. import BreakpointHandlerBase
from ..rehosting_context import RehostingContext


class TrustedCoreExceptionInterpreter(BreakpointHandlerBase):
    def __init__(self, rehosting_context: RehostingContext, enable_swi_interpreter: bool = True):
        super().__init__()

        self._context = rehosting_context

        self._breakpoints = {
            0xC001F580: "osRelocVector -> osResetVector1",
            0xC001F584: "osRelocVector -> osUndefInstrVector",
            0xC001F58C: "osRelocVector -> osPrefetchAbortVector",
            0xC001F590: "osRelocVector -> osDataAbortVector",
            0xC001F594: "osRelocVector -> osReservedVector",
            0xC001F598: "osRelocVector -> osIrqVector",
            0xC001F59C: "osRelocVector -> osFiqVector",
        }

        if enable_swi_interpreter:
            self._breakpoints.update(
                {
                    0xC001F588: "osRelocVector -> osSwiVector",
                }
            )

        self._logger = get_logger("tc_exception_interpreter")

        for bp_address in self._breakpoints.keys():
            self._register_handler_for_breakpoint(bp_address, self._handle_bp)

    def _handle_bp(self):
        bp_address = self._context.target.read_register("pc")

        # here, the registers have not changed yet (except for PC), so dumping them is a good idea
        self._logger.error("exception vector table reached, dumping registers")
        self._context.colored_register_printer.print_registers()

        interpreter = AArch32ExceptionInterpreter(self._context.target_bridge)

        if bp_address == 0xC001F580:
            interpreter.handle_reset()

        elif bp_address == 0xC001F584:
            interpreter.handle_undefined_instruction()

        elif bp_address == 0xC001F588:
            # TODO: implement svc parsing
            # interpreter.handle_svc()
            self._logger.warning("svc parsing has not been implemented yet")

        elif bp_address == 0xC001F58C:
            interpreter.handle_prefetch_abort()

        elif bp_address == 0xC001F590:
            interpreter.handle_data_abort()

        elif bp_address == 0xC001F594:
            # purpose unknown, doesn't match any exception type listed in the manual
            raise NotImplementedError()

        elif bp_address == 0xC001F598:
            interpreter.handle_IRQ()

        elif bp_address == 0xC001F59C:
            interpreter.handle_FIQ()

        else:
            # should be unreachable
            raise RuntimeError()

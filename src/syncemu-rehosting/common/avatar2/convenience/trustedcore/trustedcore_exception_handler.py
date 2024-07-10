from .... import get_logger
from .. import BreakpointHandlerBase
from ..rehosting_context import RehostingContext


class TrustedCoreExceptionHandler(BreakpointHandlerBase):
    def __init__(self, rehosting_context: RehostingContext):
        super().__init__()

        self._context = rehosting_context

        self._logger = get_logger("tc_exception_handler")

        self._register_handler_for_breakpoint(0xC0008B1C, self._handle_bp)

    def _handle_bp(self):
        # not all exceptions lead to termination: supervisor calls for instance are just regular business
        # therefore, we wait for the program to reach osExceptionHandle, which is the handler for all exceptions
        # from which the program can't recover (it's an infinite loop)
        # terminating execution here prevents QEMU from generating immense amounts of log data, if logging of
        # instructions is enabled (which is the case, currently)
        self._context.avatar.shutdown()
        raise RuntimeError("osExceptionHandle reached -> terminating")

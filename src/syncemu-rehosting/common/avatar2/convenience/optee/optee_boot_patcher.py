from .... import get_logger
from .. import BreakpointHandlerBase
from ..rehosting_context import RehostingContext


class OpteeBootPatcher(BreakpointHandlerBase):
    def __init__(self, rehosting_context: RehostingContext, enable_optional_patches: bool = False):
        super().__init__()

        self._context = rehosting_context

        # must-have patches
        self._breakpoints = {
            0x0e10ff84: "indicate gic version 3",
            0x0e10ffc0: "skip gic sysreg",
            0x0e10ffc8: "skip gic sysreg",
            0x0e110008: "skip gic sysreg",
            0x0e10f630: "skip gic sysreg",
            0x0e10f994: "modify in gic add",
            0x0e10fc68: "modify in gic enable",
        }

        if enable_optional_patches:
            # if disabled OP-TEE will boot but generate more error output
            self._breakpoints.update(
                {

                }
            )

        self._logger = get_logger("optee_boot_patcher")

        for bp_address in self._breakpoints.keys():
            self._register_handler_for_breakpoint(bp_address, self._handle_bp)

    def _handle_bp(self):
        bp_address = self._context.target.read_register("pc")

        if bp_address == 0x0e10ff84:
            self._context.target.write_register("x1", 0x3)

        if bp_address == 0x0e10ffc0:
            self._context.target_bridge.write_register("pc", 0x0e10ffc4)

        if bp_address == 0x0e10ffc8:
            self._context.target_bridge.write_register("pc", 0x0e10ffcc)

        if bp_address == 0x0e110008:
            self._context.target_bridge.write_register("pc", 0x0e11000c)

        if bp_address == 0x0e10f630:
            self._context.target_bridge.write_register("pc", 0x0e10f634)

        if bp_address == 0x0e10f994:
            self._context.target_bridge.write_register("x1", 0x1d)

        if bp_address == 0x0e10fc68:
            self._context.target_bridge.write_register("x1", 0x1d)
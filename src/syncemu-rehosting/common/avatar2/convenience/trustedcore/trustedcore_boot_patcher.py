from .... import get_logger
from .. import BreakpointHandlerBase
from ..rehosting_context import RehostingContext


class TrustedCoreBootPatcher(BreakpointHandlerBase):
    def __init__(self, rehosting_context: RehostingContext, enable_optional_patches: bool = False):
        super().__init__()

        self._context = rehosting_context
        self.accessed_hardware = 0

        # must-have patches
        self._breakpoints = {
            0xC00309EC: "PATCH: console_init: write 0x0 at uart_index to activate uart output",
            0xC0042184: "PATCH: DX_UTIL_ResetLowResTimer: write r4=0xffffffff to exit loop",
            0xC003649C: "PATCH: DX_CclibInit: set r3 (gCcBaseReg +0xabc) to 0xf to exit loop",
            0xC000DD14: "PATCH: map_task_mem: set r0 to 0x0 to pass check",
            0xC000DA80: "PATCH: load_elf: set r0 to value 0x0",
            # 0xC004174C: "PATCH: gCcRegBase set r3",
            # 0xC0039A6C: "PATCH: gCcRegBase set r3",
            # 0xC0039A78: "PATCH: gCcRegBase set r14",
            # 0xC0039A7C: "PATCH: gCcRegBase set r12",
            # 0xC004C684: "PATCH: gCcRegBase set r1",
            # 0xC003A950: "PATCH: gCcRegBase set r6",
            # 0xC00369C4: "PATCH: gCcRegBase set r2",
            # 0xC00369C8: "PATCH: gCcRegBase set r3",
            # 0xC0036A08: "PATCH: gCcRegBase set r3",
            # 0xC0036A24: "PATCH: gCcRegBase set r3",
            # 0xC0036660: "PATCH: gCcRegBase set r3",
            # 0xC003666C: "PATCH: gCcRegBase set r0",
            # 0xC00368A0: "PATCH: gCcRegBase set r9",
            0xC0036624: "DX_HAL_Init: set gCcRegBase",
            0xC002A764: "main: after DX_CclibInit - get return value",
            0xC00364C4: "PATCH: DX_CclibInit: set r3 to 0xbf to pass check",
            0xC00364DC: "PATCH: DX_CclibInit: set r2 to 0xD5C63000 to pass check",
            0xC0044698: "PATCH: RNG_PLAT_SetUserRngParameters: set r3 (gCcBaseReg +0xabc) to 0xf to exit loop ",
            0xC00446B8: "PATCH: RNG_PLAT_SetUserRngParameters: set r3 (gCcBaseReg +0xab4) to 0xf to exit loop ",
            0xC003666C: "PATCH: DX_HAL_WaitInterrupt: set r0(gCcBaseReg +0xa00) to same value as r4 to exit loop ",
            0xC003A964: "PATCH: AddHWDescSequence: set r3 to 0xf to exit loop",
            0xC00369C8: "PATCH: WaitForSequenceCompletionPlat: set r3 to 0xf to exit loop",
            0xC003655C: "PATCH: DX_CclibInit: set r0 to 0x0  ",
            # Patches in DeriveKey
            0xC0039A84: "PATCH: symDriverAdaptorCopySramBuff: set r12 to 0x1", # accessing value at 0xff011f08
            0xC004C69C: "PATCH: ReadContextWord: set r2 to 0x1", # accessing 0xff011f08
            0xC004C6BC: "PATCH: ReadContextWord: set r2 to 0x1",
            # patches for crypto cell
            #0xC0051368: "PATCH: set x3 to 0x1", # accessing value at 0xff0110b4
            #0xc005143c: "PATCH: set x3 to 0x1", # accessing value at 0xff011f08
            #0xc00514d0: "PATCH: set x3 to 0x1", # accessing value at 0xff011f08
            #0xc0051554: "PATCH: set x3 to 0x1", # accessing value at 0xff011f08
            #0xc00516b8: "PATCH: set x3 to 0x1", # accessing value at 0xff0110b4
            #0xc0051720: "PATCH: set x3 to 0x1", # accessing value at 0xff011f08
            #0xc00517a4: "PATCH: set x3 to 0x1", # accessing value at 0xff011f08
            #0xc0050524: "PATCH: set x3 to 0x1",
            #0xc00510b8: "PATCH: set x3 to 0x1",
            #0xc0051100: "PATCH: set x3 to 0x1",
            #0xc0051180: "PATCH: set x1 to 0x1",
            # patches for fingerprint
            #0xc0029834: "PATCH: set x3 to 0xe0000", # accessing value at 0xe8a09000 + 0x414
            #0xc0029444: "PATCH set x14 to 0x0", # spi controller
            # test for agent - in globaltask used by fingerprintTA to get current time
            # only needed for logging...
            #0x07064524: "PATCH: set expected value in memory",
        }

        if enable_optional_patches:
            # if disabled TC will boot but generate more error output
            self._breakpoints.update(
                {
                    0xC002A764: "PATCH: main: set r0=0x0 to not let CclibInit fail",
                    0xC0028454: "PATCH: icc_channels_init: make cmp go through by setting base_addr = 0x0",
                    # influences the virt addr of globaltask
                    0xC000DD20: "PATCH: map_task_mem: set r0 to random value 0x123C4000",
                }
            )

        self._logger = get_logger("tc_boot_patcher")

        for bp_address in self._breakpoints.keys():
            self._register_handler_for_breakpoint(bp_address, self._handle_bp)

    def _handle_bp(self):
        bp_address = self._context.target.read_register("pc")
        self.accessed_hardware = 1

        if bp_address == 0xc0029444:
            self._context.target.write_register("x14", 0x0)

        if bp_address == 0xc0029834:
            self._context.target.write_register("x3", 0xe0000)

        if bp_address == 0xC0051368 or bp_address == 0xc0051100 or bp_address == 0xc00510b8 or bp_address == 0xc0050524 or bp_address == 0xc00517a4 or bp_address == 0xc0051720 or bp_address == 0xc00516b8 or bp_address == 0xc005143c or bp_address == 0xc00514d0 or bp_address == 0xc0051554:
            self._context.target.write_register("x3", 0x1)

        if bp_address == 0xc0051180:
            self._context.target.write_register("x1", 0x1)

        if bp_address == 0xC00368A0:
            self._context.target.write_register("x9", 0xC0004000)

        if bp_address == 0xC003666C:
            self._context.target.write_register("x0", self._context.target.read_register("x4"))

        if bp_address == 0xC00369C8:
            self._context.target.write_register("x3", 0xF)

        if bp_address == 0xC00369C4:
            self._context.target.write_register("x2", 0xC0004000)

        if bp_address == 0xC003A950:
            self._context.target.write_register("x6", 0xC0004000)

        if bp_address == 0xC004C684:
            self._context.target.write_register("x1", 0xC0004000)

        if bp_address == 0xC0039A78:
            self._context.target.write_register("x14", 0xC0004000)
        if bp_address == 0xC0039A84:
            self._context.target.write_register("x12", 0x1)
        # set to some random working address?
        if (
            bp_address == 0xC004174C
            or bp_address == 0xC0039A6C
            or bp_address == 0xC0036A08
            or bp_address == 0xC0036A24
            or bp_address == 0xC0036660
        ):
            self._context.target.write_register("x3", 0xC0004000)

        if bp_address == 0xC00364C4:
            self._context.target.write_register("x3", 0xBF)
        if bp_address == 0xC00364DC:
            self._context.target.write_register("x2", 0xD5C63000)
        # normally read from 0xff011abc which has to be != 0x1
        # set r3 to 0xf to avoid the fail
        if bp_address == 0xC0044698:
            self._context.target.write_register("x3", 0xF)
        if bp_address == 0xC00446B8:
            self._context.target.write_register("x3", 0xF)
        if bp_address == 0xC003666C:
            r4 = self._context.target.read_register("x4")
            self._context.target.write_register("x0", r4)
        if bp_address == 0xC003A964:
            self._context.target.write_register("x3", 0xF)
        if bp_address == 0xC00369C8:
            self._context.target.write_register("x3", 0xF)
        if bp_address == 0xC003655C:
            self._context.target.write_register("x0", 0x0)

        # Patches for DeriveKey
        if bp_address == 0xC0039A7C:
            self._context.target.write_register("x12", 0x1)
        if bp_address == 0xC004C69C:
            self._context.target.write_register("x2", 0x1)
        if bp_address == 0xC004C6BC:
            self._context.target.write_register("x2", 0x1)

        # write 0x0 to r2. r2 is stored at uart_index -> activate UART output
        if bp_address == 0xC00309EC:
            self._context.target.write_register("x2", 0x0)

        # write 0xffffffff to r4 which breaks out of the loop
        # it seems like there is an lowResTimer MMIO
        if bp_address == 0xC0042184:
            self._context.target.write_register("x4", 0xFFFFFFFF)

        # normally read from 0xff011abc which has to be != 0x1
        # set r3 to 0xf to avoid the fail
        if bp_address == 0xC003649C:
            self._context.target.write_register("x3", 0xF)

        # set r0=0x0 so CclibInit does not fail
        # if the init hardware is needed we need to emulate more
        if bp_address == 0xC002A764:
            self._context.target.write_register("x0", 0x0)

        # icc_channels_init: make cmp go through by setting base_addr = 0x0
        if bp_address == 0xC0028454:
            self._context.target.write_register("x0", 0x0)

        # map_task_mem
        if bp_address == 0xC000DD14:
            self._context.target.write_register("x0", 0x0)

        # map_task_mem r0 = random number
        # the last 20 bit are the first 20 bit of an address we jump to at 0xc0008a58 (restoreContext)
        if bp_address == 0xC000DD20:
            self._context.target.write_register("x0", 0x123C4000)

        # we need to return a "random" value - 0x0 is ok
        if bp_address == 0xC000DA80:
            self._context.target.write_register("x0", 0x0)

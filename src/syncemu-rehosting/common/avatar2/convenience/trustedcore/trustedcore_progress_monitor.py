from .... import get_logger
from .. import BreakpointHandlerBase
from ..rehosting_context import RehostingContext


class TrustedCoreProgressMonitor(BreakpointHandlerBase):
    def __init__(self, rehosting_context: RehostingContext):
        super().__init__()

        self._context = rehosting_context

        self._breakpoints = {
            0xC0008108: "about to null bss",
            0xC000811C: "bss should now be overwritten",
            0xC002A6EC: "main start",
            0xC002A6FC: "main return from secure_mmu, call to symtab_mem_reloc",
            0xC002A5DC: "page table fail...?",
            0xC002A710: "main return from symtab_mem_reloc, call to console_init",
            0xC002A714: "main return from console_init, call to log_buff_init",
            0xC002A718: "main return from log_buff_init, call to platform_init",
            0xC002A71C: "main return from platform_init",
            0xC002A73C: "main call to uart_printf_func",
            0xC002A740: "main return from uart_printf_func, call rtosck_symtab_entry_add",
            0xC002A744: "main return from rtosck_symtab_entry_add, call to osHwInit",
            0xC002A748: "main return from osHwInit, call to osRegister",
            0xC002A74C: "main return from osRegister",
            0xC002A754: "main call to SRE_TaskMem_Init",
            0xC002A758: "main return from SRE_TaskMem_Init, call to SEB_INIT",
            0xC002A75C: "main return from SEB_INIT, call to ccs_test",
            0xC002A760: "main return from ccs_test, call to DX_CclibInit",
            0xC002A7D8: "main return from osInitialize",
            0xC002A794: "main call osStart",
            0xC00420F8: "enter ResetLowResTimer",
            0xC0042198: "exit ResetLowResTimer",
            0xC00364E8: "enter DX_HAL_Terminate",
            0xC002A7D4: "enter osInitialize",
            0xC002A420: "osMemSystemInit, SRE_MemPtCreate",
            0xC0025528: "enter bsp_param_cfg_init",
            0xC002A2F8: "enter tc_drv_init",
            0xC002673C: "enter bsp_icc_init",
            0xC0026470: "icc_channel_init",
            0xC002649C: "icc_channel_init: call SRE_MemAlloc1",
            0xC00264A0: "icc_channel_init: after SRE_MemAlloc1",
            0xC0026528: "icc_channel_init: call SRE_MemAlloc2",
            0xC0026534: "icc_channel_init: after SRE_MemAlloc2",
            0xC00266EC: "icc_channel_init: error",
            0xC00264E4: "icc_channel_init: call icc_restore_recv_channel_flag",
            0xC00264E8: "icc_channel_init: after icc_restore_recv_channel_flag",
            0xC00264F4: "icc_channel_init: call memset",
            0xC00264F8: "icc_channel_init: after memset",
            0xC002A5B8: "osInit before bx r3",
            0xC002A0D8: "osTaskInit",
            0xC000DCB4: "map_task_mem",
            0xC000DCFC: "map_task_mem: after get_empty_task_virt_mem",
            # can be activated for more output during testing
            # 0xC000D3D8: "map_page_entry",
            # 0xc000d2d8: "map_page_L2_entry",
            # 0xc001cf1c: "memset",
            0xC001D110: "strncpy in lr/r14 is the char",
            0xC00135F0: "global_task_load: after SRE_MemAlloc_Align",
            0xC0013634: "global_task_load: before memset",
            0xC0013670: "global_task_load: before memcpy",
            0xC00136C0: "global_task_load: before memmove",
            0xC00136F4: "global_task_load: before add_to_tselist",
            0xC00136FC: "global_task_load: after add_to_tselist",
            0xC001374C: "global_task_load: before change_got_table2",
            0xC00137B8: "global_task_load: before SRE_CacheCodeUpdate",
            0xC0013298: "parse_rela_section",
            0xC00188EC: "SRE_TaskCreate",
            0xC002A14C: "OsTaskInit: return from SRE_TaskCreate",
            0xC002A5BC: "osStart",
            0xC0018674: "osActivate",
            0xC00186CC: "osActivate: call SRE_Change_Pte_Svc",
            0xC00186D0: "osActivate: return from SRE_Change_Pte_Svc, call osFirstTimeSwitch",
            0xC00186D4: "osActivate: return from osFirstTimeSwitch",
            0xC00089A0: "osTaskContextSwitch",
            0xC0008A2C: "osTaskContextLoad",
            0xC000E75C: "SRE_Change_Pte_Svc",
            0xC001384C: "SRE_Dynamic_Loadelf",
            0xC0013DE8: "SRE_HuntByName",
            0xC0014C10: "SRE_MsgRcv",
            0xC0012E18: "in SRE_PullKernelVariables",
            0xC4000000: "GLOBALTASK: entry",
            0xC4000054: "GLOBALTASK: start reet",
            0xC40000FC: "GLOBALTASK: PullKernelVariables after MsgRcv",
            0xC400010C: "GLOBALTASK: compare r12 with 0xf",
            0xC400011C: "GLOBALTASK: map_ns_cmd",
            0xC4000148: "GLOBALTASK: SRE_PushKernelVariables",
            0xC40001D0: "GLOBALTASK: memset",
            0xC40001FC: "GLOBALTASK: set_TEE_return",
            0xC4000204: "GLOBALTASK: set_TEE_processed",
            0xC4000210: "GLOBALTASK: after set_TEE_processed",
            0xC4000930: "GLOBALTASK: UpdateKernelVariables",
            0xC4000568: "GLOBALTASK: switch case with r2 cmd_id",
            0xC4000ABC: "GLOBALTASK: init_ta_context",
            0xC400362C: "GLOBALTASK: find_service",
            0xC40051B8: "GLOBALTASK: register_agent",
            0xC4005220: "GLOBALTASK: in register_agent call map_from_ns_page",
            0x041DDFB4: "REET: tee_task_entry",
            0x041DDFFC: "REET: __start_tz",
            0x41DD528: "REET: MsgSnd",
            0x21DDFF0: "KEYMASTER: TA_CreateEntryPoint",
            0x21DE074: "KEYMASTER: TA_OpenSessionEntryPoint",
            0x21DE1C4: "KEYMASTER: TA_InvokeCommandEntryPoint",
            0x21DF358: "KEYMASTER: km_init_ability",
            0x21EA494: "KEYMASTER: in tee_task_entry after invokeCommand",
            0x21DE520: "KEYMASTER: TA_CloseSessionEntryPoint",
        }

        self._logger = get_logger("tc_progress_monitor")

        for bp_address in self._breakpoints.keys():
            self._register_handler_for_breakpoint(bp_address, self._handle_bp)

    def _handle_bp(self):
        bp_address = self._context.target.read_register("pc")
        self._logger.info(f"pc={hex(bp_address)}: {self._breakpoints[bp_address]}")

        # inside strncpy loop to see TA load string
        if bp_address == 0xC001D110:
            # read char for loaded TAs
            # TODO: read string directly from memory (need pyh addr for that)
            self._logger.info(f"char {repr(chr(self._context.target.read_register('x14')))}")

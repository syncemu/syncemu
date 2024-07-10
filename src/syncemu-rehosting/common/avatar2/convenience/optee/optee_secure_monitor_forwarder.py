from typing import Dict

from avatar2 import QemuTarget, GDBTarget, Target

from common import get_logger
from common.avatar2 import ConvenientAvatar
from common.avatar2.convenience import TemporaryCodeExecutionHelper
from common.avatar2.convenience.optee.structs import OpteeMsgArg
from common.avatar2.keystone import aarch64_asm
from common.avatar2.convenience import BreakpointHandlingRunner


class NonOpteeBreakpointHit(Exception):
    pass

class OpteeBooted(Exception):
    pass


class WorldSwitch(Exception):
    pass


class OpteeSecureMonitorForwarder:

    def __init__(
            self,
            avatar: ConvenientAvatar,
            emulator: BreakpointHandlingRunner,
            physical_device: GDBTarget,
            smc_emulator_entrypoint: int,
            smc_physical_device_entrypoint: int,
            nsec_shared_memory_address: int,
            avatar_tempdir: str,
    ):
        # thats the rehosted TZOS binary
        self.emulator = emulator
        # thats where the TZOS jumps to when a SMC happens
        self.smc_emulator_entrypoint = smc_emulator_entrypoint

        # thats the real device normal world
        self.physical_device = physical_device
        # thats where the NW real device has its SMC instruction
        self.smc_physical_device_entrypoint = smc_physical_device_entrypoint

        # possibility to skip a number of SMC calls before forwarding is activated
        # may help to skip setup SMCs during boot of physical device
        self.skip_optee_calls_until_ready = 0

        # this will be initialized when the emulator TZOS is booted and returns
        # thats the address to jump to if a SMC from real device NW goes to rehosted
        self.emulator_eret_entrypoint = None

        self.avatar = avatar

        self._logger = get_logger("smc_forwarding_runner")

        self.nsec_shared_memory_address = nsec_shared_memory_address
        self.shm_va_physical_device = 0x12c00000
        self.shm_va_emulator = 0x42000000

        # we register a memory forwarder for the shared memory region of the rehosted
        # all writes will be forwarded to the physical device's virtual address
        self.shared_memory = avatar.add_memory_forwarder_peripheral(nsec_shared_memory_address, 0x200000, va_machineDst=self.shm_va_physical_device, machineDst=physical_device, name="shared_mem")


        # used to execute the smc-stubs
        # the address must be in the range of the "real" SM
        self._temporary_code_execution_helper = TemporaryCodeExecutionHelper(
            self.emulator, avatar, 0xda6dabac, 0x1000
        )
    def cont_emulator(self, fail_silently: bool = False):
        """
        Continue execution until one of the following events occurs:
        
        - TZOS booted (returns None)
        - OP-TEE TZOS command finished (returns parsed result)
        
        """

        self.emulator._target.set_breakpoint(self.smc_emulator_entrypoint)

        while True:
            self.emulator.cont()

            # in case there's other breakpoints set, we pass control back to the caller
            if self.emulator._target.regs.pc != self.smc_emulator_entrypoint:
                # we clean up our own breakpoint to make sure that, should the method never be called again, the
                # remaining script is not affected
                self.emulator._target.remove_breakpoint(self.smc_emulator_entrypoint)

                # raising an exception is an easy-to-understand and -implement way to pass back control to the caller
                raise NonOpteeBreakpointHit()

            # looks like we've received an SMC from the TZOS -- let's handle it
            try:
                self._handle_smc_from_tzos()

            except OpteeBooted:
                # the boot does not return any data we could read out (makes sense, as the address of the shared
                # memory is passed upon command execution only), so there's nothing we could return here
                # as far as we could observe, this won't be reached if the TZOS hasn't been able to complete the boot,
                # though, so false positives *should* not occur
                return
            except WorldSwitch:
                return

    def cont_physical_device(self):
        """
        Continue execution until one of the following events occurs:

        - NW of physical device booted

        """

        self.physical_device.set_breakpoint(self.smc_physical_device_entrypoint)

        while True:
            self.physical_device.cont()
            self.physical_device.wait()

            if self.physical_device.regs.pc != self.smc_physical_device_entrypoint:
                self.physical_device.remove_breakpoint(self.smc_physical_device_entrypoint)

                raise NonOpteeBreakpointHit()
            
            # received SMC from NW of physical device
            try:
                self._handle_smc_from_nw()

            except WorldSwitch:
                return

    def _handle_smc_from_tzos(self):
        # we use a system of callbacks to handle SMCs
        # these are defined in a dict which can later be queried
        # each of these handlers has full access to the instance's state, and can e.g., write to memory, or read
        # registers
        smc_handlers: Dict[int, callable] = {
            # we just eret for now, but will likely add some more sophisticated functionality later on
            0x80000000: self._handle_default_smc,
            # value detected by trial-and-error
            0xBE000000: self._handle_return_from_tzos_boot,
            # optee returns that func-identifier after initializing to load a TA
            # seems to be some sort of "switch to NW" and request RPC-Service
            0xBE000005: self._handle_call_from_tzos_to_normal_world,
        }

        # first argument in x0 is always the function identifier -> see calling convention for more info
        # unknown function identifier return is 0xffffffff

        # for now we only need the function identifier
        function_identifier = self.emulator._target.read_register("x0")
        #print(hex(function_identifier))

        # in case we don't find a registered callback, we fall back to the default handler
        try:
            smc_callback = smc_handlers[function_identifier]
        except KeyError:
            smc_callback = self._handle_default_smc

        self._logger.info(f"SW->SMC->NW {hex(function_identifier)} received, handler: {smc_callback.__name__}")

        # run callback
        smc_callback()

    def _write_assembly_to_memory(self, assembler_code: str):
        # this returns a bytestring
        # every instruction consists of four bytes
        assembly = aarch64_asm(assembler_code)

        # we need an array of int values
        # therefore, we need to iterate over that bytestring, convert every
        # TODO: optimize this: we likely can avoid a loop here
        for i in range(len(assembly) // 4):
            offset = i * 4
            chunk = int.from_bytes(assembly[offset : offset + 4], "little")
            self.emulator._target.write_memory(self.smc_emulator_entrypoint + offset, 4, chunk)

        return len(assembly)

    def _write_eret_to_memory(self):
        self._write_assembly_to_memory("eret")

    def _handle_default_smc(self):
        self._write_eret_to_memory()

    def _handle_return_from_tzos_boot(self):
        # the address which we use to pass control back to the TZOS through eret is sent to us once in this SMC
        # we have to memorize it therefore
        assert self.emulator_eret_entrypoint is None

        self.emulator_eret_entrypoint = self.emulator._target.read_register("x1")

        self._logger.info(f"tee_entry_std address (used to reply to eret): {hex(self.emulator_eret_entrypoint)}")

        # pass back control to calling script
        raise OpteeBooted()

    def _handle_call_from_tzos_to_normal_world(self):

        # first read out the optee_msg_arg struct from emulator memory
        # and write it to physical device memory
        optee_msg_arg = None
        optee_msg_arg = OpteeMsgArg.from_memory(self.emulator._target, self.shm_va_emulator)
        print("emulator")
        print(optee_msg_arg)
        print(optee_msg_arg.params)

        # third sync registers and continue
        self.forward_to_physical_device(optee_msg_arg)

    def _handle_smc_from_nw(self):
        smc_handlers: Dict[int, callable] = {
            # do OPTEE_SMC_CALL_WITH_ARG
            0x32000012: self._handle_call_with_args,
            # return values after RPC
            0x32000003: self._handle_return_from_rpc_call,
        }

        # for now we only need the function identifier
        function_identifier = self.physical_device.read_register("x0")

        # in case we don't find a registered callback, we fall back to the default handler
        try:
            smc_callback = smc_handlers[function_identifier]
        except KeyError:
            smc_callback = self._handle_default_smc_physical_device

        self._logger.info(f"NW->SMC->SW {hex(function_identifier)} received, handler: {smc_callback.__name__}")

        # run callback
        smc_callback()

    def _handle_default_smc_physical_device(self):
        # this should just be continued on the physical device
        return

    def _handle_return_from_rpc_call(self):
        # we are in forwarding mode if < 0
        if self.skip_optee_calls_until_ready > 0:
            return
        else:
            self._handle_call_with_args()


    def _handle_call_with_args(self):
        # skip some smc calls if defined
        if self.skip_optee_calls_until_ready > 0:
            self.skip_optee_calls_until_ready -= 1
            return
        else:
            if self.skip_optee_calls_until_ready == 0:
                self.skip_optee_calls_until_ready -= 1
                self._logger.info("Forwarding SMCs now...")

            optee_msg_arg = None
            if self.physical_device.read_register("x2") != 0x0:
                optee_msg_arg = OpteeMsgArg.from_memory(self.physical_device, self.shm_va_physical_device)
                print("physical device")
                print(optee_msg_arg)
                print(optee_msg_arg.params)

            pa_optee_msg_arg = self.physical_device.read_register("x2")
            self.forward_to_emulator(optee_msg_arg, pa_optee_msg_arg)

    def forward_to_emulator(self, optee_msg_arg, pa_optee_msg_arg):

        assert self.emulator_eret_entrypoint is not None

        if optee_msg_arg is not None:
            #self.emulator.write_memory(self.shm_va_emulator, len(optee_msg_arg.to_bytes()), optee_msg_arg.to_bytes(), raw=True)
            self.emulator._target.write_register("x2", pa_optee_msg_arg)
        else:
            self.emulator._target.write_register("x2", self.physical_device.read_register("x2"))

        funcid = self.physical_device.read_register("x0")
        self.emulator._target.write_register("x1", self.physical_device.read_register("x1"))
        self.emulator._target.write_register("x3", self.physical_device.read_register("x3"))

        assembler_code = f"""
            movz x0, #0x03C4
            movk x0, #0x6000, lsl #16
            msr spsr_el3, x0
            movz x0, #{hex(self.emulator_eret_entrypoint & 0xFFFF)}
            movk x0, #{hex((self.emulator_eret_entrypoint >> 16) & 0xFFFF)}, lsl #16
            msr elr_el3, x0
            movz x0, #{hex(funcid & 0xFFFF)}
            movk x0, #{hex((funcid >> 16) & 0xFFFF)}, lsl #16
            eret
        """
        self._write_assembly_to_memory(assembler_code)

        raise WorldSwitch()

    def forward_to_physical_device(self, optee_msg_arg):

        # TODO: currently not implemented for newer OP-TEE version
        """
        # this is just one instruction after the smc happened -> 0xc030eb2c
        physical_device_eret_entrypoint = self.smc_physical_device_entrypoint + 0x4

        if optee_msg_arg is not None:
            pass
            #self.physical_device.write_memory(self.shm_va_physical_device, len(optee_msg_arg.to_bytes()), optee_msg_arg.to_bytes(), raw=True)

        # the function identifier in r0 is not used for NW
        self.physical_device.write_register("r0", self.emulator.read_register("r1"))
        self.physical_device.write_register("r1", self.emulator.read_register("r2"))
        # there is a cookie write it to r2
        # if not just let the r2 register as is
        if self.physical_device.read_register("r5") != 0x0:
            self.physical_device.write_register("r2", self.physical_device.read_register("r5"))
        else:
            self.physical_device.write_register("r2", self.physical_device.read_register("r3"))
        self.physical_device.write_register("r3", self.emulator.read_register("r4"))

        self.physical_device.write_register("pc", physical_device_eret_entrypoint)
        """

        raise WorldSwitch()

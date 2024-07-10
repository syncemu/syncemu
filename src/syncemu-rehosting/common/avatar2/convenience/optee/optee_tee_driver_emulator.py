from avatar2 import Target

from .non_secure_shared_memory_manager import NonSecureSharedMemoryManager
from .optee_tee_supplicant_emulator import OpteeTeeSupplicantEmulator
from ..secure_monitor_emulator import TzosCommandFinished
from ..tee_driver_emulator import TeeDriverEmulator
from .... import get_logger


class UnsupportedRpcFuncReceivedError(Exception):
    """
    Raised whenever an RPC is received that is not (yet) supported by the TEE driver emulator.
    """

    def __init__(self, rpc_id):
        self.rpc_id = rpc_id

    def __str__(self):
        return f"Unsupported RPC function received: {hex(self.rpc_id)}"


class OpteeTeeDriverEmulator(TeeDriverEmulator):
    def __init__(self, target: Target, nsec_shared_memory_address: int, trusted_apps_dir: str, avatar_tempdir: str):
        self.target = target

        # list of all shared memories we currently manage
        self.normal_world_shm_manager = NonSecureSharedMemoryManager(nsec_shared_memory_address)

        self.tee_supplicant_emulator = OpteeTeeSupplicantEmulator(
            self.target, self.normal_world_shm_manager, trusted_apps_dir, avatar_tempdir
        )

        self.logger = get_logger("tee-driver-emu")

    def handle_rpc(self):
        # first we see which RPC_FUNC is sent according to optee_handle_rpc
        # the rpc_func is given through x1 register, it defines which service is requested
        rpc_func = self.target.read_register("x1")
        self.logger.info("Handling RPC call: %s", hex(rpc_func))

        if rpc_func == 0xFFFF0000:
            # here we are in OPTEE_SMC_RPC_FUNC_ALLOC --> TZOS wants to allocate shared memory
            self.handle_memory_allocation()

        elif rpc_func == 0xFFFF0005:
            # OPTEE_SMC_RPC_FUNC_CMD: calls with this ID would normally be forwarded towards the TEE supplicant
            self.tee_supplicant_emulator.handle_rpc_cmd()

        elif rpc_func == 0xFFFF0002:
            # OPTEE_SMC_RPC_FUNC_FREE
            self.handle_memory_free()

        elif rpc_func == 0x0:
            # OPTEE_SMC_RETURN_OK: our first SMC call (0x32000004) is finished
            # TODO: handle failed commands, too
            # TODO: parse and return actual result instead of None
            raise TzosCommandFinished(None)

        else:
            if rpc_func == 0x1:
                error_message = "OPTEE_SMC_RETURN_ETHREAD_LIMIT"
            elif rpc_func == 0x2:
                error_message = "OPTEE_SMC_RETURN_EBUSY"
            elif rpc_func == 0x3:
                error_message = "OPTEE_SMC_RETURN_ERESUME"
            elif rpc_func == 0x4:
                error_message = "OPTEE_SMC_RETURN_EBADADDR"
            elif rpc_func == 0x5:
                error_message = "OPTEE_SMC_RETURN_EBADCMD"
            elif rpc_func == 0x6:
                error_message = "OPTEE_SMC_RETURN_ENOMEM"
            elif rpc_func == 0x7:
                error_message = "OPTEE_SMC_RETURN_ENOTAVAIL"
            else:
                # should not be reached
                error_message = "Unknown error code"

            self.logger.critical(error_message)

            # it usually makes no sense to continue execution when an RPC is received which we can't handle
            # therefore, we can just terminate execution here automatically instead of spamming log messages forever
            raise UnsupportedRpcFuncReceivedError(rpc_func)

        # we need to set x0 to OPTEE_SMC_CALL_RETURN_FROM_RPC for the TZOS
        self.target.write_register("x0", 0x32000003)

    def handle_memory_allocation(self):
        # the size is given in x2 which is sent to a function tee_shm_alloc (make sure to use the backuped value)
        shm_size = self.target.read_register("x2")
        self.logger.debug("TZOS wants to allocate shared memory, size: %s", hex(shm_size))

        next_shm = self.normal_world_shm_manager.allocate_bytes(shm_size)

        # TODO some sort of mechanism to manage the shared memory
        # To return we sent a physical address pointing inside shared memory in register x1/x2
        # for now fixed "random" value
        self.target.write_register("x1", 0x0)
        self.target.write_register("x2", next_shm)

        # in x4/x5 we need to put the corresponding virtual address
        # for now thats a fixed value from virt-optee
        self.target.write_register("x4", 0x0)
        self.target.write_register("x5", next_shm)
        # it seems like we also can sent the physical address and leave out virtual address

        # set other registers to zero so we get no error 0x3
        self.target.write_register("x3", 0x0)
        self.target.write_register("x6", 0x0)

    def handle_memory_free(self):
        reg_x2 = self.target.read_register("x2")
        reg_x3 = self.target.read_register("x3")
        shm_addr = (reg_x2 << 32) + reg_x3
        self.normal_world_shm_manager.free(shm_addr)
        for reg in ["x0", "x1", "x2", "x3", "x4", "x5", "x6"]:
            self.target.write_register(reg, 0x0)

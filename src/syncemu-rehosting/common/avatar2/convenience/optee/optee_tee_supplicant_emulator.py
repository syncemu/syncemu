import ctypes
import os
from typing import Dict

from avatar2 import Target

from common import get_logger
from .non_secure_shared_memory_manager import NonSecureSharedMemoryManager
from .structs import OpteeMsgArg


class UnknownCommandError(Exception):
    def __init__(self, command_id: int):
        self.command_id = command_id

    def __str__(self):
        return f"cannot handle unknown command ID {self.command_id}"


class OpteeSecureStorageEmulator:
    """
    Emulates the OP-TEE secure storage file system, usually mounted as /data/tee in the OP-TEE normal world.

    The TEE supplicant receives RPCs from the TZOS, which resemble regular file system operations like read, write, ...

    This class parses the RPC argument, executes the requested operation and returns the appropriate result.
    """

    def __init__(self, target: Target, secure_storage_dir: str):
        self.target = target

        self.logger = get_logger("secure_storage_emu")

        # current value of next filedescriptor if requested
        # we start with a random 5 and just count up
        self.next_fd = 5

        # dictionary to keep track of opened files with their filedescriptors
        self.descriptor_to_file_map: Dict[int, str] = {}

        self.secure_storage_dir = secure_storage_dir

        # make sure the directory exists
        os.makedirs(secure_storage_dir, exist_ok=True)

    def _resolve_path(self, fname: str):
        # all (valid) paths are "absolute", i.e., they're in the root of the secure storage filesystem maintained by
        # the normal world
        # we can just strip all the leading /, and build the path we use internally
        if fname[0] == "/":
            return os.path.join(self.secure_storage_dir, fname.lstrip("/"))

        # all other paths shall be rejected until a proper (safe) path resolution is implemented
        raise RuntimeError(f"unsupported filename received from sw: {fname}")

    def _add_entry_for_file(self, fname: str) -> int:
        fd = self.next_fd
        self.next_fd += 1
        self.descriptor_to_file_map[fd] = fname
        return fd

    def _read_fname_from_msg_arg(self, optee_msg_arg: OpteeMsgArg):
        data = self.target.read_memory(optee_msg_arg.params[1].param.c, optee_msg_arg.params[1].param.b, raw=True)
        return ctypes.create_string_buffer(data).value.decode()

    def _handle_mrf_open(self, shm_address: int, optee_msg_arg: OpteeMsgArg):
        fname = self._read_fname_from_msg_arg(optee_msg_arg)

        resolved_path = self._resolve_path(fname)

        # return a fd based on the fname
        # check if file already exists if not take action to create it
        try:
            with open(resolved_path):
                # check if we already have that file in our dictionary
                for fd, file_name in self.descriptor_to_file_map.items():
                    if file_name == fname:
                        # if so then just write the corresponding fd
                        optee_msg_arg.params[2].param.a = fd
                        break

                else:
                    # if not, add a new entry, using the unresolved filename as a key, and assign the next available fd
                    self.descriptor_to_file_map[self.next_fd] = fname
                    # and write it in the return buffer
                    optee_msg_arg.params[2].param.a = self.next_fd
                    # increment next_fd so a new file will get another address
                    self.next_fd += 1

                # file exists and is tracked -> return success
                optee_msg_arg.ret = 0x0

        except FileNotFoundError:
            self.logger.warning("Tried to open file which does not exist... let it create")
            # set filedescriptor to zero
            optee_msg_arg.params[2].param.a = 0x0
            # file does not exist -> return a error value not sure what this stands for
            optee_msg_arg.ret = 0xFFFF0008

    def _handle_mrf_create(self, shm_address: int, optee_msg_arg: OpteeMsgArg):
        fname = self._read_fname_from_msg_arg(optee_msg_arg)

        resolved_path = self._resolve_path(fname)

        # check if we already have that file in our dictionary
        for fd, file_name in self.descriptor_to_file_map.items():
            if file_name == fname:
                # if so then just write the corresponding fd
                optee_msg_arg.params[2].param.a = fd
                break

        else:
            # register the file in the storage, and assign the next fd to it
            fd = self._add_entry_for_file(fname)

            # and write it in the return buffer
            optee_msg_arg.params[2].param.a = fd

        # create file in blob
        # we should never be here if the file exists so its ok to use x
        with open(resolved_path, "x"):
            pass

        # set arg->ret to TEEC_SUCCESS
        optee_msg_arg.ret = 0x0

    def _handle_mrf_read(self, shm_address: int, optee_msg_arg: OpteeMsgArg):
        # get corresponding file path
        fd = int(optee_msg_arg.params[0].param.b)
        read_file_path = self.descriptor_to_file_map[fd]

        resolved_path = self._resolve_path(read_file_path)

        with open(resolved_path, "rb") as storage_file:
            # offset to read from file
            offs = optee_msg_arg.params[0].param.c
            # goto offset
            storage_file.seek(offs)
            # size to read is the size of the given buffer in param[1].b
            size_to_read = int(optee_msg_arg.params[1].param.b)
            chunk = storage_file.read(size_to_read)
            # write to given buffer address in param[1].a
            self.target.write_memory(optee_msg_arg.params[1].param.a, size_to_read, chunk, raw=True)
            # set arg->ret to TEEC_SUCCESS
            optee_msg_arg.ret = 0x0

    def _handle_mrf_write(self, shm_address: int, optee_msg_arg: OpteeMsgArg):
        # get corresponding file path
        fd = int(optee_msg_arg.params[0].param.b)
        write_file_path = self.descriptor_to_file_map[fd]

        resolved_path = self._resolve_path(write_file_path)

        with open(resolved_path, "r+b") as storage_file:
            # offset where to write in file
            offs = optee_msg_arg.params[0].param.c
            storage_file.seek(offs)
            # size to write is the size of the given buffer
            size_to_write = int(optee_msg_arg.params[1].param.b)
            # read data from buffer with address in param[1].a
            chunk = self.target.read_memory(optee_msg_arg.params[1].param.a, size_to_write, raw=True)
            storage_file.write(chunk)
            # set arg->ret to TEEC_SUCCESS
            optee_msg_arg.ret = 0x0

    def handle_rpc(self, shm_address: int, optee_msg_arg: OpteeMsgArg):
        # depending on the value a of first parameter we do different things
        if optee_msg_arg.params[0].param.a == 0:
            # we are in OPTEE_MRF_OPEN
            # the file name to open
            self._handle_mrf_open(shm_address, optee_msg_arg)

        elif optee_msg_arg.params[0].param.a == 1:
            # we are in OPTEE_MRF_CREATE
            self._handle_mrf_create(shm_address, optee_msg_arg)

        elif optee_msg_arg.params[0].param.a == 3:
            # we are in OPTEE_MRF_READ
            self._handle_mrf_read(shm_address, optee_msg_arg)

        elif optee_msg_arg.params[0].param.a == 4:
            # we are in OPTEE_MRF_WRITE
            self._handle_mrf_write(shm_address, optee_msg_arg)


class OpteeTeeSupplicantEmulator:
    def __init__(
        self,
        target: Target,
        normal_world_shm_manager: NonSecureSharedMemoryManager,
        trusted_apps_dir: str,
        avatar_tempdir: str,
    ):
        self.target = target
        self.normal_world_shm_manager = normal_world_shm_manager

        self.secure_storage_emulator = OpteeSecureStorageEmulator(
            self.target, os.path.join(avatar_tempdir, "secure-storage")
        )

        self.trusted_apps_dir = trusted_apps_dir

        self.logger = get_logger("tee-supplicant-emu")

    def handle_rpc_cmd(self):
        # here we are in OPTEE_SMC_RPC_FUNC_CMD
        # in x2/x3 is the address of the shared memory for the request
        # in TA loading we expect it to be the same as the one we sent in the allocation

        shm_address = (self.target.read_register("x2") << 32) + self.target.read_register("x3")
        self.logger.debug("TZOS sent CMD with shared memory at %s", hex(shm_address))

        # we decode the memory content as it is a optee_msg_arg struct
        optee_msg_arg = OpteeMsgArg.from_memory(self.target, shm_address)

        self.logger.debug("Received command: %s", hex(optee_msg_arg.cmd))
        self.logger.debug("number of params: %s", hex(len(optee_msg_arg.params)))

        # act according to the cmd similar to handle_rpc_func_cmd
        if optee_msg_arg.cmd == 6:
            # here we are in OPTEE_MSG_RPC_CMD_SHM_ALLOC
            # arg->params[0].u.value.a = Type of SHM --> not used for now...
            # arg->params[0].u.value.b = size of SHM that should be allocated
            self.logger.debug(f"Received SHM alloc command")

            # allocate new memory according to the requested size
            shm = self.normal_world_shm_manager.allocate_bytes(optee_msg_arg.params[0].param.b)

            # we need to set attr and the tmem properties example from rpc.c
            # arg->params[0].attr = OPTEE_MSG_ATTR_TYPE_TMEM_OUTPUT |OPTEE_MSG_ATTR_NONCONTIG; ## 0x20a
            # arg->params[0].u.tmem.buf_ptr = pa;
            # arg->params[0].u.tmem.size = sz;
            # arg->params[0].u.tmem.shm_ref = (unsigned long)shm;

            # TODO: currently we use the OpteeMsgParamValue struct but acutally we should use OpteeMsgParamTmem instead
            # attr -> only set OPTEE_MSG_ATTR_TYPE_TMEM_OUTPUT
            # we dont get into msg_param_mobj_from_noncontig (for us its not important that we use noncontig memory) at thread_optee_smc.c
            # directly call mobj_shm_alloc
            # working with nonconti memory is too complex
            optee_msg_arg.params[0].attr = 0xA

            # buf_ptr -> maybe inside 0x42000000 size 0x00200000
            # this seems to work! look in core_pbuf_is from core_mmu.c
            # D/TC:0 0 add_phys_mem:586 TEE_SHMEM_START type NSEC_SHM 0x42000000 size 0x00200000
            optee_msg_arg.params[0].param.a = shm

            # size
            # just set the requested size, we always return enough memory
            optee_msg_arg.params[0].param.b = optee_msg_arg.params[0].param.b

            # shm_ref
            # this is normally the virtual address for the NW but the TZOS just uses this as cookie
            # so we just set the buf_ptr address again for easier memory management
            optee_msg_arg.params[0].param.c = shm

            # set arg->ret to TEEC_SUCCESS
            optee_msg_arg.ret = 0x0

        elif optee_msg_arg.cmd == 7:
            # here we are in OPTEE_MSG_RPC_CMD_SHM_FREE
            self.logger.debug(f"Received SHM free command")

            # Remove the requested shared memory (saved in value b)
            self.normal_world_shm_manager.free(optee_msg_arg.params[0].param.b)

            # set arg->ret to TEEC_SUCCESS
            optee_msg_arg.ret = 0x0

        elif optee_msg_arg.cmd == 0:
            # here we are in OPTEE_MSG_RPC_CMD_LOAD_TA
            # decode the uuid from the parameters, and create a hex string
            value_a = int.to_bytes(optee_msg_arg.params[0].param.a, 8, "little")
            value_b = int.to_bytes(optee_msg_arg.params[0].param.b, 8, "little")
            uuid = (value_a + value_b).hex()

            self.logger.debug(f"Received load TA command for UUID {uuid}")

            # create the filename of the ta-binary by inserting correct dash lines
            ta_file_name = uuid[:8] + "-" + uuid[8:12] + "-" + uuid[12:16] + "-" + uuid[16:20] + "-" + uuid[20:] + ".ta"

            # now just open the requested TA-binary
            with open(os.path.join(self.trusted_apps_dir, ta_file_name), "rb") as ta_file:
                # read the ta-binary file
                ta_file_content = ta_file.read()
                # the size is just the len of the content
                size_of_ta_file = len(ta_file_content)

            if optee_msg_arg.params[1].param.b != 0:
                # if we got a buffer fill it with the binary
                self.target.write_memory(optee_msg_arg.params[1].param.c, size_of_ta_file, ta_file_content, raw=True)
                # if no buffer was provided just tell the TZOS how big it must be

            # write size of ta_file in param[1].b
            optee_msg_arg.params[1].param.b = size_of_ta_file

            # set arg->ret to TEEC_SUCCESS
            optee_msg_arg.ret = 0x0

        elif optee_msg_arg.cmd == 2:
            # here we are in OPTEE_MSG_RPC_CMD_FS
            # it seems we do some filesystem operations

            self.logger.debug(f"Received filesystem command {hex(optee_msg_arg.params[0].param.a)}")

            # secure storage is going to do the heavy lifting
            self.secure_storage_emulator.handle_rpc(shm_address, optee_msg_arg)

        else:
            raise UnknownCommandError(optee_msg_arg.cmd)

        # set return values in shared memory buffer
        # set arg->ret_origin to TEEC_ORIG_COMMS
        optee_msg_arg.ret_origin = 0x2

        optee_msg_arg_bytes = optee_msg_arg.to_bytes()
        self.target.write_memory(shm_address, len(optee_msg_arg_bytes), optee_msg_arg_bytes, raw=True)

        # in x1/x2 we have to put the address of the shared memory where our return values are located
        self.target.write_register("x1", 0x0)
        self.target.write_register("x2", shm_address)
        # virt-optee also set this address in x4/x5 but it seems we really do not need that

        # set other registers to zero
        for reg in ["x3", "x4", "x5", "x6"]:
            self.target.write_register(reg, 0x0)

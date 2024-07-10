import io
import struct
from typing import Union, List

from avatar2 import Target


class Struct:
    @classmethod
    def from_memory(cls, target: Target, start_address: int):
        """
        Read struct from memory, using Avatar2's remote memory interface.

        The advantage of implementing this instead of, e.g., a from_bytes method, is that the caller does not need to
        know the amount of bytes that will be consumed. This allows for implementing reading recursively, with
        dynamically sized elements like arrays of child structs whose size is defined by another member.

        :param target: target to use for reading memory
        :param start_address: address to start reading at
        """

        raise NotImplementedError()

    def serialize(self, buffer: io.BytesIO):
        """
        Serialize all attributes recursively into the provided buffer object.
        """

        raise NotImplementedError()

    def to_bytes(self) -> bytes:
        """
        Serialize all attributes recursively into a buffer, and return its contents as bytes.
        """

        buffer = io.BytesIO()
        self.serialize(buffer)

        buffer.seek(0, io.SEEK_SET)

        return buffer.read()


class TC_Param(Struct):
    def __init__(self, a: int, b: int):
        self.a = a
        self.b = b

    @classmethod
    def from_memory(cls, target: Target, start_address: int):
        fmt = "<II"

        num_bytes_consumed = struct.calcsize(fmt)
        data = target.read_memory(start_address, num_bytes_consumed, raw=True)
        a, b = struct.unpack(fmt, data)

        return cls(a, b)

    def serialize(self, buffer: io.BytesIO):
        data = struct.pack("<II", self.a, self.b)
        buffer.write(data)

    def __repr__(self):
        return f"<{self.__class__.__name__} a={hex(self.a)} b={hex(self.b)}>"


class TC_Operation(Struct):
    def __init__(self, paramTypes: int, params: List[TC_Param]):
        self.paramTypes = paramTypes
        self.params = params

    @classmethod
    def from_memory(cls, target: Target, start_address: int):
        fmt = "<I"

        paramTypes = target.read_memory(start_address, 0x4)
        params: List[TC_Param] = []
        for i in range(4):
            param = TC_Param.from_memory(target, start_address + 0x4 + i * 0x8)
            params.append(param)

        return cls(paramTypes, params)

    def serialize(self, buffer: io.BytesIO):
        data = struct.pack("<I", self.paramTypes)
        buffer.write(data)
        for param in self.params:
            param.serialize(buffer)

    def __repr__(self):
        return (
            f"<{self.__class__.__name__} paramTypes={hex(self.paramTypes)} {''.join(f'params={repr(self.params)}') }>"
        )


class TC_NS_SMC_CMD(Struct):
    def __init__(
        self,
        uuid_phys: int,
        cmd_id: int,
        dev_file_id: int,
        context_id: int,
        agent_id: int,
        operation_phys: int,
        login_method: int,
        login_data: int,
        err_origin: int,
        ret_val: int,
        event_nr: int,
        remap: int,
        uid: int,
        started: int,
    ):
        self.uuid_phys = uuid_phys
        self.cmd_id = cmd_id
        self.dev_file_id = dev_file_id
        self.context_id = context_id
        self.agent_id = agent_id
        self.operation_phys = operation_phys
        self.login_method = login_method
        self.login_data = login_data
        self.err_origin = err_origin
        self.ret_val = ret_val
        self.event_nr = event_nr
        self.remap = remap
        self.uid = uid
        self.started = started

    @classmethod
    def from_memory(cls, target: Target, start_address: int):
        # first, we have to parse the constant part of the struct
        # this includes the number of parameters, which we can then use to parse all the parameters in a loop

        # 14x int for the normal struct members + 17 Bytes for uuid +  1x int for operation.paramTypes
        struct_fmt = "<IIIIIIIIIIIIII"
        struct_size = struct.calcsize(struct_fmt)

        header_data = target.read_memory(start_address, struct_size, raw=True)
        (
            uuid_phys,
            cmd_id,
            dev_file_id,
            context_id,
            agent_id,
            operation_phys,
            login_method,
            login_data,
            err_origin,
            ret_val,
            event_nr,
            remap,
            uid,
            started,
        ) = struct.unpack(struct_fmt, header_data)

        return cls(
            uuid_phys,
            cmd_id,
            dev_file_id,
            context_id,
            agent_id,
            operation_phys,
            login_method,
            login_data,
            err_origin,
            ret_val,
            event_nr,
            remap,
            uid,
            started,
        )

    def serialize(self, buffer: io.BytesIO):
        data = struct.pack(
            "<IIIIIIIIIIIIII",
            self.uuid_phys,
            self.cmd_id,
            self.dev_file_id,
            self.context_id,
            self.agent_id,
            self.operation_phys,
            self.login_method,
            self.login_data,
            self.err_origin,
            self.ret_val,
            self.event_nr,
            self.remap,
            self.uid,
            self.started,
        )
        buffer.write(data)

    def __repr__(self):
        attrs = {
            attr: getattr(self, attr)
            for attr in [
                "uuid_phys",
                "cmd_id",
                "dev_file_id",
                "context_id",
                "agent_id",
                "operation_phys",
                "login_method",
                "login_data",
                "err_origin",
                "ret_val",
                "event_nr",
                "remap",
                "uid",
                "started",
            ]
        }

        return f"<{self.__class__.__name__} {' '.join(f'{k}={hex(v)}' for k, v in attrs.items())}>"

import io
import struct
from typing import Union, List

from avatar2 import Target

from ..struct import Struct


class OpteeMsgParamTmem(Struct):
    def __init__(self, buf_ptr: int, size: int, shm_ref: int):
        self.buf_ptr = buf_ptr
        self.size = size
        self.shm_ref = shm_ref

    @classmethod
    def from_memory(cls, target: Target, start_address: int):
        fmt = "<QQQ"

        num_bytes_consumed = struct.calcsize(fmt)

        data = target.read_memory(start_address, num_bytes_consumed)
        buf_ptr, size, shm_ref = struct.unpack(fmt, data)

        return cls(buf_ptr, size, shm_ref), num_bytes_consumed

    def serialize(self, buffer: io.BytesIO):
        data = struct.pack("<QQQ", self.buf_ptr, self.size, self.shm_ref)
        buffer.write(data)

    def __repr__(self):
        return (
            f"<{self.__class__.__name__} "
            f"buf_ptr={hex(self.buf_ptr)} size={hex(self.size)} shm_ref={hex(self.shm_ref)}>"
        )


class OpteeMsgParamRmem(Struct):
    def __init__(self, offset: int, size: int, shm_ref: int):
        self.offset = offset
        self.size = size
        self.shm_ref = shm_ref

    @classmethod
    def from_memory(cls, target: Target, start_address: int):
        fmt = "<QQQ"

        num_bytes_consumed = struct.calcsize(fmt)

        data = target.read_memory(start_address, num_bytes_consumed, raw=True)
        offset, size, shm_ref = struct.unpack(fmt, data)

        return cls(offset, size, shm_ref), num_bytes_consumed

    def serialize(self, buffer: io.BytesIO):
        data = struct.pack("<QQQ", self.offset, self.size, self.shm_ref)
        buffer.write(data)

    def __repr__(self):
        return (
            f"<{self.__class__.__name__} "
            f"offset={hex(self.offset)} size={hex(self.size)} shm_ref={hex(self.shm_ref)}>"
        )


class OpteeMsgParamValue(Struct):
    def __init__(self, a: int, b: int, c: int):
        self.a = a
        self.b = b
        self.c = c

    @classmethod
    def from_memory(cls, target: Target, start_address: int):
        fmt = "<QQQ"

        num_bytes_consumed = struct.calcsize(fmt)

        data = target.read_memory(start_address, num_bytes_consumed, raw=True)
        buf_ptr, size, shm_ref = struct.unpack(fmt, data)

        return cls(buf_ptr, size, shm_ref), num_bytes_consumed

    def serialize(self, buffer: io.BytesIO):
        data = struct.pack("<QQQ", self.a, self.b, self.c)
        buffer.write(data)

    def __repr__(self):
        return f"<{self.__class__.__name__} a={hex(self.a)} b={hex(self.b)} c={hex(self.c)}>"


class OpteeMsgParam(Struct):
    def __init__(self, attr: int, param: Union[OpteeMsgParamTmem, OpteeMsgParamRmem, OpteeMsgParamValue]):
        self.attr = attr
        self.param = param

    @classmethod
    def from_memory(cls, target: Target, start_address: int):
        fmt = "<Q"

        num_bytes_consumed = struct.calcsize(fmt)
        data = target.read_memory(start_address, num_bytes_consumed, raw=True)
        attr = struct.unpack(fmt, data)[0]

        # TODO: differentiate between attributes and return the right object
        # for now, we'll hardcode one of them
        param, bytes_consumed_by_param = OpteeMsgParamValue.from_memory(target, start_address + num_bytes_consumed)

        # the param also consumed a bunch of bytes, and we should inform the caller about them
        num_bytes_consumed += bytes_consumed_by_param

        return cls(attr, param), num_bytes_consumed

    def serialize(self, buffer: io.BytesIO):
        data = struct.pack("<Q", self.attr)
        buffer.write(data)

        self.param.serialize(buffer)

    def __repr__(self):
        return f"<{self.__class__.__name__} attr={hex(self.attr)} param={repr(self.param)}>"


class OpteeMsgArg(Struct):
    def __init__(
        self,
        cmd: int,
        func: int,
        session: int,
        cancel_id: int,
        pad: int,
        ret: int,
        ret_origin: int,
        params: List[OpteeMsgParam],
    ):
        self.cmd = cmd
        self.func = func
        self.session = session
        self.cancel_id = cancel_id
        self.pad = pad
        self.ret = ret
        self.ret_origin = ret_origin
        self.params = params

    @classmethod
    def from_memory(cls, target: Target, start_address: int):
        # first, we have to parse the constant part of the struct
        # this includes the number of parameters, which we can then use to parse all the parameters in a loop
        struct_fmt = "<IIIIIIII"
        struct_size = struct.calcsize(struct_fmt)

        header_data = target.read_memory(start_address, struct_size, raw=True)
        cmd, func, session, cancel_id, pad, ret, ret_origin, num_params = struct.unpack(struct_fmt, header_data)

        # now that we know the number of parameters, we can parse them one at a time
        params_offset = struct_size
        params: List[OpteeMsgParam] = []

        for _ in range(num_params):
            param, num_bytes_consumed = OpteeMsgParam.from_memory(target, start_address + params_offset)
            params.append(param)

            # we let the factory return the actual number of bytes consumed by it and use that to increase the offset
            # for the next iteration
            params_offset += num_bytes_consumed

        return cls(cmd, func, session, cancel_id, pad, ret, ret_origin, params)

    def serialize(self, buffer: io.BytesIO):
        data = struct.pack(
            "<IIIIIIII",
            self.cmd,
            self.func,
            self.session,
            self.cancel_id,
            self.pad,
            self.ret,
            self.ret_origin,
            len(self.params),
        )
        buffer.write(data)

        for param in self.params:
            param.serialize(buffer)

    def __repr__(self):
        attrs = {
            attr: getattr(self, attr) for attr in ["cmd", "func", "session", "cancel_id", "pad", "ret", "ret_origin"]
        }
        attrs["num_params"] = len(self.params)

        return f"<{self.__class__.__name__} {' '.join(f'{k}={hex(v)}' for k, v in attrs.items())}>"

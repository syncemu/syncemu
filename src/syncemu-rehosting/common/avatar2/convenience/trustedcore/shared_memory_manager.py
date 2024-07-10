from typing import Dict

from .... import get_logger
from ..rehosting_context import RehostingContext


class MemoryRangeNotFoundError(Exception):
    """
    Raised when a user tries to run an operation on a memory range which is unknown to the manager (e.g., freeing an
    address that doesn't represent the start of a memory range previously allocated).
    """

    pass


class SharedMemoryManager:
    """
    The management of the regions is considered an implementation detail, so the caller doesn't need to worry about
    this. Same goes for the allocation algorithm.

    TODO: so far, we merely hope that all memory that will ever be required won't exceed the memory range
        this should probably be checked by the code at some point
    """

    def __init__(self, context: RehostingContext):

        self._context = context
        self.start_address = self._context.shared_memory.address + 0x10000

        # this value defines the starting address for newly allocated ranges
        # so far, new memory ranges are always appended inside the managed shared memory
        # TODO: support allocating previously free'd ranges
        self.next_unused_address = self.start_address

        self.logger = get_logger("shared-mem-manager")

    def allocate_bytes(self, data: bytes) -> int:
        """
        Allocate a memory range that is *at least* the number of bytes in size provided by the caller.

        :param data: the data which should be stored in SHM
        """

        # write data to memory at next unused address
        self._context.shared_memory.forwarded_to.write_memory(self.next_unused_address, len(data), data, raw=True)
        ret = self.next_unused_address
        self.next_unused_address += len(data)

        return ret

    # def free(self, address: int):
    #     self.logger.debug(f"freeing memory range at address {hex(address)}")

    # TODO: be less greedy and free old memory properly to allow new memory to be allocated within those areas
    # try:
    #     del self.memory_map[address]
    # except KeyError:
    #     raise MemoryRangeNotFoundError()

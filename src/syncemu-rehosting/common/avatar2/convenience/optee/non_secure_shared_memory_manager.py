from typing import Dict

from .... import get_logger


class MemoryRangeNotFoundError(Exception):
    """
    Raised when a user tries to run an operation on a memory range which is unknown to the manager (e.g., freeing an
    address that doesn't represent the start of a memory range previously allocated).
    """

    pass


class SharedMemoryEntry:
    """
    Represents an entry in the memory manager.
    """

    def __init__(self, num_pages: int):
        """
        :param num_pages: number of pages to allocate (allocation only ever happens page-aligned); the page size is defined in the memory manager
        """

        self.num_pages = num_pages


class NonSecureSharedMemoryManager:
    """
    In OP-TEE, communication between the normal and secure worlds happens mainly through a small set of general purpose
    registers as well as large memory range in which areas can be allocated by the TZOS, allowing the CA to pass
    parameters that wouldn't fit into the registers only.

    The memory range that can be used for this is hardcoded in the binary. If memory addresses are returned to the
    secure world which are not contained in this map, the secure world will return some not-really-helpful error
    messages. Therefore, the caller must pass the address at which we can start to "allocate" memory.

    Note that the class does not provide any form of Avatar peripheral. The caller must make sure that the address
    passed as start address points to some mapped memory range.

    The management of the regions is considered an implementation detail, so the caller doesn't need to worry about
    this. Same goes for the allocation algorithm.

    TODO: so far, we merely hope that all memory that will ever be required won't exceed the memory range
        this should probably be checked by the code at some point
    """

    def __init__(self, start_address: int, page_size: int = 0x1000):
        """
        :param start_address: address from which on memory will be allocated
        :param page_size: as we allocate memory only page-aligned, we must know the size of one page
        """

        self.start_address = start_address
        self.page_size = page_size

        # the concrete memory management is considered an implementation detail
        # so far, a simple dict that maps the physical addresses to the actual memory entries works well enough
        self.memory_map: Dict[int, SharedMemoryEntry] = {}

        # this value defines the starting address for newly allocated ranges
        # so far, new memory ranges are always appended inside the managed shared memory
        # TODO: support allocating previously free'd ranges
        self.new_memory_allocation_address = start_address

        self.logger = get_logger("nsec-shared-mem-manager")

    def allocate_pages(self, num_pages: int) -> int:
        """
        Allocate some pages of memory.
        The page size was defined when the class was initialized.

        :param num_pages: number of pages to allocate
        """

        new_address = self.new_memory_allocation_address
        size_in_bytes = self.page_size * num_pages

        self.logger.debug(
            f"allocating {hex(num_pages)} page(s) of memory "
            f"(size: {hex(size_in_bytes)} bytes, address: {hex(new_address)})"
        )

        self.memory_map[new_address] = SharedMemoryEntry(size_in_bytes)
        self.new_memory_allocation_address += size_in_bytes

        return new_address

    def allocate_bytes(self, num_bytes: int) -> int:
        """
        Allocate a memory range that is *at least* the number of bytes in size provided by the caller.
        The allocation algorithm takes care of page alignment.

        :param num_bytes: number of bytes the range must provide *at least*
        """

        # align to page size (basically "rounding up" to a multiple of the page size)
        num_pages = num_bytes // self.page_size

        if num_bytes % self.page_size != 0:
            num_pages += 1

        self.logger.debug(f"allocating {hex(num_bytes)} bytes (requires {hex(num_pages)} pages)")

        # now, we can let the page allocation method handle the rest
        return self.allocate_pages(num_pages)

    def free(self, address: int):
        self.logger.debug(f"freeing memory range at address {hex(address)}")

        # TODO: be less greedy and free old memory properly to allow new memory to be allocated within those areas
        try:
            del self.memory_map[address]
        except KeyError:
            raise MemoryRangeNotFoundError()

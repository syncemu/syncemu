import typing


if typing.TYPE_CHECKING:
    from .rehosting_context import RehostingContext
    from .struct import Struct


class CallIntoTzosStrategy:
    """
    Interface for strategies that implement calls into the TZOS

    Implementation of the strategy pattern.
    """

    def execute_tzos_command(self, struct: "Struct") -> "Struct":
        raise NotImplementedError()

    def parse_return_value(self) -> "Struct":
        raise NotImplementedError()


class CallIntoTzosStrategyBase(CallIntoTzosStrategy):
    """
    Abstract base class that implements a common constructor.
    """

    def __init__(self, rehosting_context: "RehostingContext"):
        self._context = rehosting_context

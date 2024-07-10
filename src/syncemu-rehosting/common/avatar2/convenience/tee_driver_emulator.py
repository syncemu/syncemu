class UnsupportedRpcFuncReceivedError(Exception):
    """
    Raised whenever an RPC is received that is not (yet) supported by the TEE driver emulator.
    """

    def __init__(self, rpc_id):
        self.rpc_id = rpc_id

    def __str__(self):
        return f"Unsupported RPC function received: {hex(self.rpc_id)}"


class TeeDriverEmulator:
    """
    Interface for normal-world emulation.
    """

    def handle_rpc(self):
        """
        Handle call from secure into normal world.
        """

        raise NotImplementedError()

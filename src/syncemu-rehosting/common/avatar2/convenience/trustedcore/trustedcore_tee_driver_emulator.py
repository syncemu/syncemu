from common.avatar2.convenience.secure_monitor_emulator import TzosCommandFinished
from common.avatar2.convenience.tee_driver_emulator import TeeDriverEmulator


class TrustedCoreTeeDriverEmulator(TeeDriverEmulator):
    def handle_rpc(self):
        raise TzosCommandFinished(None)

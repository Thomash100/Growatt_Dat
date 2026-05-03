"""Future Growatt command encoder.

TODO: Add a command abstraction for verified local output-power commands. Keep
all real hardware commands behind the safety layer and never expose raw command
payloads through the web UI.
"""


class GrowattCommandClient:
    async def set_output_power(self, target_power_w: int) -> None:
        raise NotImplementedError("Real Growatt commands are not implemented in version 1.")


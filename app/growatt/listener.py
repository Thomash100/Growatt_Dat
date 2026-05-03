"""Future local Growatt packet listener.

TODO: Add a UDP/TCP listener for Growatt NEO/NOAH traffic once the local
protocol handling is implemented. This module must not send raw commands to
real devices until the decoder and safety layers are verified.
"""


class GrowattListener:
    async def start(self) -> None:
        raise NotImplementedError("Growatt listener is planned for a later milestone.")


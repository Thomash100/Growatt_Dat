"""Future Growatt protocol decoder.

TODO: Decode local Growatt NEO/NOAH frames into app.models.Measurement objects.
Version 1 intentionally uses the mock device only and performs no real protocol
decoding.
"""


class GrowattDecoder:
    def decode(self, raw_payload: bytes) -> None:
        raise NotImplementedError("Growatt protocol decoding is not implemented in version 1.")


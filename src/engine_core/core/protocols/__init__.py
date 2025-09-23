# Protocols Module
from .protocol import *
from .protocol_builder import ProtocolBuilder

# Lazy import to avoid database dependencies at import time
def __getattr__(name):
    if name == 'Protocol':
        from ...models.protocol import Protocol
        return Protocol
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = [
    'ProtocolBuilder'
]
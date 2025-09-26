import sys

sys.path.insert(0, "/home/mau/engine/engine-core/src")

try:
    from engine_core.core.protocols.protocol_builder import ProtocolBuilder

    print("ProtocolBuilder import successful")
    # Test basic instantiation
    builder = ProtocolBuilder()
    print(f"Builder created: {type(builder)}")
    # Test build
    protocol = builder.with_id("test_protocol").with_name("Test Protocol").build()
    print(f"Protocol created: {protocol.id}")
except Exception as e:
    print(f"Error: {e}")
    import traceback

    traceback.print_exc()

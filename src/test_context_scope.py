from engine_core.core.protocols.protocol import ContextScope
print('ContextScope values:')
for scope in ContextScope:
    print(f'  {scope.name}: {scope.value}')
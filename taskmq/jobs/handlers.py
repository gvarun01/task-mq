import hashlib
import inspect

HANDLERS = {}
HANDLER_HASHES = {}

def register_handler(name):
    def decorator(func):
        HANDLERS[name] = func
        try:
            source = inspect.getsource(func)
            # Simple normalization
            source_hash = hashlib.sha256(source.encode('utf-8')).hexdigest()
            HANDLER_HASHES[name] = source_hash
        except (OSError, TypeError):
            # Can happen in REPL or dynamic code
            HANDLER_HASHES[name] = None
        return func
    return decorator

def get_handler(name):
    return HANDLERS.get(name)

def get_handler_hash(name):
    return HANDLER_HASHES.get(name)

# Register a persistent dummy handler for testing
@register_handler("dummy")
def dummy_handler(job):
    print(f"[DUMMY HANDLER] Executed for job {job.id} with payload: {job.payload}")

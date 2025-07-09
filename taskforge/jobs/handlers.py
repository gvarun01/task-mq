HANDLERS = {}

def register_handler(name):
    def decorator(func):
        HANDLERS[name] = func
        return func
    return decorator

def get_handler(name):
    return HANDLERS.get(name)

# Register a persistent dummy handler for testing
@register_handler("dummy")
def dummy_handler(job):
    print(f"[DUMMY HANDLER] Executed for job {job.id} with payload: {job.payload}")

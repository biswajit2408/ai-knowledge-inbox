from contextvars import ContextVar

# Holds the current request's ID so every log line written while handling
# that request can include it, without passing it through every function.
request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)

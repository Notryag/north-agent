from langgraph.checkpoint.memory import InMemorySaver


def get_default_checkpointer():
    """Return the default checkpoint saver for the lite runtime."""
    return InMemorySaver()

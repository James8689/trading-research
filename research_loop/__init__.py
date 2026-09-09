"""Durable, research-only agent loop.

The package deliberately contains no market-data acquisition or order APIs.  It
coordinates bounded reasoning tasks and stores their reviewable packets/results.
"""

__all__ = ["DEFAULT_CONFIG", "ResultValidationError", "ResearchLoop", "ResearchLoopError"]


def __getattr__(name):
    # Keep ``python -m research_loop.runner`` free of runpy's double-import
    # warning while retaining convenient package-level imports.
    if name in __all__:
        from . import runner
        return getattr(runner, name)
    raise AttributeError(name)

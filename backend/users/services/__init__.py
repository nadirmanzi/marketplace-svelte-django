"""Business logic services package for the `users` app.

Note: do not import submodules at package import time to avoid heavy
third-party/Django imports during unit-test discovery. Import specific
service modules (e.g. ``from users.services import auth_service``) when
they are needed at runtime.
"""

__all__ = [
    # submodules are imported lazily by consumers
]

# Ensures the Celery app is always loaded when Django starts, so that
# `shared_task` resolves to our configured app (correct broker, eager mode
# in tests) rather than falling back to Celery's unconfigured default app.
from .celery import app as celery_app

__all__ = ('celery_app',)

import json
import logging
import traceback
from datetime import datetime, timezone


class JSONFormatter(logging.Formatter):
    """
    Renders log records as single-line JSON so they're easy to ingest into
    CloudWatch / Datadog / ELK without a parsing layer.
    """

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            'timestamp': datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'request_id': getattr(record, 'request_id', None),
        }
        if record.exc_info:
            payload['exception'] = ''.join(traceback.format_exception(*record.exc_info))
        return json.dumps(payload)

import json
import logging
import traceback


class JSONFormatter(logging.Formatter):
    """Structured JSON log formatter used in production.

    Plain text is easier to read in a dev terminal, but production log
    aggregators (CloudWatch, Loki, Datadog) all expect one JSON object per
    line so fields can be indexed and queried.
    """

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if record.exc_info:
            payload["exception"] = "".join(traceback.format_exception(*record.exc_info))
        if hasattr(record, "request_id"):
            payload["request_id"] = record.request_id
        return json.dumps(payload)

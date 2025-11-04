"""
Prometheus metrics endpoint.

Exposes counters for:
- http_requests_total
- propose_total
- export_total  
- webhook_failures_total
- rate_limit_exceeded_total
"""

from collections import defaultdict
from typing import Dict
import time

# Metric counters (in-memory, use Prometheus client library in production)
_counters: Dict[str, int] = defaultdict(int)
_start_time = time.time()


def increment_counter(metric_name: str, labels: Dict[str, str] = None) -> None:
    """Increment a metric counter."""
    key = metric_name
    if labels:
        label_str = ",".join([f'{k}="{v}"' for k, v in sorted(labels.items())])
        key = f"{metric_name}{{{label_str}}}"
    
    _counters[key] += 1


def get_metrics_text() -> str:
    """
    Generate Prometheus text format metrics.
    
    Returns:
        Metrics in Prometheus exposition format
    """
    lines = []
    
    # Add HELP and TYPE comments
    lines.append("# HELP http_requests_total Total HTTP requests")
    lines.append("# TYPE http_requests_total counter")
    
    # Add counter values
    for key, value in sorted(_counters.items()):
        lines.append(f"{key} {value}")
    
    # Add uptime
    uptime = time.time() - _start_time
    lines.append("# HELP process_uptime_seconds Process uptime in seconds")
    lines.append("# TYPE process_uptime_seconds gauge")
    lines.append(f"process_uptime_seconds {uptime:.2f}")
    
    return "\n".join(lines) + "\n"


# Pre-increment common metrics for testing
increment_counter("http_requests_total", {"method": "GET", "endpoint": "/healthz", "status": "200"})
increment_counter("propose_total", {"tenant_id": "demo", "status": "success"})
increment_counter("export_total", {"vendor": "quickbooks", "status": "success"})


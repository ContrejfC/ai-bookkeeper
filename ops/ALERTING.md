# Alerting & Monitoring - Production Ops Guide

This document provides guidance for setting up production alerts and monitoring for AI Bookkeeper.

## 📊 Key Metrics to Monitor

### 1. Application Health

- **5xx Error Rate**
  - Threshold: > 2% for 5 minutes
  - Action: Page on-call engineer
  - Query: `rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])`

- **4xx Error Rate** (excluding 401/404)
  - Threshold: > 5% for 10 minutes
  - Action: Alert in Slack
  - Query: `rate(http_requests_total{status=~"4..", status!="401", status!="404"}[5m])`

### 2. Latency

- **P95 Latency**
  - Threshold: > 1 second for 5 minutes
  - Action: Alert in Slack
  - Critical: > 3 seconds → Page

- **P99 Latency**
  - Threshold: > 5 seconds for 5 minutes
  - Action: Investigate performance

### 3. Resource Usage

- **Memory Usage**
  - Threshold: > 80% for 10 minutes
  - Action: Scale up or investigate leak
  - Critical: > 90% → Page

- **CPU Usage**
  - Threshold: > 70% for 15 minutes
  - Action: Consider scaling
  - Critical: > 85% → Alert

- **Database Connections**
  - Threshold: > 80% of pool size
  - Action: Review pool configuration or scale

### 4. Business Metrics

- **Transactions Processed**
  - Threshold: < 100 in last hour (during business hours)
  - Action: Check for ingestion issues

- **Categorization Failures**
  - Threshold: > 10% failure rate
  - Action: Review LLM service status

- **Export Failures** (QBO/Xero)
  - Threshold: > 5% failure rate
  - Action: Check external API status

### 5. External Dependencies

- **Stripe API Availability**
  - Threshold: Any 5xx from Stripe
  - Action: Monitor and retry

- **QuickBooks API Availability**
  - Threshold: > 10 failures in 10 minutes
  - Action: Check QBO status page

- **LLM API (OpenAI/Anthropic)**
  - Threshold: > 5 rate limit errors in 5 minutes
  - Action: Review usage tier

## 🔔 Alert Configuration Examples

### Google Cloud Monitoring

```yaml
# 5xx Error Rate Alert
display_name: "High 5xx Error Rate"
conditions:
  - display_name: "5xx rate > 2%"
    condition_threshold:
      filter: |
        resource.type = "cloud_run_revision"
        metric.type = "run.googleapis.com/request_count"
        metric.label.response_code_class = "5xx"
      comparison: COMPARISON_GT
      threshold_value: 0.02
      duration: 300s
      aggregations:
        - alignment_period: 60s
          per_series_aligner: ALIGN_RATE
notification_channels:
  - projects/PROJECT_ID/notificationChannels/CHANNEL_ID
```

```yaml
# Memory Usage Alert
display_name: "High Memory Usage"
conditions:
  - display_name: "Memory > 80%"
    condition_threshold:
      filter: |
        resource.type = "cloud_run_revision"
        metric.type = "run.googleapis.com/container/memory/utilizations"
      comparison: COMPARISON_GT
      threshold_value: 0.80
      duration: 600s
notification_channels:
  - projects/PROJECT_ID/notificationChannels/CHANNEL_ID
```

```yaml
# P95 Latency Alert
display_name: "High Request Latency"
conditions:
  - display_name: "P95 > 1s"
    condition_threshold:
      filter: |
        resource.type = "cloud_run_revision"
        metric.type = "run.googleapis.com/request_latencies"
      comparison: COMPARISON_GT
      threshold_value: 1000  # milliseconds
      duration: 300s
      aggregations:
        - alignment_period: 60s
          per_series_aligner: ALIGN_DELTA
          cross_series_reducer: REDUCE_PERCENTILE_95
notification_channels:
  - projects/PROJECT_ID/notificationChannels/CHANNEL_ID
```

### Datadog

```json
{
  "name": "High 5xx Error Rate",
  "type": "metric alert",
  "query": "sum(last_5m):sum:http.requests{status:5xx}.as_count() / sum:http.requests{*}.as_count() > 0.02",
  "message": "5xx error rate is {{value}}% @pagerduty",
  "tags": ["env:production", "service:ai-bookkeeper"],
  "priority": 1
}
```

```json
{
  "name": "High Memory Usage",
  "type": "metric alert",
  "query": "avg(last_10m):avg:container.memory.usage{service:ai-bookkeeper} / avg:container.memory.limit{service:ai-bookkeeper} > 0.80",
  "message": "Memory usage is {{value}}% @slack-alerts",
  "tags": ["env:production", "service:ai-bookkeeper"],
  "priority": 2
}
```

## 📱 Notification Channels

### Severity Levels

| Severity | Channel | Response Time |
|----------|---------|---------------|
| Critical | PagerDuty | 15 minutes |
| High | Slack + Email | 1 hour |
| Medium | Slack | 4 hours |
| Low | Email | Next day |

### Recommended Channels

1. **PagerDuty** - Critical alerts only
2. **Slack #alerts** - High/Medium alerts
3. **Email** - Low priority, summaries

## 🏃 Runbooks

### High 5xx Error Rate

1. Check Cloud Run logs: `gcloud run services logs tail ai-bookkeeper-api`
2. Look for recurring patterns in errors
3. Check database connectivity
4. Review recent deployments
5. Scale up if under capacity

### High Memory Usage

1. Check for memory leaks in logs
2. Review connection pool usage
3. Check for large data loads
4. Consider scaling vertically
5. Restart service if leak suspected

### Database Connection Pool Exhausted

1. Check current connections: `SELECT count(*) FROM pg_stat_activity;`
2. Review slow queries: `SELECT * FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;`
3. Increase pool size if needed
4. Check for connection leaks in code

### LLM Rate Limiting

1. Check usage dashboard in OpenAI/Anthropic console
2. Review request volume in logs
3. Implement exponential backoff
4. Consider upgrading tier if systematic

## 📈 Dashboard Recommendations

### Application Dashboard

- Request rate (by endpoint)
- Error rate (by status code)
- Latency percentiles (P50, P95, P99)
- Active instances
- Memory/CPU usage

### Business Dashboard

- Transactions processed (hourly/daily)
- Categorization accuracy
- Exports completed
- Active subscriptions
- Revenue metrics

### Infrastructure Dashboard

- Database connections
- Query performance
- Cache hit rate
- External API latency
- Queue depth (if using background jobs)

## 🔍 Log Analysis Queries

### Find errors by request ID

```bash
gcloud logging read "resource.type=cloud_run_revision AND jsonPayload.request_id=REQUEST_ID" --limit 50
```

### Find slow requests

```bash
gcloud logging read "resource.type=cloud_run_revision AND httpRequest.latency>1s" --limit 20
```

### Find authentication failures

```bash
gcloud logging read "resource.type=cloud_run_revision AND httpRequest.status=401" --limit 20
```

## 🚨 On-Call Procedures

### P0 - Critical (Service Down)

1. Acknowledge alert within 15 minutes
2. Check service health: `/readyz` endpoint
3. Review Cloud Run metrics
4. Check recent deployments
5. Rollback if recent deploy
6. Escalate to senior eng if unresolved in 30min

### P1 - High (Degraded Performance)

1. Acknowledge within 1 hour
2. Review error rates and latency
3. Check for resource constraints
4. Review slow query logs
5. Scale if needed
6. Create incident report

### P2 - Medium (Minor Issues)

1. Acknowledge within 4 hours
2. Review and triage
3. Create Jira ticket
4. Fix in next sprint if not urgent

## 📊 SLI/SLO Definitions

### Service Level Indicators (SLIs)

- **Availability**: % of successful requests (non-5xx)
- **Latency**: P95 response time
- **Correctness**: % of successful categorizations

### Service Level Objectives (SLOs)

| Metric | Target | Measurement Window |
|--------|--------|-------------------|
| Availability | 99.5% | 30 days |
| P95 Latency | < 1s | 7 days |
| P99 Latency | < 3s | 7 days |
| Categorization Accuracy | > 85% | 30 days |

### Error Budget

- **Monthly Budget**: 0.5% of requests (for 99.5% availability)
- **Action on Burn**: Freeze non-critical features, focus on reliability

## 🔐 Security Alerts

- **Unusual login patterns**: > 10 failed logins from same IP in 5min
- **API key usage**: Unexpected spike in API calls
- **Data export**: Large volume downloads
- **Admin actions**: Any production data modification

## 📝 Post-Incident Review Template

1. **Incident Summary**: What happened?
2. **Timeline**: Key events
3. **Root Cause**: Why did it happen?
4. **Resolution**: How was it fixed?
5. **Action Items**: What to improve?
6. **Lessons Learned**: What did we learn?

---

**Remember**: The goal is early detection and quick resolution. Tune alerts to minimize false positives while catching real issues early.


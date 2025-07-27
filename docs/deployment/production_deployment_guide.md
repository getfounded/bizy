# Production Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying the Business Logic Orchestrator in production environments, including scaling recommendations, security configurations, and operational best practices.

## Prerequisites

- Kubernetes 1.24+ or Docker Swarm
- Redis 6.2+ cluster
- Monitoring stack (Prometheus, Grafana)
- TLS certificates
- Load balancer

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                   Load Balancer                          │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                  Kubernetes Cluster                      │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────┐           │
│  │  Orchestrator   │    │  Orchestrator   │    ...    │
│  │    Pod (1)      │    │    Pod (2)      │           │
│  └─────────────────┘    └─────────────────┘           │
│                                                         │
│  ┌─────────────────┐    ┌─────────────────┐           │
│  │ Adapter Pool    │    │ Adapter Pool    │    ...    │
│  │  (LangChain)    │    │  (Temporal)     │           │
│  └─────────────────┘    └─────────────────┘           │
│                                                         │
│  ┌─────────────────────────────────────────┐           │
│  │          Redis Cluster (HA)              │           │
│  └─────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────┘
```

## Deployment Steps

### 1. Container Images

Build production images:

```dockerfile
# Dockerfile
FROM python:3.12-slim as builder

WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev

FROM python:3.12-slim

WORKDIR /app
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY business_logic_orchestrator ./business_logic_orchestrator

ENV PYTHONUNBUFFERED=1
ENV WORKERS=4

EXPOSE 8000
CMD ["uvicorn", "business_logic_orchestrator.api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "$WORKERS"]
```

### 2. Kubernetes Deployment

```yaml
# orchestrator-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: business-logic-orchestrator
  namespace: orchestrator
spec:
  replicas: 3
  selector:
    matchLabels:
      app: orchestrator
  template:
    metadata:
      labels:
        app: orchestrator
    spec:
      containers:
      - name: orchestrator
        image: orchestrator:latest
        ports:
        - containerPort: 8000
        env:
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: orchestrator-secrets
              key: redis-url
        - name: LOG_LEVEL
          value: "INFO"
        resources:
          requests:
            cpu: 500m
            memory: 512Mi
          limits:
            cpu: 2000m
            memory: 2Gi
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: orchestrator-service
  namespace: orchestrator
spec:
  selector:
    app: orchestrator
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

### 3. Adapter Deployment

Deploy framework adapters:

```yaml
# adapter-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: langchain-adapter
  namespace: orchestrator
spec:
  replicas: 2
  selector:
    matchLabels:
      app: langchain-adapter
  template:
    metadata:
      labels:
        app: langchain-adapter
    spec:
      containers:
      - name: adapter
        image: orchestrator-adapter:langchain
        env:
        - name: FRAMEWORK
          value: "langchain"
        - name: ORCHESTRATOR_URL
          value: "http://orchestrator-service"
        - name: LANGCHAIN_API_KEY
          valueFrom:
            secretKeyRef:
              name: langchain-secrets
              key: api-key
        resources:
          requests:
            cpu: 250m
            memory: 256Mi
          limits:
            cpu: 1000m
            memory: 1Gi
```

### 4. Redis Cluster Setup

Deploy Redis with high availability:

```yaml
# redis-cluster.yaml
apiVersion: redis.redis.opstreelabs.in/v1beta1
kind: RedisCluster
metadata:
  name: orchestrator-redis
  namespace: orchestrator
spec:
  clusterSize: 3
  kubernetesConfig:
    image: redis:6.2-alpine
    resources:
      requests:
        cpu: 101m
        memory: 128Mi
      limits:
        cpu: 101m
        memory: 128Mi
  redisExporter:
    enabled: true
    image: oliver006/redis_exporter:latest
  storage:
    volumeClaimTemplate:
      spec:
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 10Gi
```

## Configuration Management

### 1. Environment Variables

```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: orchestrator-config
  namespace: orchestrator
data:
  LOG_LEVEL: "INFO"
  WORKERS: "4"
  EVENT_BUS_BATCH_SIZE: "100"
  RULE_CACHE_TTL: "300"
  HEALTH_CHECK_INTERVAL: "30"
  METRICS_PORT: "9090"
```

### 2. Secrets Management

```yaml
# secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: orchestrator-secrets
  namespace: orchestrator
type: Opaque
stringData:
  redis-url: "redis://user:pass@redis-cluster:6379"
  langchain-api-key: "your-api-key"
  temporal-auth-token: "your-token"
```

## Scaling Configuration

### 1. Horizontal Pod Autoscaling

```yaml
# hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: orchestrator-hpa
  namespace: orchestrator
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: business-logic-orchestrator
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  - type: Pods
    pods:
      metric:
        name: rule_evaluation_rate
      target:
        type: AverageValue
        averageValue: "1000"
```

### 2. Vertical Pod Autoscaling

```yaml
# vpa.yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: orchestrator-vpa
  namespace: orchestrator
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: business-logic-orchestrator
  updatePolicy:
    updateMode: "Auto"
  resourcePolicy:
    containerPolicies:
    - containerName: orchestrator
      maxAllowed:
        cpu: 4
        memory: 4Gi
      minAllowed:
        cpu: 100m
        memory: 128Mi
```

## Monitoring Setup

### 1. Prometheus Configuration

```yaml
# prometheus-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: monitoring
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
    scrape_configs:
    - job_name: 'orchestrator'
      kubernetes_sd_configs:
      - role: pod
        namespaces:
          names:
          - orchestrator
      relabel_configs:
      - source_labels: [__meta_kubernetes_pod_label_app]
        action: keep
        regex: orchestrator.*
      - source_labels: [__meta_kubernetes_pod_name]
        target_label: pod
      - source_labels: [__meta_kubernetes_namespace]
        target_label: namespace
```

### 2. Grafana Dashboards

Import provided dashboards:
- Business Logic Overview
- Framework Performance
- Rule Evaluation Metrics
- Error Analysis

### 3. Alerting Rules

```yaml
# alerts.yaml
groups:
- name: orchestrator
  rules:
  - alert: HighErrorRate
    expr: rate(orchestrator_errors_total[5m]) > 0.1
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: High error rate detected
      
  - alert: FrameworkDown
    expr: up{job="orchestrator"} == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: Framework adapter is down
```

## Security Hardening

### 1. Network Policies

```yaml
# network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: orchestrator-netpol
  namespace: orchestrator
spec:
  podSelector:
    matchLabels:
      app: orchestrator
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: orchestrator
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: orchestrator
  - to:
    - podSelector:
        matchLabels:
          app: redis
  - ports:
    - protocol: TCP
      port: 443  # External APIs
```

### 2. Pod Security Policy

```yaml
# psp.yaml
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: orchestrator-psp
spec:
  privileged: false
  allowPrivilegeEscalation: false
  requiredDropCapabilities:
  - ALL
  volumes:
  - 'configMap'
  - 'emptyDir'
  - 'projected'
  - 'secret'
  - 'downwardAPI'
  - 'persistentVolumeClaim'
  runAsUser:
    rule: 'MustRunAsNonRoot'
  seLinux:
    rule: 'RunAsAny'
  fsGroup:
    rule: 'RunAsAny'
```

## Performance Tuning

### 1. Connection Pooling

```python
# config/production.py
CONNECTION_POOL_CONFIG = {
    "min_size": 10,
    "max_size": 100,
    "timeout": 30,
    "retry_attempts": 3,
    "retry_delay": 1
}

REDIS_POOL_CONFIG = {
    "max_connections": 200,
    "health_check_interval": 30
}
```

### 2. Caching Strategy

```python
CACHE_CONFIG = {
    "rule_cache_ttl": 300,  # 5 minutes
    "framework_cache_ttl": 60,  # 1 minute
    "result_cache_ttl": 30,  # 30 seconds
    "cache_size": 10000
}
```

### 3. Batch Processing

```python
BATCH_CONFIG = {
    "event_batch_size": 100,
    "event_batch_timeout": 1.0,
    "rule_batch_size": 50,
    "framework_batch_size": 25
}
```

## Disaster Recovery

### 1. Backup Strategy

- Daily Redis snapshots
- Rule configuration backups
- Event log archival
- Framework state persistence

### 2. Recovery Procedures

1. **Redis Failure**:
   - Failover to replica
   - Restore from snapshot
   - Replay event log

2. **Orchestrator Failure**:
   - Kubernetes auto-restart
   - Load balancer rerouting
   - State recovery from Redis

3. **Framework Failure**:
   - Circuit breaker activation
   - Fallback rule execution
   - Manual intervention alerts

## Operational Runbook

### Health Checks

```bash
# Check orchestrator health
curl http://orchestrator-service/health

# Check adapter status
kubectl get pods -n orchestrator -l app=langchain-adapter

# Check Redis cluster
redis-cli -h redis-cluster ping
```

### Common Operations

```bash
# Scale orchestrator
kubectl scale deployment business-logic-orchestrator --replicas=5

# Update configuration
kubectl apply -f configmap.yaml
kubectl rollout restart deployment business-logic-orchestrator

# View logs
kubectl logs -n orchestrator -l app=orchestrator --tail=100
```

### Troubleshooting

1. **High Latency**:
   - Check CPU/memory usage
   - Review connection pool metrics
   - Analyze slow queries

2. **Rule Failures**:
   - Check rule syntax
   - Verify framework connectivity
   - Review error logs

3. **Event Backlog**:
   - Scale event processors
   - Increase batch size
   - Check Redis performance

## Maintenance Windows

### Rolling Updates

```bash
# Update orchestrator image
kubectl set image deployment/business-logic-orchestrator \
  orchestrator=orchestrator:v1.2.0 \
  -n orchestrator

# Monitor rollout
kubectl rollout status deployment/business-logic-orchestrator -n orchestrator
```

### Database Maintenance

```bash
# Redis maintenance
redis-cli --cluster check redis-cluster:6379
redis-cli --cluster rebalance redis-cluster:6379
```

## Compliance

### Audit Logging

All operations logged with:
- User identity
- Action performed
- Timestamp
- Result/error

### Data Retention

- Event logs: 90 days
- Audit logs: 7 years
- Metrics: 30 days
- Backups: 30 days

## Support

- Documentation: https://docs.orchestrator.io
- Support: support@orchestrator.io
- Emergency: +1-xxx-xxx-xxxx
---
name: Performance Issue
about: Report performance problems or optimization opportunities
title: '[PERFORMANCE] '
labels: 'performance'
assignees: ''
---

## 🚀 Performance Issue Description

**Component affected:**
- [ ] Sentiment analysis (Gemini API)
- [ ] Reddit data collection
- [ ] Economic events scraping
- [ ] Database operations
- [ ] EUR/USD monitor
- [ ] Docker containers
- [ ] Other: ____________

**Issue type:**
- [ ] Slow response times
- [ ] High memory usage
- [ ] High CPU usage
- [ ] Database performance
- [ ] API rate limiting
- [ ] Container startup time
- [ ] Network latency

## 📊 Performance Metrics

**Current performance:**
- Response time: __ seconds/minutes
- Memory usage: __ MB/GB
- CPU usage: __ %
- Database query time: __ ms/seconds
- API calls per minute: __
- Container startup time: __ seconds

**Expected performance:**
- Target response time: __ seconds/minutes
- Acceptable memory usage: __ MB/GB
- Target CPU usage: __ %

## 🔄 Steps to Reproduce

1. Set up environment with '...'
2. Run component '....'
3. Monitor performance with '....'
4. Observe degradation after '....'

## 📈 Performance Data

**System monitoring output:**
```bash
# Docker stats
docker stats --no-stream

# System resources
top -bn1 | head -20

# Database performance
EXPLAIN ANALYZE your_slow_query;
```

**Profiling results (if available):**
```python
# Python profiling output
cProfile results or other profiling data
```

**API response times:**
```bash
# Example API timing data
curl -w "@curl-format.txt" -s -o /dev/null [API_ENDPOINT]
```

## 🌍 Environment

**System specifications:**
- CPU: [e.g. Intel i7-10700K, 8 cores]
- RAM: [e.g. 16GB DDR4]
- Storage: [e.g. SSD, HDD]
- Network: [e.g. 1Gbps fiber, WiFi]

**Docker environment:**
- Docker version: [e.g. 24.0.6]
- Available memory to containers: [e.g. 8GB]
- CPU limit for containers: [e.g. 4 cores]

**Dataset size:**
- Database size: [e.g. 100MB, 5GB]
- Number of Reddit posts: [e.g. 10,000]
- Number of economic events: [e.g. 1,000]
- Time period analyzed: [e.g. 3 months]

## 📊 Workload Details

**Usage patterns:**
- Monitor interval: [e.g. 30 minutes]
- Concurrent API calls: [e.g. 5]
- Reddit posts per cycle: [e.g. 100]
- Economic events per day: [e.g. 20]

**Data volume:**
- Daily data ingestion: __ MB/GB
- Peak usage hours: [e.g. Market open]
- Sustained load duration: [e.g. 8 hours]

## 🔍 Analysis

**Suspected bottleneck:**
- [ ] Database queries
- [ ] API rate limiting
- [ ] Memory allocation
- [ ] CPU computation
- [ ] Network I/O
- [ ] Disk I/O
- [ ] Container overhead

**Evidence supporting suspicion:**
Provide logs, metrics, or observations that point to the bottleneck.

## 💡 Optimization Ideas

**Potential solutions:**
- [ ] Database indexing
- [ ] Query optimization
- [ ] Caching layer
- [ ] Batch processing
- [ ] Asynchronous operations
- [ ] Resource allocation tuning
- [ ] Algorithm optimization
- [ ] Other: ____________

**Research done:**
- Documentation reviewed: [Links]
- Similar issues found: [Links]
- Optimization techniques considered: [List]

## 🧪 Testing Methodology

**How to measure improvement:**
```bash
# Commands used to benchmark
time python -m news_sentiment.main --test
docker stats --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"
```

**Test scenarios:**
1. Baseline performance test
2. Load testing with increased data
3. Stress testing with concurrent operations

## 📋 Performance Requirements

**Acceptable performance targets:**
- Maximum response time: __ seconds
- Maximum memory usage: __ MB/GB
- Maximum CPU usage: __ %
- Minimum throughput: __ requests/minute

**SLA requirements:**
- Uptime: __ %
- Availability during market hours: __ %
- Maximum downtime: __ minutes/month

## 🔗 Related Issues

- Performance issue #
- Related optimization #
- Similar problem #

## 🚀 Priority and Impact

**Business impact:**
- [ ] Critical - System unusable
- [ ] High - Significant delays
- [ ] Medium - Noticeable slowdown
- [ ] Low - Minor optimization

**User impact:**
- Number of affected users: [e.g. All users, specific use cases]
- Frequency of occurrence: [Always/Often/Sometimes/Rarely]
- Workaround available: [Yes/No]

## 📝 Additional Context

**Historical performance:**
- When did this issue start: [Date/Version]
- Previous performance levels: [Metrics]
- Recent changes that might be related: [Code/Config changes]

**Additional logs:**
```
Include relevant logs that might help identify the performance issue
```

---

**🔧 Note**: For database performance issues, consider including query execution plans. For API issues, include network latency measurements.
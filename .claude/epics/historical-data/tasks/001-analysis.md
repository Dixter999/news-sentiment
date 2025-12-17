---
issue: 11
title: Historical Data - Backfill 3 years of ForexFactory economic events
analyzed: 2025-12-01T17:50:17Z
estimated_hours: 8
parallelization_factor: 1.5
---

# Parallel Work Analysis: Issue #11

## Overview

Collect 3 years of historical economic calendar data from ForexFactory (Jan 2022 - Dec 2024) to build a training dataset for PPO/SAC trading models. The main work is a long-running scraping process with post-processing for sentiment analysis.

## Parallel Streams

### Stream A: Data Collection (ALREADY RUNNING)
**Scope**: Scrape 158 weeks of ForexFactory economic calendar data
**Files**:
- `scripts/backfill_forex_factory.py` (created)
- `scripts/.backfill_checkpoint.json` (checkpoint)
- Database: `economic_events` table
**Agent Type**: python-backend-engineer
**Can Start**: immediately (ALREADY RUNNING)
**Estimated Hours**: 4-6 (wall clock, mostly waiting)
**Dependencies**: none
**Status**: IN PROGRESS - Currently at week 3/158

### Stream B: Data Validation Script
**Scope**: Create validation script to verify collected data quality
**Files**:
- `scripts/validate_backfill.py` (new)
**Agent Type**: python-backend-engineer
**Can Start**: immediately (parallel with A)
**Estimated Hours**: 1
**Dependencies**: none (can run against partial data)

### Stream C: Sentiment Analysis Batch
**Scope**: Analyze sentiment for all collected historical events
**Files**:
- `scripts/analyze_historical_sentiment.py` (new)
- Database: `economic_events.sentiment_score` column
**Agent Type**: python-backend-engineer
**Can Start**: after Stream A completes (or partial runs during)
**Estimated Hours**: 2-3 (depends on Gemini API rate limits)
**Dependencies**: Stream A (needs data to analyze)

### Stream D: Data Export for ML
**Scope**: Export processed data in formats suitable for PPO/SAC training
**Files**:
- `scripts/export_training_data.py` (new)
- `data/training/` directory (exports)
**Agent Type**: python-backend-engineer
**Can Start**: after Stream C completes
**Estimated Hours**: 1
**Dependencies**: Stream A, Stream C

## Coordination Points

### Shared Files
- Database `economic_events` table - Streams A, B, C all access
- No file conflicts expected (different scripts)

### Sequential Requirements
1. Data collection (A) must progress before validation (B) has data to check
2. Data collection (A) must complete before full sentiment analysis (C)
3. Sentiment analysis (C) must complete before ML export (D)

## Conflict Risk Assessment

**Low Risk**: All streams work on separate script files. Database access is read/write safe with SQLAlchemy transactions.

## Parallelization Strategy

**Recommended Approach**: hybrid

```
Timeline:
├─ Stream A: Data Collection ─────────────────────────────> (4-6h, RUNNING)
├─ Stream B: Validation Script ──> (1h, can start now)
│                                    └─ Run validation periodically
├─────────────────────────────────── Stream C: Sentiment ──> (2-3h, after A)
└─────────────────────────────────────────────────────────── Stream D: Export (1h, after C)
```

**Current Status**:
- Stream A is ACTIVELY RUNNING (backfill script)
- Stream B can start NOW
- Streams C and D must wait

## Expected Timeline

**With parallel execution:**
- Wall time: ~7-8 hours (dominated by data collection + sentiment analysis)
- Total work: ~9 hours
- Efficiency gain: ~15%

**Without parallel execution:**
- Wall time: ~9 hours

## Notes

1. **Stream A is already running** - backfill script started, currently processing
2. **Rate limiting is the bottleneck** - both ForexFactory and Gemini API have limits
3. **Checkpointing enabled** - can resume if interrupted
4. **Partial processing possible** - Stream C can run on completed data while A continues
5. **Weekend consideration** - ForexFactory has fewer events on weekends, faster scraping

## Immediate Actions

1. Monitor Stream A progress: `cat scripts/.backfill_checkpoint.json`
2. Optionally start Stream B now to prepare validation
3. Wait for A to complete before starting C
4. Stream D is the final step before ML training can begin

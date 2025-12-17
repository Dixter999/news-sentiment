---
issue: 12
title: Silent Image Download Failures Cause Mass 0 Sentiment Scores
analyzed: 2025-12-02T22:33:18Z
estimated_hours: 6
parallelization_factor: 2.5
---

# Parallel Work Analysis: Issue #12

## Overview

Fix silent image download failures in the Gemini sentiment analyzer that cause 163+ Reddit posts to receive 0.0 sentiment scores. The issue stems from `_download_image()` returning `None` silently, with no logging or metadata tracking, causing fallback to text-only analysis that has insufficient content.

## Parallel Streams

### Stream A: Core Fix - Image Download with Logging & Retry
**Scope**: Fix `_download_image()` to add logging, retry logic, and return failure metadata
**Files**:
- `src/news_sentiment/analyzer/gemini.py` (lines 267-291, 319-337)
**Agent Type**: python-backend-engineer
**Can Start**: immediately
**Estimated Hours**: 2
**Dependencies**: none

**Changes**:
1. Add logging to `_download_image()` exception handler
2. Add retry logic for transient failures (timeout, connection errors)
3. Return structured failure info instead of just `None`
4. Track `image_download_failed` and `failure_reason` in result metadata

### Stream B: Fallback Prompt Improvement
**Scope**: Improve text-only fallback prompt to include image URL context
**Files**:
- `src/news_sentiment/analyzer/gemini.py` (lines 360-386)
**Agent Type**: python-backend-engineer
**Can Start**: immediately
**Estimated Hours**: 1
**Dependencies**: none

**Changes**:
1. Add `image_failed` parameter to `_build_reddit_prompt()`
2. Include image URL in prompt when image download failed
3. Instruct Gemini to analyze based on title/context when image unavailable

### Stream C: Tests for Image Failure Scenarios
**Scope**: Add comprehensive tests for image download failure handling
**Files**:
- `tests/test_gemini_image_failures.py` (new file)
**Agent Type**: python-backend-engineer
**Can Start**: immediately
**Estimated Hours**: 1.5
**Dependencies**: none

**Changes**:
1. Test timeout handling and retry logic
2. Test fallback prompt generation with image context
3. Test metadata tracking for failed downloads
4. Mock network failures and verify proper logging

### Stream D: Reprocessing Script
**Scope**: Create script to identify and reprocess affected posts
**Files**:
- `scripts/reprocess_failed_images.py` (new file)
**Agent Type**: python-backend-engineer
**Can Start**: after Stream A completes
**Estimated Hours**: 1.5
**Dependencies**: Stream A (needs the fixed analyzer)

**Changes**:
1. Query database for posts with "no information" patterns in reasoning
2. Re-attempt analysis with fixed image download logic
3. Log success/failure for each reprocessed post
4. Support dry-run mode and batch processing

## Coordination Points

### Shared Files
- `src/news_sentiment/analyzer/gemini.py` - Streams A & B (coordinate method signatures)
  - **Risk Mitigation**: Stream A modifies `_download_image()` and `analyze_reddit_post()`
  - **Risk Mitigation**: Stream B modifies `_build_reddit_prompt()` only
  - **Coordination**: Stream A should define the interface (e.g., `image_failed: bool` param) before Stream B implements

### Sequential Requirements
1. Stream A & B can run in parallel (different methods)
2. Stream C can run in parallel (separate test file)
3. Stream D must wait for Stream A (needs working retry logic)

## Conflict Risk Assessment

**Low Risk**:
- Streams work on different methods within the same file
- Test file is completely separate
- Reprocessing script is new file

**Coordination Needed**:
- Agree on the interface between `analyze_reddit_post()` and `_build_reddit_prompt()` for passing image failure status

## Parallelization Strategy

**Recommended Approach**: hybrid

```
Time →
├─ Stream A (Core Fix)        ████████░░░░  (2h)
├─ Stream B (Fallback Prompt) ████░░░░░░░░  (1h)
├─ Stream C (Tests)           ██████░░░░░░  (1.5h)
└─ Stream D (Reprocess)       ░░░░░░██████  (1.5h, after A)
```

Launch Streams A, B, C simultaneously. Start Stream D when A completes.

## Expected Timeline

**With parallel execution:**
- Wall time: 3.5 hours (A=2h, then D=1.5h)
- Total work: 6 hours
- Efficiency gain: 42%

**Without parallel execution:**
- Wall time: 6 hours

## Notes

- Stream A is the critical path - fixes must be solid before reprocessing
- Stream B is low-risk and can be reviewed independently
- Stream C tests should cover both success and failure paths
- Stream D should have a dry-run mode to validate before bulk updates
- Consider adding metrics/alerting for future image download failures

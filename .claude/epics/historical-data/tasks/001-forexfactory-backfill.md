---
name: Backfill 3 years of ForexFactory economic events
status: in_progress
priority: high
created: 2025-12-01T17:45:57Z
updated: 2025-12-01T17:45:57Z
github: https://github.com/Dixter999/news-sentiment/issues/11
imported: true
---

# Historical Data: Backfill 3 years of ForexFactory economic events

## Summary

Collect 3 years of historical economic calendar data from ForexFactory (Jan 2022 - Dec 2024) to build a training dataset for PPO/SAC trading models.

## Background

- Current system only collects real-time/weekly data
- PPO/SAC reinforcement learning models need historical data for training
- ForexFactory has historical calendar data accessible week-by-week

## Technical Approach

### Data Source
- ForexFactory Economic Calendar: `https://www.forexfactory.com/calendar?week=<month><day>.<year>`
- ~156 weeks of data (3 years)
- Existing `ForexFactoryScraper` class supports `scrape_week(start_date)` method

### Implementation

1. **Create backfill script** (`scripts/backfill_forex_factory.py`)
   - Iterate week-by-week from Jan 2022 to Dec 2024
   - Use existing `ForexFactoryScraper.scrape_week()`
   - Store in `economic_events` table
   - Checkpoint progress (resume capability)

2. **Rate limiting strategy**
   - 1.5-2 second delay between requests (already in scraper)
   - Add random jitter to avoid detection
   - Implement exponential backoff on failures
   - ~4-6 hours total runtime

3. **Error handling**
   - Cloudflare blocks: pause and retry with longer delay
   - Save progress after each week
   - Skip weeks that already exist in DB

### Database Storage

Uses existing `EconomicEvent` model:
- timestamp, currency, event_name, impact
- actual, forecast, previous values
- sentiment_score (to be analyzed after collection)

## Acceptance Criteria

- [x] Backfill script created with resume capability
- [ ] ~156 weeks of data collected (Jan 2022 - Dec 2024)
- [x] Progress logged and checkpointed
- [x] Handle Cloudflare/rate limiting gracefully
- [ ] Data stored in `economic_events` table

## Estimated Data Volume

| Metric | Estimate |
|--------|----------|
| Weeks | 156 |
| Events/week | ~100-150 |
| Total events | ~15,000-23,000 |
| Runtime | 4-6 hours |

## Risk Mitigation

- IP blocking: Use longer delays, consider proxy rotation
- Cloudflare: playwright-stealth already configured
- Data loss: Checkpoint after each successful week

## Related

- Prepares data for PPO/SAC trading model training
- EUR/USD and other major pairs sentiment analysis

## Progress

- Script: `scripts/backfill_forex_factory.py`
- Checkpoint: `scripts/.backfill_checkpoint.json`
- Resume command: `python scripts/backfill_forex_factory.py --resume`

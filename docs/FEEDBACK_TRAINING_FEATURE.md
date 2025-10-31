# User Feedback & AI Training Feature

## Overview

The Free Tool now includes an **interactive feedback loop** where users can help categorize low-confidence transactions. This feature:

1. **Improves user experience** - Users get better results for unclear transactions
2. **Builds training data** - Every correction trains the AI model
3. **Increases engagement** - Users invest more time, increasing conversion
4. **No interruption** - Completely optional; users can skip and continue

## How It Works

### 1. Detection Phase

After categorization, the system identifies transactions with **confidence < 0.85**:

```typescript
const lowConfidenceTransactions = previewRows
  .filter(row => row.confidence < 0.85);
```

### 2. User Prompt

If low-confidence transactions exist, users see a friendly banner:

```
🤔 Help Improve Our AI! (Optional)

We found 3 transactions where our AI isn't fully confident.
Would you help us categorize them?

⏱️ Takes about 1 minute • Your feedback trains our model for everyone

[Help Categorize (3)]  [Skip & Continue]
```

### 3. Interactive Questions

Users are shown one transaction at a time with:

- **Transaction details**: Date, description, amount
- **AI suggestion**: Current category with confidence score
- **Category options**: Suggested categories as buttons
- **Custom input**: Option to enter a custom category
- **Progress indicator**: "Transaction 2 of 5"

Example:
```
Transaction Details:
Date: 2024-01-15
Amount: $45.99
Description: AMZN MKTP US

Our AI suggests: Shopping (78%)

What category should this be?

[Shopping] [Business Expenses] [Personal] [Entertainment]
[+ Enter custom category]

[Submit Category]  [Skip]
```

### 4. Feedback Collection

User responses are captured in this format:

```typescript
{
  upload_id: "abc123",
  timestamp: "2024-10-30T12:34:56Z",
  ip: "192.168.1.1",
  feedback_count: 3,
  transactions: [
    {
      id: "txn_0",
      date: "2024-01-15",
      description: "AMZN MKTP US",
      amount: -45.99,
      original_category: "Shopping",
      original_confidence: 0.78,
      user_category: "Business Expenses"
    }
  ]
}
```

### 5. Storage

Feedback is stored in two formats:

**Individual files** (for review):
```
data/training/feedback/abc123_1698765432100.json
```

**Consolidated log** (for batch training):
```
data/training/feedback/training_log.jsonl
```

### 6. Summary & Continue

After all feedback is provided, users see:

```
✅ Thank you for your feedback!

You helped categorize 3 transactions.
This data will improve our AI for everyone.

Feedback provided: 3 / 3 transactions
██████████████████████ 100%

[Continue to Download]
```

## Components

### Frontend Components

1. **`CategoryFeedback.tsx`** - Main feedback UI component
   - Shows transaction details
   - Presents category options
   - Captures user selection
   - Displays confidence meter

2. **`FeedbackSummary.tsx`** - Completion summary
   - Shows feedback count
   - Progress bar
   - Thank you message
   - Continue button

3. **`ResultsPreview.tsx`** (updated)
   - Detects low-confidence transactions
   - Shows feedback prompt banner
   - Orchestrates feedback flow
   - Integrates with main flow

### Backend Integration

1. **API Route**: `/api/free/save_feedback/route.ts`
   - Validates feedback data
   - Stores to filesystem
   - Returns success/error

2. **Server Action**: `saveFeedback()` in `actions.ts`
   - Formats training data
   - Calls API endpoint
   - Handles errors gracefully

3. **Page Integration**: `page.tsx`
   - Handles feedback callback
   - Doesn't block user flow
   - Silent failure handling

## Data Format

### Training Data Schema

```json
{
  "upload_id": "string",
  "timestamp": "ISO-8601",
  "ip": "string",
  "user_agent": "string",
  "feedback_count": "number",
  "transactions": [
    {
      "id": "string",
      "date": "YYYY-MM-DD",
      "description": "string (truncated to 100 chars)",
      "amount": "number",
      "original_category": "string",
      "original_confidence": "0.0-1.0",
      "user_category": "string"
    }
  ]
}
```

### JSONL Format (for ML training)

Each line in `training_log.jsonl` is a complete JSON object:

```jsonl
{"upload_id":"abc123","timestamp":"2024-10-30T12:34:56Z","transactions":[...]}
{"upload_id":"def456","timestamp":"2024-10-30T13:45:67Z","transactions":[...]}
```

## Privacy & Safety

### PII Handling

1. **Description truncation**: Limited to 100 characters
2. **No full statements**: Only individual transactions stored
3. **Hashed amounts**: Can optionally round for anonymization
4. **IP logging**: For abuse prevention only

### Data Retention

- Individual feedback files: **90 days** (configurable)
- Training log: **Permanent** (aggregated)
- No email addresses stored with feedback
- Upload IDs are temporary (24h TTL)

### Opt-Out

Users can:
- Skip individual questions
- Skip all feedback ("Skip & Continue")
- Still get full CSV export

## Using Training Data

### Batch Training Script (To Be Implemented)

```python
# scripts/train_from_feedback.py

import json
import sys

def load_feedback(log_file):
    """Load all feedback from JSONL log"""
    with open(log_file) as f:
        return [json.loads(line) for line in f]

def prepare_training_data(feedback_entries):
    """Convert feedback to ML training format"""
    training_samples = []
    
    for entry in feedback_entries:
        for txn in entry['transactions']:
            training_samples.append({
                'description': txn['description'],
                'amount': txn['amount'],
                'label': txn['user_category'],
                'weight': 1.0 / (txn['original_confidence'] + 0.1)  # Higher weight for low confidence
            })
    
    return training_samples

def retrain_model(training_samples):
    """Retrain categorization model with new samples"""
    # Implementation depends on your ML framework
    pass

if __name__ == '__main__':
    feedback = load_feedback('data/training/feedback/training_log.jsonl')
    samples = prepare_training_data(feedback)
    print(f"Loaded {len(samples)} training samples")
    retrain_model(samples)
```

### Continuous Learning Pipeline

1. **Nightly aggregation**: Collect previous day's feedback
2. **Quality filtering**: Remove duplicates, check for abuse
3. **Model retraining**: Incorporate new samples
4. **A/B testing**: Compare new model vs. current
5. **Gradual rollout**: Deploy if metrics improve

## Metrics & KPIs

### Track These Metrics

1. **Engagement**
   - % of users who see feedback prompt
   - % who click "Help Categorize"
   - Average feedback provided per session
   - Completion rate (finish all vs. skip)

2. **Data Quality**
   - Total feedback entries per day/week
   - Unique categories discovered
   - Agreement with AI (validation)
   - Patterns in corrections

3. **Model Improvement**
   - Confidence score trends (before/after training)
   - Accuracy on test set
   - Reduction in low-confidence transactions

### Dashboard Queries

```sql
-- Feedback volume
SELECT DATE(timestamp) as date, 
       COUNT(*) as sessions,
       SUM(feedback_count) as total_corrections
FROM feedback_log
GROUP BY DATE(timestamp)
ORDER BY date DESC;

-- Most corrected categories
SELECT original_category, 
       user_category, 
       COUNT(*) as corrections
FROM feedback_transactions
WHERE original_category != user_category
GROUP BY original_category, user_category
ORDER BY corrections DESC
LIMIT 20;

-- Category discovery
SELECT user_category, COUNT(*) as usage
FROM feedback_transactions
WHERE user_category NOT IN (SELECT name FROM default_categories)
GROUP BY user_category
ORDER BY usage DESC;
```

## Configuration

### Enable/Disable Feature

In `configs/free_tool.yaml`:

```yaml
feedback:
  enabled: true
  confidence_threshold: 0.85  # Show feedback for transactions below this
  max_questions: 10           # Limit questions per session
  skip_allowed: true          # Allow users to skip
```

### Environment Variables

```bash
# Storage location
FEEDBACK_STORAGE_DIR=data/training/feedback

# Retention
FEEDBACK_RETENTION_DAYS=90

# Rate limiting (prevent abuse)
FEEDBACK_MAX_PER_IP_PER_DAY=5
```

## Deployment Checklist

- [x] Frontend components created
- [x] API route implemented
- [x] Server actions added
- [x] Page integration complete
- [x] Storage directories configured
- [x] `.gitignore` updated
- [ ] Monitoring alerts set up
- [ ] Weekly review process established
- [ ] Training pipeline implemented
- [ ] A/B test framework ready

## Future Enhancements

### Phase 2
- **Category suggestions API**: Suggest based on description analysis
- **Bulk feedback**: Allow users to review multiple at once
- **Confidence calibration**: Use feedback to improve confidence scores

### Phase 3
- **Gamification**: "You've helped train 100 transactions! 🎉"
- **Leaderboard**: Show community impact
- **Category voting**: Multiple users vote on same transaction

### Phase 4
- **Active learning**: Intelligently select which transactions to ask about
- **Transfer learning**: Use feedback from one industry to improve another
- **Federated learning**: Train on aggregated feedback without raw data

## Support & Troubleshooting

### Common Issues

**Issue**: Feedback not saving
- Check filesystem permissions on `data/training/feedback/`
- Verify API route returns 200
- Check browser console for errors

**Issue**: Too many questions
- Adjust `confidence_threshold` higher (e.g., 0.90)
- Reduce `max_questions` limit

**Issue**: Poor category suggestions
- Expand `suggested_categories` in component
- Add industry-specific categories
- Use description analysis for dynamic suggestions

### Debug Mode

Enable verbose logging:

```typescript
// In CategoryFeedback.tsx
const DEBUG = process.env.NEXT_PUBLIC_DEBUG === 'true';

if (DEBUG) {
  console.log('[FEEDBACK] Transaction:', transaction);
  console.log('[FEEDBACK] Selected category:', selectedCategory);
}
```

## License & Attribution

This feedback system is part of AI-Bookkeeper's Free Tool.
All feedback data is owned by AI-Bookkeeper and used solely to improve the service.

Users are informed via UI:
> "Your feedback trains our model for everyone"

---

**Last Updated**: 2024-10-30  
**Feature Version**: 1.0  
**Status**: ✅ Production Ready


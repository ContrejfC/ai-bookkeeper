# Training Feedback Data

This directory stores user feedback from the Free Tool for AI model training.

## Contents

- **Individual files**: `{upload_id}_{timestamp}.json` - One file per feedback session
- **Training log**: `training_log.jsonl` - Consolidated log in JSONL format (one JSON object per line)

## Privacy & Security

⚠️ **This directory contains user data and is excluded from git.**

- All files here are `.gitignored` to protect user privacy
- Data is automatically cleaned after **90 days** (configurable)
- Only aggregated statistics should be shared publicly

## Data Format

Each feedback entry contains:
- Upload ID (temporary, expires in 24h)
- Timestamp
- IP address (for abuse prevention only)
- Transaction corrections (description truncated to 100 chars)

## Usage

### View Recent Feedback

```bash
# Show last 10 feedback sessions
tail -10 training_log.jsonl | jq

# Count total corrections
wc -l training_log.jsonl
```

### Extract Training Data

```bash
# Get all user corrections
jq -r '.transactions[] | "\(.description)\t\(.user_category)"' training_log.jsonl
```

### Statistics

```bash
# Total feedback sessions
wc -l training_log.jsonl

# Total corrections
jq '[.feedback_count] | add' training_log.jsonl | paste -sd+ | bc
```

## Retention Policy

- **Individual files**: Deleted after 90 days
- **Training log**: Kept indefinitely (aggregated data)
- **PII**: Never stored (descriptions truncated, no emails)

## Training Pipeline

To retrain the model with feedback data:

```bash
python scripts/train_from_feedback.py data/training/feedback/training_log.jsonl
```

(Training script to be implemented)

## Monitoring

Check feedback volume:

```bash
# Today's feedback
find . -name "*.json" -mtime 0 | wc -l

# This week's feedback
find . -name "*.json" -mtime -7 | wc -l
```

## Support

For questions about this data:
- **Privacy concerns**: See `docs/FEEDBACK_TRAINING_FEATURE.md`
- **Technical issues**: Check logs in `ops/launch_checks/`
- **Data access**: Contact data team

---

**Last Updated**: 2024-10-30


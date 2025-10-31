/**
 * Save Feedback API Route
 * 
 * Stores user feedback for low-confidence categorizations.
 * This data is used to train and improve the AI model.
 */

import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';
import fs from 'fs/promises';
import path from 'path';

// Request schema
const FeedbackSchema = z.object({
  upload_id: z.string().min(1),
  feedback: z.record(z.string(), z.string()), // transactionId -> selectedCategory
  transactions: z.array(z.object({
    id: z.string(),
    date: z.string(),
    description: z.string(),
    amount: z.number(),
    original_category: z.string(),
    original_confidence: z.number(),
    user_category: z.string()
  }))
});

type FeedbackData = z.infer<typeof FeedbackSchema>;

export async function POST(request: NextRequest) {
  try {
    // Parse and validate request body
    const body = await request.json();
    const validated = FeedbackSchema.parse(body);

    // Create feedback entry with metadata
    const feedbackEntry = {
      upload_id: validated.upload_id,
      timestamp: new Date().toISOString(),
      ip: request.headers.get('x-forwarded-for') || request.headers.get('x-real-ip') || 'unknown',
      user_agent: request.headers.get('user-agent') || 'unknown',
      feedback_count: validated.transactions.length,
      transactions: validated.transactions
    };

    // Store feedback to training data file
    const feedbackDir = path.join(process.cwd(), 'data', 'training', 'feedback');
    await fs.mkdir(feedbackDir, { recursive: true });

    const feedbackFile = path.join(feedbackDir, `${validated.upload_id}_${Date.now()}.json`);
    await fs.writeFile(feedbackFile, JSON.stringify(feedbackEntry, null, 2), 'utf8');

    // Also append to consolidated training log
    const trainingLogFile = path.join(feedbackDir, 'training_log.jsonl');
    const logEntry = JSON.stringify(feedbackEntry) + '\n';
    await fs.appendFile(trainingLogFile, logEntry, 'utf8');

    // Track telemetry (optional - integrate with your telemetry system)
    console.log(`[FEEDBACK] Saved ${validated.transactions.length} feedback entries for upload ${validated.upload_id}`);

    return NextResponse.json({
      success: true,
      message: `Saved ${validated.transactions.length} feedback entries`,
      feedback_id: `${validated.upload_id}_${Date.now()}`
    });

  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json(
        {
          success: false,
          error: 'INVALID_INPUT',
          hint: 'Invalid feedback data format',
          details: error.errors
        },
        { status: 400 }
      );
    }

    console.error('[FEEDBACK] Error saving feedback:', error);
    return NextResponse.json(
      {
        success: false,
        error: 'STORAGE_ERROR',
        hint: 'Failed to save feedback data'
      },
      { status: 500 }
    );
  }
}

/**
 * GET endpoint to retrieve feedback statistics (optional - for admin dashboard)
 */
export async function GET(request: NextRequest) {
  try {
    const feedbackDir = path.join(process.cwd(), 'data', 'training', 'feedback');
    
    // Read training log
    const trainingLogFile = path.join(feedbackDir, 'training_log.jsonl');
    
    try {
      const logContent = await fs.readFile(trainingLogFile, 'utf8');
      const entries = logContent.trim().split('\n').filter(Boolean).map(line => JSON.parse(line));
      
      // Calculate statistics
      const stats = {
        total_feedback_sessions: entries.length,
        total_transactions_corrected: entries.reduce((sum, e) => sum + e.feedback_count, 0),
        date_range: {
          earliest: entries.length > 0 ? entries[0].timestamp : null,
          latest: entries.length > 0 ? entries[entries.length - 1].timestamp : null
        }
      };

      return NextResponse.json({
        success: true,
        stats
      });
    } catch (err) {
      // No training data yet
      return NextResponse.json({
        success: true,
        stats: {
          total_feedback_sessions: 0,
          total_transactions_corrected: 0,
          date_range: { earliest: null, latest: null }
        }
      });
    }

  } catch (error) {
    console.error('[FEEDBACK] Error reading stats:', error);
    return NextResponse.json(
      {
        success: false,
        error: 'READ_ERROR',
        hint: 'Failed to read feedback statistics'
      },
      { status: 500 }
    );
  }
}


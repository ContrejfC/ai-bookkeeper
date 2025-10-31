/**
 * Free Tool Propose API Route
 * 
 * Calls backend to categorize transactions and returns preview data.
 */

import { NextRequest, NextResponse } from 'next/server';
import { readFile } from 'fs/promises';
import { join } from 'path';
import { proposeSchema } from '@/lib/validators';

export async function POST(request: NextRequest) {
  try {
    // Parse request body
    const body = await request.json();
    
    // Validate input
    const validated = proposeSchema.parse(body);
    const { upload_id } = validated;
    
    // Read file metadata
    const tempDir = process.env.TEMP_STORAGE_PATH || '/tmp/free_uploads';
    const uploadDir = join(tempDir, upload_id);
    const metadataPath = join(uploadDir, 'metadata.json');
    
    const metadata = JSON.parse(await readFile(metadataPath, 'utf-8'));
    const filePath = join(uploadDir, metadata.filename);
    
    // Call backend API
    const apiBase = process.env.BACKEND_API_BASE || 'http://localhost:8000';
    const apiKey = process.env.BACKEND_API_KEY;
    
    const formData = new FormData();
    const fileBuffer = await readFile(filePath);
    const blob = new Blob([fileBuffer], { type: metadata.mime_type });
    formData.append('file', blob, metadata.filename);
    
    const response = await fetch(`${apiBase}/api/ingestion/upload`, {
      method: 'POST',
      headers: {
        'X-Free-Mode': 'true',
        'X-Rate-Limited': 'true',
        ...(apiKey && { 'Authorization': `Bearer ${apiKey}` })
      },
      body: formData
    });
    
    if (!response.ok) {
      const error = await response.json();
      return NextResponse.json(
        { error: error.message || 'Categorization failed', code: 'PROPOSE_FAILED' },
        { status: response.status }
      );
    }
    
    const result = await response.json();
    
    // Cap rows at 500
    const totalRows = result.transactions?.length || 0;
    const cappedTransactions = (result.transactions || []).slice(0, 500);
    
    // Get preview (first 25 rows)
    const previewRows = cappedTransactions.slice(0, 25).map((txn: any) => ({
      date: txn.date || txn.post_date,
      description: (txn.description || '').slice(0, 80), // Truncate for privacy
      amount: parseFloat(txn.amount || 0),
      category: txn.category || 'Uncategorized',
      confidence: parseFloat(txn.confidence || 0),
      notes: txn.notes || ''
    }));
    
    // Calculate metrics
    const categories = new Set(cappedTransactions.map((t: any) => t.category || 'Uncategorized'));
    const confidences = cappedTransactions.map((t: any) => parseFloat(t.confidence || 0));
    const avgConfidence = confidences.reduce((a, b) => a + b, 0) / confidences.length;
    
    return NextResponse.json({
      upload_id,
      preview_rows: previewRows,
      total_rows: totalRows,
      exportable_rows: Math.min(totalRows, 500),
      categories_count: categories.size,
      confidence_avg: avgConfidence,
      metrics: {
        parse_ms: result.parse_time_ms || 0,
        rows_parsed: totalRows,
        capped: totalRows > 500
      }
    });
    
  } catch (error) {
    console.error('Propose error:', error);
    
    return NextResponse.json(
      {
        error: 'Failed to categorize transactions',
        code: 'PROPOSE_ERROR',
        message: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    );
  }
}


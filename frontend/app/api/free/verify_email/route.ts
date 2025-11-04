/**
 * Free Tool Email Verification API Route
 * 
 * Handles email verification code sending and verification.
 */

import { NextRequest, NextResponse } from 'next/server';
import { cookies } from 'next/headers';
import { checkEmailRateLimit } from '@/lib/rateLimit';
import { verifyEmailSendSchema, verifyEmailConfirmSchema } from '@/lib/validators';

/**
 * POST /api/free/verify_email
 * 
 * Body can be either:
 * 1. { email, captcha_token, action: 'send' } - Send verification code
 * 2. { email, code, action: 'verify' } - Verify code
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const action = body.action || 'send';
    
    if (action === 'send') {
      return handleSendCode(body);
    } else if (action === 'verify') {
      return handleVerifyCode(body);
    } else {
      return NextResponse.json(
        { error: 'Invalid action', code: 'INVALID_ACTION' },
        { status: 400 }
      );
    }
    
  } catch (error) {
    console.error('Email verification error:', error);
    
    return NextResponse.json(
      {
        error: 'Verification failed',
        code: 'VERIFY_ERROR',
        message: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    );
  }
}

/**
 * Send verification code
 */
async function handleSendCode(body: any) {
  // Validate input
  const validated = verifyEmailSendSchema.parse(body);
  const { email, captcha_token } = validated;
  
  // Check email rate limit
  const rateLimitResult = await checkEmailRateLimit(email);
  
  if (!rateLimitResult.allowed) {
    return NextResponse.json(
      {
        error: 'Email rate limit exceeded (3 per day)',
        code: 'EMAIL_RATE_LIMIT',
        retry_after: Math.ceil((rateLimitResult.resetAt.getTime() - Date.now()) / 1000)
      },
      { status: 429 }
    );
  }
  
  // Generate 6-digit code
  const code = Math.floor(100000 + Math.random() * 900000).toString();
  
  // Store code in cookie (expires in 15 minutes)
  const cookieStore = await cookies();
  
  cookieStore.set('verification_code', code, {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    maxAge: 15 * 60,
    sameSite: 'lax'
  });
  
  cookieStore.set('verification_email', email, {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    maxAge: 15 * 60,
    sameSite: 'lax'
  });
  
  cookieStore.set('verification_sent_at', Date.now().toString(), {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    maxAge: 15 * 60,
    sameSite: 'lax'
  });
  
  // Send email
  await sendEmailCode(email, code);
  
  return NextResponse.json({
    success: true,
    message: 'Verification code sent to your email'
  });
}

/**
 * Verify code
 */
async function handleVerifyCode(body: any) {
  // Validate input
  const validated = verifyEmailConfirmSchema.parse(body);
  const { email, code } = validated;
  
  // Get stored values from cookies
  const cookieStore = await cookies();
  const storedCode = cookieStore.get('verification_code')?.value;
  const storedEmail = cookieStore.get('verification_email')?.value;
  const sentAt = cookieStore.get('verification_sent_at')?.value;
  
  if (!storedCode || !storedEmail || !sentAt) {
    return NextResponse.json(
      { error: 'Verification code expired or not found', code: 'CODE_EXPIRED' },
      { status: 400 }
    );
  }
  
  // Check if code expired (15 minutes)
  const sentTime = parseInt(sentAt);
  if (Date.now() - sentTime > 15 * 60 * 1000) {
    return NextResponse.json(
      { error: 'Verification code expired', code: 'CODE_EXPIRED' },
      { status: 400 }
    );
  }
  
  // Verify email and code match
  if (storedEmail !== email || storedCode !== code) {
    return NextResponse.json(
      { error: 'Invalid verification code', code: 'CODE_INVALID' },
      { status: 400 }
    );
  }
  
  // Generate JWT token (simplified - use proper JWT library in production)
  const token = Buffer.from(JSON.stringify({
    email,
    verified_at: Date.now(),
    expires_at: Date.now() + (24 * 60 * 60 * 1000)
  })).toString('base64');
  
  // Store token in cookie
  cookieStore.set('email_token', token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    maxAge: 24 * 60 * 60,
    sameSite: 'lax'
  });
  
  // Store consent timestamp
  cookieStore.set('email_consent_at', Date.now().toString(), {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    maxAge: 365 * 24 * 60 * 60, // 1 year
    sameSite: 'lax'
  });
  
  // Clear verification cookies
  cookieStore.delete('verification_code');
  cookieStore.delete('verification_email');
  cookieStore.delete('verification_sent_at');
  
  return NextResponse.json({
    success: true,
    message: 'Email verified successfully',
    token
  });
}

/**
 * Send email code via provider
 */
async function sendEmailCode(email: string, code: string): Promise<void> {
  const provider = process.env.EMAIL_PROVIDER || 'sendgrid';
  const apiKey = process.env.EMAIL_PROVIDER_API_KEY;
  const from = process.env.EMAIL_FROM || 'no-reply@aibookkeeper.com';
  
  if (!apiKey) {
    console.warn('EMAIL_PROVIDER_API_KEY not set');
    console.log(`[DEV] Verification code for ${email}: ${code}`);
    return;
  }
  
  const emailHtml = `
    <!DOCTYPE html>
    <html>
    <head>
      <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { text-align: center; margin-bottom: 30px; }
        .code { font-size: 36px; letter-spacing: 8px; font-family: monospace; text-align: center; background: #f0f0f0; padding: 20px; border-radius: 8px; margin: 20px 0; }
        .footer { text-align: center; font-size: 12px; color: #666; margin-top: 30px; }
      </style>
    </head>
    <body>
      <div class="container">
        <div class="header">
          <h1>Your Verification Code</h1>
        </div>
        <p>Enter this code to download your categorized CSV:</p>
        <div class="code">${code}</div>
        <p>This code expires in <strong>15 minutes</strong>.</p>
        <p>If you didn't request this code, you can safely ignore this email.</p>
        <div class="footer">
          <p>© ${new Date().getFullYear()} AI-Bookkeeper. All rights reserved.</p>
        </div>
      </div>
    </body>
    </html>
  `;
  
  if (provider === 'sendgrid') {
    await sendViaSendGrid(email, code, apiKey, from, emailHtml);
  } else if (provider === 'mailgun') {
    await sendViaMailgun(email, code, apiKey, from, emailHtml);
  }
}

async function sendViaSendGrid(to: string, code: string, apiKey: string, from: string, html: string) {
  await fetch('https://api.sendgrid.com/v3/mail/send', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${apiKey}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      personalizations: [{ to: [{ email: to }] }],
      from: { email: from },
      subject: `Your AI-Bookkeeper Verification Code: ${code}`,
      content: [{ type: 'text/html', value: html }]
    })
  });
}

async function sendViaMailgun(to: string, code: string, apiKey: string, from: string, html: string) {
  const domain = process.env.MAILGUN_DOMAIN || 'mg.aibookkeeper.com';
  
  const formData = new FormData();
  formData.append('from', from);
  formData.append('to', to);
  formData.append('subject', `Your AI-Bookkeeper Verification Code: ${code}`);
  formData.append('html', html);
  
  await fetch(`https://api.mailgun.net/v3/${domain}/messages`, {
    method: 'POST',
    headers: {
      'Authorization': `Basic ${Buffer.from(`api:${apiKey}`).toString('base64')}`
    },
    body: formData
  });
}




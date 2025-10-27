# Background Jobs System - Complete Guide

## 📋 Overview

The AI Bookkeeper now has a **complete background jobs system** for handling long-running operations with real-time progress tracking.

**Features:**
- ✅ Queue-based job processing (Redis or in-memory)
- ✅ Real-time progress updates
- ✅ Automatic polling with exponential backoff
- ✅ Error handling and retry logic
- ✅ React hooks and UI components
- ✅ Full TypeScript support

---

## 🏗️ Architecture

```
┌─────────────┐         ┌──────────────┐         ┌──────────────┐
│   Frontend  │  POST   │   Backend    │ Enqueue │ Job Queue    │
│  (Next.js)  ├────────>│  /api/jobs   ├────────>│ (Redis/Mem) │
└──────┬──────┘         └──────────────┘         └──────┬───────┘
       │                                                  │
       │ Poll GET /api/jobs/{id}                        │
       │<───────────────────────────────────────────────┤
       │                                                 │
       │                                          ┌──────▼───────┐
       │                                          │ Worker Tasks │
       │                                          │  - AI Cat.   │
       │                                          │  - OCR       │
       │                                          │  - Exports   │
       │                                          └──────────────┘
```

---

## 🚀 Quick Start

### 1. Start a Background Job

```typescript
// Frontend: pages/transactions/upload.tsx
import { useState } from 'react';
import { JobProgress } from '@/components/JobProgress';

function UploadPage() {
  const [jobId, setJobId] = useState<string | null>(null);

  const handleUpload = async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('company_id', 'my-company');
    formData.append('tenant_id', 'my-tenant');

    const response = await fetch('/api/jobs/upload-and-categorize', {
      method: 'POST',
      body: formData
    });

    const data = await response.json();
    setJobId(data.job_id);  // Save job ID for polling
  };

  return (
    <div>
      <input type="file" onChange={(e) => handleUpload(e.target.files[0])} />
      
      {jobId && (
        <JobProgress
          jobId={jobId}
          title="Processing Transactions"
          onComplete={(result) => {
            console.log('Done!', result);
            // Refresh your data
          }}
        />
      )}
    </div>
  );
}
```

### 2. Use the Hook Directly

```typescript
import { useJobStatus } from '@/hooks/useJobStatus';

function MyComponent({ jobId }: { jobId: string }) {
  const { status, progress, message, result, error, isLoading } = 
    useJobStatus(jobId, {
      onComplete: (result) => console.log('Done!', result),
      onError: (error) => console.error('Failed:', error)
    });

  if (isLoading) {
    return <Progress value={progress} label={message} />;
  }

  if (error) {
    return <Alert color="danger">{error}</Alert>;
  }

  return <Alert color="success">Complete!</Alert>;
}
```

---

## 📡 API Endpoints

### Start Jobs

#### 1. **Categorize Transactions**
```bash
POST /api/jobs/categorize
{
  "company_id": "string",
  "tenant_id": "string",
  "transaction_ids": ["txn1", "txn2"],  # optional
  "limit": 100
}
```

#### 2. **Process Receipt OCR**
```bash
POST /api/jobs/ocr
{
  "company_id": "string",
  "receipt_id": "string",
  "file_path": "/path/to/receipt.jpg"
}
```

#### 3. **Export to QuickBooks**
```bash
POST /api/jobs/export-qbo
{
  "company_id": "string",
  "tenant_id": "string",
  "start_date": "2025-01-01",
  "end_date": "2025-12-31"
}
```

#### 4. **Bulk Approve**
```bash
POST /api/jobs/bulk-approve
{
  "company_id": "string",
  "tenant_id": "string",
  "transaction_ids": ["txn1", "txn2", "txn3"]
}
```

#### 5. **Upload & Categorize**
```bash
POST /api/jobs/upload-and-categorize
Content-Type: multipart/form-data

file: <file>
company_id: "string"
tenant_id: "string"
```

### Monitor Jobs

#### **Get Job Status**
```bash
GET /api/jobs/{job_id}

Response:
{
  "id": "job_abc123",
  "status": "running",       # pending/running/complete/failed
  "progress": 45,            # 0-100
  "message": "Processing transaction 45/100...",
  "result": null,            # Available when complete
  "error": null,             # Available when failed
  "created_at": "2025-10-27T10:00:00Z",
  "started_at": "2025-10-27T10:00:01Z",
  "finished_at": null
}
```

#### **Get Company Jobs**
```bash
GET /api/jobs/company/{company_id}?limit=50

Response:
{
  "company_id": "demo-company",
  "jobs": [
    { "id": "job_1", "status": "complete", ... },
    { "id": "job_2", "status": "running", ... }
  ],
  "count": 2
}
```

---

## 🎨 Frontend Components

### `<JobProgress>` - Full Progress Card

```tsx
import { JobProgress } from '@/components/JobProgress';

<JobProgress
  jobId={jobId}
  title="Processing Transactions"
  showDetails={true}
  onComplete={(result) => console.log(result)}
  onError={(error) => console.error(error)}
/>
```

### `<JobProgressCompact>` - Inline Progress

```tsx
import { JobProgressCompact } from '@/components/JobProgress';

<JobProgressCompact
  jobId={jobId}
  onComplete={() => refetchData()}
/>
```

### `<JobProgressModal>` - Full-Screen Modal

```tsx
import { JobProgressModal } from '@/components/JobProgress';

<JobProgressModal
  jobId={jobId}
  title="Exporting to QuickBooks"
  onClose={() => setModalOpen(false)}
/>
```

---

## 🔧 Backend Implementation

### Create a New Background Task

```python
# app/worker/background_tasks.py

def my_custom_task(
    company_id: str,
    param1: str,
    param2: int
) -> Dict[str, Any]:
    """My custom background task."""
    job_id = None
    try:
        if QUEUE_TYPE == "redis":
            from rq import get_current_job
            job = get_current_job()
            job_id = job.id if job else None
    except:
        pass
    
    # Update progress
    if job_id:
        update_job_progress(job_id, 25, "Step 1 of 4...")
    
    # Do work
    result = {"status": "success"}
    
    if job_id:
        update_job_progress(job_id, 100, "Complete!")
    
    return result
```

### Add API Endpoint

```python
# app/api/background_jobs.py

@router.post("/my-job")
async def start_my_job(
    company_id: str,
    param1: str,
    current_user = Depends(get_current_user)
):
    from app.worker.background_tasks import my_custom_task
    
    job_id = enqueue_job(
        my_custom_task,
        kwargs={"company_id": company_id, "param1": param1, "param2": 42},
        meta={"company_id": company_id, "operation": "my_job"}
    )
    
    return {"job_id": job_id, "status": "pending"}
```

---

## 🛠️ Configuration

### Environment Variables

```bash
# .env

# Redis URL (optional - falls back to in-memory queue)
REDIS_URL=redis://localhost:6379/0

# Worker settings
WORKER_THREADS=4
JOB_TIMEOUT=600
JOB_TTL=3600
```

### Start Worker (Redis mode only)

```bash
# Start RQ worker
rq worker high default low --url redis://localhost:6379/0

# Or use multiple workers
rq worker high default low --url redis://localhost:6379/0 &
rq worker high default low --url redis://localhost:6379/0 &
```

### In-Memory Mode (No Redis)

The system automatically falls back to an in-memory queue if Redis is not available:

- ✅ No external dependencies
- ✅ Thread-based execution
- ✅ Works out of the box
- ⚠️ Jobs lost on restart
- ⚠️ Single-server only

---

## 📊 Monitoring & Debugging

### View All Jobs for a Company

```typescript
const response = await fetch('/api/jobs/company/my-company?limit=50');
const { jobs } = await response.json();

jobs.forEach(job => {
  console.log(`${job.id}: ${job.status} (${job.progress}%)`);
});
```

### Debug a Specific Job

```typescript
const response = await fetch('/api/jobs/job_abc123');
const job = await response.json();

console.log('Status:', job.status);
console.log('Progress:', job.progress);
console.log('Message:', job.message);
console.log('Error:', job.error);
```

### Job Cleanup

Old jobs are automatically cleaned up after 24 hours (configurable):

```python
# app/worker/simple_queue.py
cleanup_old_jobs(max_age_hours=24)
```

---

## 🎯 Use Cases

### 1. Transaction Upload & Categorization

```typescript
const formData = new FormData();
formData.append('file', csvFile);
formData.append('company_id', companyId);
formData.append('tenant_id', tenantId);

const { job_id } = await (await fetch('/api/jobs/upload-and-categorize', {
  method: 'POST',
  body: formData
})).json();

// Show progress
<JobProgress jobId={job_id} onComplete={() => refetchTransactions()} />
```

### 2. Bulk Operations

```typescript
const { job_id } = await (await fetch('/api/jobs/bulk-approve', {
  method: 'POST',
  body: JSON.stringify({
    company_id: 'demo',
    tenant_id: 'demo',
    transaction_ids: selectedIds
  })
})).json();

// Track progress
<JobProgressModal jobId={job_id} title="Approving Transactions" />
```

### 3. Export to Accounting System

```typescript
const { job_id } = await (await fetch('/api/jobs/export-qbo', {
  method: 'POST',
  body: JSON.stringify({
    company_id: 'demo',
    tenant_id: 'demo',
    start_date: '2025-01-01',
    end_date: '2025-12-31'
  })
})).json();

// Show progress
<JobProgress jobId={job_id} onComplete={() => showSuccessToast()} />
```

---

## 🧪 Testing

### Test Backend Jobs

```bash
# Run tests
pytest tests/test_background_jobs.py -v

# Test specific job
pytest tests/test_background_jobs.py::test_categorize_job -v
```

### Test Frontend Components

```bash
cd frontend
npm run test -- JobProgress
```

### Manual Testing

1. Visit `/dashboard/background-jobs` in the app
2. Click buttons to start jobs
3. Watch real-time progress updates
4. Check console for logs

---

## 🚦 Production Deployment

### With Redis (Recommended)

1. **Add Redis to your infrastructure**
   ```bash
   # Docker Compose
   redis:
     image: redis:7-alpine
     ports:
       - "6379:6379"
   ```

2. **Set environment variable**
   ```bash
   REDIS_URL=redis://redis:6379/0
   ```

3. **Start workers**
   ```bash
   rq worker high default low
   ```

### Without Redis (Simple mode)

- No additional setup required
- Jobs run in background threads
- Suitable for small deployments

---

## 📝 Summary

You now have a complete background jobs system with:

- ✅ **Backend**: Job queue + worker tasks
- ✅ **Frontend**: Polling hooks + UI components
- ✅ **API**: RESTful endpoints for all operations
- ✅ **Examples**: Demo page showing usage
- ✅ **Documentation**: This guide

**Next Steps:**
1. Try the demo: `/dashboard/background-jobs`
2. Integrate into your pages
3. Add custom tasks as needed
4. Deploy with Redis for production

**Questions?** Check the code comments or API docs at `/docs`


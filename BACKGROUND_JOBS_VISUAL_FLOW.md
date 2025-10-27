# Background Jobs System - Visual Flow

## 🔄 Complete Request/Response Flow

```
┌──────────────────────────────────────────────────────────────────────┐
│                          USER ACTION                                 │
│                     (Click "Categorize")                             │
└─────────────────────────────┬────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│  STEP 1: START JOB                                                   │
│  ─────────────────────────────────────────────────────────────────  │
│                                                                       │
│  Frontend:                                                           │
│    const response = await fetch('/api/jobs/categorize', {           │
│      method: 'POST',                                                 │
│      body: JSON.stringify({ company_id, tenant_id, limit: 100 })    │
│    });                                                                │
│    const { job_id } = await response.json();                         │
│                                                                       │
│  Backend:                                                            │
│    1. Receives request at /api/jobs/categorize                       │
│    2. Calls enqueue_job(categorize_transactions_task, ...)           │
│    3. Creates job record: { id, status: "pending", progress: 0 }     │
│    4. Submits to ThreadPoolExecutor                                  │
│    5. Returns immediately: { job_id: "job_abc123" }                  │
│                                                                       │
│  Response Time: ~100ms                                               │
└─────────────────────────────┬────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│  STEP 2: POLL FOR STATUS (Automatic)                                │
│  ─────────────────────────────────────────────────────────────────  │
│                                                                       │
│  Frontend (useJobStatus hook):                                       │
│    Every 1 second (initially):                                       │
│      GET /api/jobs/job_abc123                                        │
│                                                                       │
│  Backend:                                                            │
│    Returns current state:                                            │
│    {                                                                  │
│      id: "job_abc123",                                               │
│      status: "running",        ← Changes over time                   │
│      progress: 45,             ← 0 → 25 → 50 → 75 → 100             │
│      message: "Processing transaction 45/100...",                    │
│      result: null              ← Populated when complete             │
│    }                                                                  │
│                                                                       │
│  Polling Strategy:                                                   │
│    - Start: 1 second interval                                        │
│    - After 5 polls: 1.5 seconds                                      │
│    - After 10 polls: 2.25 seconds                                    │
│    - Max: 5 seconds                                                  │
│    - Stops when: status = "complete" or "failed"                     │
└─────────────────────────────┬────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│  STEP 3: JOB EXECUTION (Background Thread)                           │
│  ─────────────────────────────────────────────────────────────────  │
│                                                                       │
│  Worker Thread:                                                      │
│    1. Status → "running"                                             │
│    2. Progress → 10%, message: "Fetching transactions..."            │
│    3. Query database for uncategorized transactions                  │
│    4. Progress → 20%, message: "Categorizing transaction 1/100..."   │
│    5. For each transaction:                                          │
│         - Apply rules engine                                         │
│         - Call LLM if needed                                         │
│         - Create journal entry                                       │
│         - Update progress: 20 + (idx/total * 70)                     │
│    6. Progress → 95%, message: "Committing to database..."           │
│    7. db.commit()                                                    │
│    8. Progress → 100%, status → "complete"                           │
│    9. Store result: { journal_entries_created: 95, ... }             │
│                                                                       │
│  Timeline: 10-60 seconds (depends on data volume)                    │
└─────────────────────────────┬────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│  STEP 4: COMPLETION                                                  │
│  ─────────────────────────────────────────────────────────────────  │
│                                                                       │
│  Frontend (useJobStatus):                                            │
│    - Detects status = "complete"                                     │
│    - Stops polling                                                   │
│    - Calls onComplete(result) callback                               │
│    - Shows success UI                                                │
│                                                                       │
│  User sees:                                                          │
│    ✅ Job completed successfully!                                    │
│    📊 95 journal entries created                                     │
│    [View Results] button                                             │
│                                                                       │
│  Cleanup:                                                            │
│    - Job record kept for 24 hours                                    │
│    - Then auto-deleted by cleanup worker                             │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 🎬 Timeline View

```
Time →

0s     [User clicks "Categorize"]
       ↓
0.1s   [Backend creates job → job_abc123]
       ↓
0.1s   [Frontend receives job_id]
       ↓
1.0s   [Poll #1] status: pending, progress: 0
       ↓
2.0s   [Poll #2] status: running, progress: 10, "Fetching..."
       ↓
3.0s   [Poll #3] status: running, progress: 25, "Categorizing 1/100"
       ↓
4.5s   [Poll #4] status: running, progress: 35, "Categorizing 15/100"
       ↓
6.5s   [Poll #5] status: running, progress: 50, "Categorizing 30/100"
       ↓
9.0s   [Poll #6] status: running, progress: 65, "Categorizing 45/100"
       ↓
12.0s  [Poll #7] status: running, progress: 80, "Categorizing 60/100"
       ↓
15.0s  [Poll #8] status: running, progress: 95, "Committing..."
       ↓
16.0s  [Poll #9] status: complete, progress: 100, result: {...}
       ↓
16.0s  [Frontend stops polling, calls onComplete()]
       ↓
16.0s  [Show success message to user]
```

---

## 🧩 Component Interaction

```
┌─────────────────────────────────────────────────────────────┐
│                      REACT COMPONENT                        │
│                                                             │
│  function TransactionsPage() {                             │
│    const [jobId, setJobId] = useState(null);               │
│                                                             │
│    return (                                                 │
│      <>                                                     │
│        <Button onClick={() => startJob()}>                 │
│          Categorize                                         │
│        </Button>                                            │
│                                                             │
│        {jobId && (                                          │
│          <JobProgress                    ┐                 │
│            jobId={jobId}                 │                 │
│            onComplete={(result) => {     │ Encapsulates   │
│              refetchData();              │ all polling     │
│              showSuccess(result);        │ logic           │
│            }}                            │                 │
│          />                              ┘                 │
│        )}                                                   │
│      </>                                                    │
│    );                                                       │
│  }                                                          │
│                                                             │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          │ Uses
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   <JobProgress> Component                   │
│                                                             │
│  - Renders progress bar                                     │
│  - Shows status messages                                    │
│  - Displays errors/success                                  │
│  - Uses useJobStatus hook internally                        │
│                                                             │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          │ Uses
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                 useJobStatus Hook                           │
│                                                             │
│  - Manages polling state                                    │
│  - Implements exponential backoff                           │
│  - Handles cleanup on unmount                               │
│  - Provides: { status, progress, message, result, error }   │
│                                                             │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          │ Calls
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                 fetch('/api/jobs/{job_id}')                 │
│                                                             │
│  Returns job status from backend                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 State Machine

```
                    ┌─────────────┐
                    │   PENDING   │
                    │  progress:0  │
                    └──────┬──────┘
                           │
             Job picked up by worker
                           │
                           ▼
                    ┌─────────────┐
                    │   RUNNING   │
                    │ progress:1-99│
                    └──────┬──────┘
                           │
                    ┌──────┴──────┐
                    │             │
            Success │             │ Error
                    │             │
                    ▼             ▼
            ┌─────────────┐  ┌─────────────┐
            │  COMPLETE   │  │   FAILED    │
            │ progress:100│  │ error:msg   │
            └─────────────┘  └─────────────┘
                    │             │
                    └──────┬──────┘
                           │
              Cleanup after 24 hours
                           │
                           ▼
                    ┌─────────────┐
                    │   DELETED   │
                    └─────────────┘
```

---

## 🎨 UI States

```
┌─────────────────────────────────────────────────────────┐
│  PENDING STATE                                          │
│  ┌───────────────────────────────────────────────────┐ │
│  │ ⏱️  Processing Transactions                       │ │
│  │                                                    │ │
│  │ [░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 0%          │ │
│  │ Job queued                                         │ │
│  └───────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  RUNNING STATE                                          │
│  ┌───────────────────────────────────────────────────┐ │
│  │ ⏳ Processing Transactions                        │ │
│  │                                                    │ │
│  │ [████████████░░░░░░░░░░░░░░░░░░░░] 45%           │ │
│  │ Processing transaction 45/100...                  │ │
│  │                                                    │ │
│  │ 45% complete                                       │ │
│  └───────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  COMPLETE STATE                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │ ✅ Processing Transactions                        │ │
│  │                                                    │ │
│  │ [██████████████████████████████████] 100%         │ │
│  │ Complete                                           │ │
│  │                                                    │ │
│  │ ┌─────────────────────────────────────────────┐  │ │
│  │ │ ✓ Job completed successfully!                │  │ │
│  │ │                                               │  │ │
│  │ │ Results:                                      │  │ │
│  │ │ - Journal entries created: 95                 │  │ │
│  │ │ - High confidence: 80                         │  │ │
│  │ │ - Needs review: 15                            │  │ │
│  │ └─────────────────────────────────────────────┘  │ │
│  └───────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  FAILED STATE                                           │
│  ┌───────────────────────────────────────────────────┐ │
│  │ ❌ Processing Transactions                        │ │
│  │                                                    │ │
│  │ [████████░░░░░░░░░░░░░░░░░░░░░░░░] 35%           │ │
│  │ Job failed                                         │ │
│  │                                                    │ │
│  │ ┌─────────────────────────────────────────────┐  │ │
│  │ │ Error:                                        │  │ │
│  │ │ Database connection timeout                   │  │ │
│  │ └─────────────────────────────────────────────┘  │ │
│  └───────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

---

## 🔗 Data Flow

```
USER INPUT
    │
    └──▶ Upload CSV file (3000 transactions)
            │
            │ POST /api/jobs/upload-and-categorize
            │
            ▼
        ┌─────────────────────────────────┐
        │  API ENDPOINT                   │
        │  - Validates file               │
        │  - Creates job ID               │
        │  - Enqueues task                │
        │  - Returns job_id immediately   │
        └───────────┬─────────────────────┘
                    │
                    ├─────▶ JOB QUEUE
                    │       {
                    │         id: "job_xyz",
                    │         status: "pending",
                    │         meta: { company_id, file_name }
                    │       }
                    │
                    ▼
        ┌─────────────────────────────────┐
        │  WORKER THREAD                  │
        │                                 │
        │  Progress: 0% → Parse CSV       │
        │  Progress: 20% → Validate data  │
        │  Progress: 30% → Insert DB      │
        │  Progress: 50% → Run rules      │
        │  Progress: 70% → Call LLM       │
        │  Progress: 90% → Create JEs     │
        │  Progress: 100% → Done!         │
        │                                 │
        │  Result: {                      │
        │    parsed: 3000,                │
        │    inserted: 2950,              │
        │    categorized: 2950,           │
        │    je_created: 2950             │
        │  }                              │
        └───────────┬─────────────────────┘
                    │
                    ▼
        ┌─────────────────────────────────┐
        │  DATABASE                       │
        │  - 2950 new TransactionDB rows  │
        │  - 2950 new JournalEntryDB rows │
        │  - Updated metadata             │
        └─────────────────────────────────┘
```

---

## 🎯 Key Takeaways

1. **Immediate Response**: API returns job_id in ~100ms
2. **Background Processing**: Actual work happens in separate thread
3. **Real-time Updates**: Progress tracked at every step
4. **Smart Polling**: Exponential backoff (1s → 5s max)
5. **Type-Safe**: Full TypeScript + Pydantic validation
6. **Error Handling**: Comprehensive error capture + user-friendly messages
7. **Automatic Cleanup**: Jobs deleted after 24 hours
8. **No External Deps**: Works with in-memory queue (Redis optional)

---

## 🚀 Next Steps

1. **Try It:** Visit `/dashboard/background-jobs`
2. **Integrate:** Add `<JobProgress>` to your pages
3. **Customize:** Create your own background tasks
4. **Deploy:** Works out of the box, no Redis required!

**You're all set! 🎉**


# API Route Loading Issue - Immediate Fix Required

## 🔴 CRITICAL ISSUE

The Cloud Run API deployment is NOT loading any application routes. Only health check endpoints are available.

### Current Status
- **Deployed Revision:** ai-bookkeeper-api-00011-8mn
- **Available Endpoints:** Only /, /healthz, /readyz
- **Missing:** All /api/auth/* and other application routes
- **Impact:** Frontend cannot sign up users - getting "Not Found" errors

### Root Cause
The router imports in `app/api/main.py` are failing silently during startup, likely due to:
1. Missing dependencies for auth module
2. Database connection issues during import
3. Other module import failures

### Immediate Solutions

#### Option 1: Use Minimal Working API (FASTEST - 10 minutes)
Create a minimal FastAPI app with just auth routes:

```python
# app/api/main_minimal.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
import os

app = FastAPI(title="AI Bookkeeper API")

# CORS
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database
def get_db():
    from app.db.session import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Models
class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str

# Routes
@app.get("/")
async def root():
    return {"message": "AI Bookkeeper API", "version": "0.2.1-beta"}

@app.get("/healthz")
async def health():
    return {"status": "ok"}

@app.post("/api/auth/signup")
async def signup(request: SignupRequest, db: Session = Depends(get_db)):
    from app.db.models import UserDB
    from app.auth.security import get_password_hash
    import uuid
    
    # Check existing
    existing = db.query(UserDB).filter(UserDB.email == request.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    user_id = f"user-{uuid.uuid4().hex[:8]}"
    user = UserDB(
        user_id=user_id,
        email=request.email,
        password_hash=get_password_hash(request.password),
        role="owner",
        is_active=True
    )
    db.add(user)
    db.commit()
    
    return {"success": True, "user_id": user_id, "email": request.email}

@app.post("/api/auth/login")
async def login(request: dict, db: Session = Depends(get_db)):
    from app.db.models import UserDB
    from app.auth.security import verify_password
    from app.auth.jwt_handler import create_access_token
    
    user = db.query(UserDB).filter(UserDB.email == request["email"]).first()
    if not user or not verify_password(request["password"], user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token(user_id=user.user_id, email=user.email, role=user.role, tenant_ids=[])
    return {"user_id": user.user_id, "email": user.email, "role": user.role, "token": token}
```

Update Dockerfile:
```dockerfile
CMD ["uvicorn", "api.main_minimal:app", "--host", "0.0.0.0", "--port", "8080"]
```

#### Option 2: Debug Import Errors (THOROUGH - 30 minutes)
Add detailed error logging to catch what's failing:

```python
# In app/api/main.py or main_cloudrun.py
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

try:
    from app.api import auth as auth_router
    app.include_router(auth_router.router)
    logger.info("✅ Auth routes loaded successfully")
except Exception as e:
    logger.error(f"❌ Failed to load auth routes: {type(e).__name__}: {str(e)}")
    import traceback
    logger.error(traceback.format_exc())
```

#### Option 3: Use Frontend Proxy (WORKAROUND - 15 minutes)
Have Vercel proxy auth requests to a working Render instance temporarily.

### Recommended Action

**Implement Option 1 immediately** - create `main_minimal.py` with just the essential auth endpoints to unblock user signups while we debug the full API.

### Testing Commands

After fix:
```bash
# Test signup
curl -X POST https://ai-bookkeeper-api-644842661403.us-central1.run.app/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass123","full_name":"Test User"}'

# Should return:
# {"success":true,"user_id":"user-xxxxxxxx","email":"test@example.com"}
```

### Priority: URGENT
This blocks the entire signup flow and Google Ads launch.

---

**Status:** Issue identified, solutions proposed  
**Next Action:** Implement Option 1 (minimal working API)  
**ETA:** 10-15 minutes

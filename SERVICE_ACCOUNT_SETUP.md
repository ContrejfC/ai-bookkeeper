# Google Cloud Service Account Setup - Detailed Guide

**Purpose:** Create a service account with minimal required permissions for AI Bookkeeper Cloud Run migration

---

## 🎯 STEP-BY-STEP SERVICE ACCOUNT CREATION

### **Step 1: Navigate to Service Accounts**

1. **Go to:** [Google Cloud Console](https://console.cloud.google.com/)
2. **Select your project** (or create one if needed)
3. **Navigate to:** IAM & Admin → Service Accounts
4. **Click:** "CREATE SERVICE ACCOUNT" (blue button)

### **Step 2: Basic Service Account Information**

**Service Account Details:**
- **Service account name:** `ai-bookkeeper-migration`
- **Service account ID:** `ai-bookkeeper-migration` (auto-filled)
- **Description:** `Service account for AI Bookkeeper Cloud Run migration with minimal required permissions`

**Click:** "CREATE AND CONTINUE"

### **Step 3: Grant Access (IAM Roles)**

**Add these roles one by one:**

#### **Required Roles:**

1. **Cloud Run Admin**
   - **Role:** `Cloud Run Admin`
   - **Purpose:** Deploy and manage Cloud Run services
   - **Search:** "run.admin" or "Cloud Run Admin"

2. **Cloud Build Editor**
   - **Role:** `Cloud Build Editor`
   - **Purpose:** Build and deploy container images
   - **Search:** "cloudbuild.builds.editor" or "Cloud Build Editor"

3. **Artifact Registry Writer**
   - **Role:** `Artifact Registry Writer`
   - **Purpose:** Push container images to Artifact Registry
   - **Search:** "artifactregistry.writer" or "Artifact Registry Writer"

4. **Secret Manager Admin**
   - **Role:** `Secret Manager Admin`
   - **Purpose:** Create and manage secrets (JWT, API keys)
   - **Search:** "secretmanager.admin" or "Secret Manager Admin"

5. **Service Account User**
   - **Role:** `Service Account User`
   - **Purpose:** Use service account for authentication
   - **Search:** "iam.serviceAccountUser" or "Service Account User"

#### **Optional Roles (if using Cloud SQL):**

6. **Cloud SQL Admin** (only if `CLOUD_SQL=true`)
   - **Role:** `Cloud SQL Admin`
   - **Purpose:** Manage Cloud SQL instances
   - **Search:** "sql.admin" or "Cloud SQL Admin"

**After adding each role, click:** "CONTINUE"

### **Step 4: Grant Users Access (Optional)**

**Skip this step** - we don't need to grant access to users for this migration.

**Click:** "DONE"

### **Step 5: Create and Download Key**

1. **Find your service account** in the list
2. **Click on the service account name** (`ai-bookkeeper-migration`)
3. **Go to:** "KEYS" tab
4. **Click:** "ADD KEY" → "Create new key"
5. **Select:** "JSON" format
6. **Click:** "CREATE"

**The JSON key file will download automatically**

### **Step 6: Secure the Key File**

```bash
# Move the downloaded file to a secure location
mv ~/Downloads/ai-bookkeeper-migration-*.json ~/.gcp/service-account.json

# Set proper permissions
chmod 600 ~/.gcp/service-account.json

# Verify the file
cat ~/.gcp/service-account.json | jq '.project_id'
```

---

## 🔍 VERIFICATION STEPS

### **Verify Service Account Permissions**

```bash
# Set your project ID
export PROJECT="your-project-id"
export GCP_SA_JSON_PATH="~/.gcp/service-account.json"

# Authenticate with service account
gcloud auth activate-service-account --key-file "$GCP_SA_JSON_PATH"
gcloud config set project "$PROJECT"

# Test permissions
echo "Testing Cloud Run permissions..."
gcloud run services list --region=us-central1

echo "Testing Cloud Build permissions..."
gcloud builds list --limit=1

echo "Testing Artifact Registry permissions..."
gcloud artifacts repositories list

echo "Testing Secret Manager permissions..."
gcloud secrets list
```

### **Expected Output:**
- All commands should execute without permission errors
- If any fail, the service account is missing required roles

---

## 🚨 TROUBLESHOOTING

### **Permission Denied Errors**

**If you get permission errors:**

1. **Check IAM roles:**
   ```bash
   gcloud projects get-iam-policy $PROJECT --flatten="bindings[].members" --format="table(bindings.role)" --filter="bindings.members:ai-bookkeeper-migration@$PROJECT.iam.gserviceaccount.com"
   ```

2. **Add missing roles:**
   - Go to IAM & Admin → IAM
   - Find your service account
   - Click "Edit" (pencil icon)
   - Add missing roles

### **Common Issues:**

**"Cloud Run API not enabled":**
```bash
gcloud services enable run.googleapis.com
```

**"Cloud Build API not enabled":**
```bash
gcloud services enable cloudbuild.googleapis.com
```

**"Artifact Registry API not enabled":**
```bash
gcloud services enable artifactregistry.googleapis.com
```

**"Secret Manager API not enabled":**
```bash
gcloud services enable secretmanager.googleapis.com
```

---

## 📋 SERVICE ACCOUNT SUMMARY

**Created Service Account:**
- **Name:** `ai-bookkeeper-migration`
- **Email:** `ai-bookkeeper-migration@[PROJECT-ID].iam.gserviceaccount.com`
- **Key File:** `~/.gcp/service-account.json`

**Permissions Granted:**
- ✅ Cloud Run Admin (`run.admin`)
- ✅ Cloud Build Editor (`cloudbuild.builds.editor`)
- ✅ Artifact Registry Writer (`artifactregistry.writer`)
- ✅ Secret Manager Admin (`secretmanager.admin`)
- ✅ Service Account User (`iam.serviceAccountUser`)
- ✅ Cloud SQL Admin (`sql.admin`) - if needed

**Security Notes:**
- Key file has restricted permissions (600)
- Service account has minimal required permissions
- Can be deleted after migration if needed

---

## 🎯 NEXT STEPS

After creating the service account:

1. **Set environment variable:**
   ```bash
   export GCP_SA_JSON_PATH="~/.gcp/service-account.json"
   ```

2. **Run prerequisites check:**
   ```bash
   bash scripts/check_prerequisites.sh
   ```

3. **Execute migration:**
   ```bash
   bash scripts/gcp_migrate.sh
   ```

**The service account is now ready for the Cloud Run migration!** 🚀

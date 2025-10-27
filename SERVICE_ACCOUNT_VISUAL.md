# Google Cloud Service Account Setup - Visual Guide

## 🎯 SERVICE ACCOUNT CREATION FLOW

```
Google Cloud Console
    ↓
IAM & Admin → Service Accounts
    ↓
CREATE SERVICE ACCOUNT
    ↓
Service Account Details:
├── Name: ai-bookkeeper-migration
├── ID: ai-bookkeeper-migration
└── Description: AI Bookkeeper migration service account
    ↓
Grant Access (IAM Roles):
├── Cloud Run Admin (run.admin)
├── Cloud Build Editor (cloudbuild.builds.editor)
├── Artifact Registry Writer (artifactregistry.writer)
├── Secret Manager Admin (secretmanager.admin)
└── Service Account User (iam.serviceAccountUser)
    ↓
CREATE AND CONTINUE
    ↓
Grant Users Access: SKIP
    ↓
DONE
    ↓
Service Account Created
    ↓
KEYS Tab → ADD KEY → Create new key → JSON
    ↓
Download JSON Key File
    ↓
Secure the Key:
├── Move to ~/.gcp/service-account.json
├── chmod 600 ~/.gcp/service-account.json
└── Verify with: cat ~/.gcp/service-account.json | jq '.project_id'
```

## 🔐 PERMISSIONS BREAKDOWN

| Role | Purpose | Required For |
|------|---------|--------------|
| **Cloud Run Admin** | Deploy/manage Cloud Run services | API deployment |
| **Cloud Build Editor** | Build container images | Docker builds |
| **Artifact Registry Writer** | Push images to registry | Image storage |
| **Secret Manager Admin** | Manage secrets (JWT, API keys) | Secure configuration |
| **Service Account User** | Use service account for auth | Authentication |

## 🚨 COMMON MISTAKES TO AVOID

❌ **Don't use overly broad roles** like "Owner" or "Editor"  
❌ **Don't skip the JSON key download**  
❌ **Don't leave the key file in Downloads**  
❌ **Don't forget to set proper file permissions**  
❌ **Don't share the JSON key file**  

✅ **Use minimal required permissions**  
✅ **Download and secure the JSON key**  
✅ **Test permissions before migration**  
✅ **Keep the key file private**  

## 🔍 VERIFICATION COMMANDS

```bash
# 1. Authenticate with service account
gcloud auth activate-service-account --key-file ~/.gcp/service-account.json

# 2. Set project
gcloud config set project YOUR_PROJECT_ID

# 3. Test Cloud Run permissions
gcloud run services list --region=us-central1

# 4. Test Cloud Build permissions
gcloud builds list --limit=1

# 5. Test Artifact Registry permissions
gcloud artifacts repositories list

# 6. Test Secret Manager permissions
gcloud secrets list
```

## 📋 CHECKLIST

- [ ] Service account created with name `ai-bookkeeper-migration`
- [ ] All 5 required roles added
- [ ] JSON key downloaded
- [ ] Key file moved to secure location
- [ ] File permissions set to 600
- [ ] Permissions tested with gcloud commands
- [ ] Environment variable set: `GCP_SA_JSON_PATH`

## 🎯 NEXT STEPS

After service account setup:

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

**Service account setup complete! Ready for Cloud Run migration.** 🚀


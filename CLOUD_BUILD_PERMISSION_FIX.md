# Fix Cloud Build Service Account Permission - Detailed Guide

## 🎯 PROBLEM
Your migration service account needs permission to **use** the Cloud Build service account to build Docker images.

## 📋 DETAILED STEP-BY-STEP INSTRUCTIONS

### **Step 1: Navigate to IAM & Admin**

1. **Open your browser** and go to:
   ```
   https://console.cloud.google.com/iam-admin/iam?project=bright-fastness-475700-j2
   ```

2. You should see a page titled **"IAM"** with a list of principals (users and service accounts)

---

### **Step 2: Locate Your Migration Service Account**

1. **Scroll through the list** or use the **filter box** at the top
2. **Search for:** `id-ai-bookkeeper-migration`
3. You should see:
   ```
   id-ai-bookkeeper-migration@bright-fastness-475700-j2.iam.gserviceaccount.com
   ```
4. **Verify** it has these roles (you added these earlier):
   - Cloud Run Admin
   - Cloud Build Editor
   - Artifact Registry Repository Administrator
   - Secret Manager Admin
   - Service Account User
   - Storage Admin
   - Service Usage Admin
   - Service Account Token Creator

---

### **Step 3: Add Service Account User Role (If Not Already There)**

**Check if the role is already there:**
- Look at the roles listed for `id-ai-bookkeeper-migration@...`
- If you see **"Service Account User"** - it's there, but we need it on the **Cloud Build SA specifically**

**If "Service Account User" is NOT there at the project level:**
1. Click the **pencil icon** (✏️) next to the service account name
2. Click **"ADD ANOTHER ROLE"**
3. In the dropdown, search for: `Service Account User`
4. Select **"Service Account User"**
5. Click **"SAVE"**

---

### **Step 4: Grant Permission on Cloud Build Service Account (CRITICAL)**

This is the key step that's missing!

#### **Option A: Using IAM Page (Recommended)**

1. **Stay on the IAM page** (https://console.cloud.google.com/iam-admin/iam?project=bright-fastness-475700-j2)

2. **Click "GRANT ACCESS"** button (top of page)

3. **In the "New principals" field, paste:**
   ```
   id-ai-bookkeeper-migration@bright-fastness-475700-j2.iam.gserviceaccount.com
   ```

4. **In the "Select a role" dropdown:**
   - Search for: `Service Account User`
   - Select: **"Service Account User"**

5. **Click "ADD ANOTHER ROLE"**

6. **Add second role:**
   - Search for: `Service Account Token Creator`
   - Select: **"Service Account Token Creator"**

7. **Click "SAVE"**

8. **Wait 2-3 minutes** for permissions to propagate

#### **Option B: Using Service Accounts Page (Alternative)**

1. **Go to Service Accounts page:**
   ```
   https://console.cloud.google.com/iam-admin/serviceaccounts?project=bright-fastness-475700-j2
   ```

2. **Find the Compute Engine default service account:**
   - Look for an email ending in: `@developer.gserviceaccount.com`
   - OR look for: `[PROJECT_NUMBER]@cloudbuild.gserviceaccount.com`
   - The number `108280552423305078080` from the error

3. **Click on that service account** (click the email address)

4. **Go to the "PERMISSIONS" tab** (at the top)

5. **Click "GRANT ACCESS"**

6. **In "New principals", enter:**
   ```
   id-ai-bookkeeper-migration@bright-fastness-475700-j2.iam.gserviceaccount.com
   ```

7. **Select role:** `Service Account User`

8. **Click "SAVE"**

---

### **Step 5: Enable Cloud Build to Use Default Service Account**

1. **Go to Cloud Build Settings:**
   ```
   https://console.cloud.google.com/cloud-build/settings/service-account?project=bright-fastness-475700-j2
   ```

2. **Check the service account being used:**
   - You should see either:
     - **"Cloud Build Service Account"** (default)
     - **"Compute Engine default service account"**

3. **If you see any "DISABLED" services, enable them:**
   - Scroll down to see status of various services
   - Look for **"Service Accounts"** or **"Service Account User"**
   - If it says "DISABLED", click **"ENABLE"**

---

### **Step 6: Alternative - Use Compute Engine Service Account**

If Cloud Build service account doesn't exist or has issues:

1. **Go to IAM page:**
   ```
   https://console.cloud.google.com/iam-admin/iam?project=bright-fastness-475700-j2
   ```

2. **Find the Compute Engine default service account:**
   - Look for: `[PROJECT_NUMBER]-compute@developer.gserviceaccount.com`
   - Example: `644842661403-compute@developer.gserviceaccount.com`

3. **Click the pencil icon** to edit it

4. **Add these roles if missing:**
   - Cloud Build Service Account
   - Service Account User

5. **Click "SAVE"**

---

### **Step 7: Verify Permissions**

After completing the above steps:

1. **Wait 2-3 minutes** for permissions to propagate

2. **Run this verification:**
   ```bash
   gcloud projects get-iam-policy bright-fastness-475700-j2 \
     --flatten="bindings[].members" \
     --format="table(bindings.role)" \
     --filter="bindings.members:id-ai-bookkeeper-migration@bright-fastness-475700-j2.iam.gserviceaccount.com"
   ```

3. **You should see:**
   - roles/iam.serviceAccountUser
   - roles/iam.serviceAccountTokenCreator
   - Plus all the other roles

---

## 🎯 SUMMARY OF REQUIRED ACTIONS

**COMPLETED:**
- ✅ Service account created
- ✅ Basic roles assigned (Cloud Run, Cloud Build, etc.)
- ✅ Artifact Registry repository created manually

**STILL NEEDED:**
- ❌ Grant Service Account User role at PROJECT level
- ❌ Grant Service Account Token Creator at PROJECT level
- ❌ Ensure Cloud Build can use service accounts

**The key is:** Your migration service account needs permission to "impersonate" or "act as" the Cloud Build service account.

---

## 🚨 IF STILL HAVING ISSUES

**Try the simplest approach:**

1. Go to: https://console.cloud.google.com/iam-admin/iam?project=bright-fastness-475700-j2
2. Click "GRANT ACCESS"
3. Paste: `id-ai-bookkeeper-migration@bright-fastness-475700-j2.iam.gserviceaccount.com`
4. Add these roles:
   - **Editor** (this gives broad permissions - we can restrict later)
5. Click "SAVE"
6. Wait 2 minutes
7. Try the migration again

**Note:** Editor role is broad but will let us complete the migration. We can remove it and use minimal roles after deployment succeeds.

---

## 📞 READY TO CONTINUE?

After completing these steps, type **'done'** and I'll run the migration again.


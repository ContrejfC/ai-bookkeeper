# AI Bookkeeper - OpenAPI Diff Report
**Generated:** 2025-10-15  
**Previous Version:** Not available (first export)  
**Current Version:** 0.2.1-beta  
**OpenAPI Spec:** 3.1.0

## Summary
This is the first OpenAPI export for AI Bookkeeper. No previous version exists for comparison.

## Current OpenAPI Status
- **Total Endpoints:** 33+ REST endpoints documented
- **Authentication:** JWT-based with cookie and bearer token support
- **RBAC:** Role-based access control (Owner, Staff, Public)
- **Response Formats:** JSON for API, HTML for UI endpoints
- **File Uploads:** Multipart form support for file operations

## Key API Features Documented

### Authentication Flow
```json
{
  "paths": {
    "/api/auth/login": {
      "post": {
        "operationId": "login_api_auth_login_post",
        "tags": ["auth"],
        "summary": "Login",
        "description": "Authenticate user and issue JWT token"
      }
    }
  }
}
```

### Multi-Tenant Architecture
- Tenant management with RBAC
- Settings configuration with validation
- Owner vs Staff permission levels

### Rules Engine
- Candidate rule management
- Dry-run simulation capabilities
- Version control with rollback support
- Audit trail for all rule changes

### Export/Import System
- QuickBooks (IIF and CSV formats)
- Xero CSV format
- Chart of accounts import
- Idempotent export tracking

### Compliance & Audit
- Streaming CSV export for audit logs
- SOC2 compliance endpoints
- Access snapshot capabilities
- Data retention management

## Missing from OpenAPI (Not Yet Implemented)

### QBO OAuth2 Flow
```json
// NOT FOUND - These endpoints are missing:
"/api/auth/qbo": {
  "get": {
    "operationId": "qbo_oauth_init",
    "summary": "Initialize QuickBooks OAuth2 flow"
  }
},
"/api/auth/qbo/callback": {
  "get": {
    "operationId": "qbo_oauth_callback", 
    "summary": "Handle QBO OAuth2 callback"
  }
}
```

### Label Pipeline Management
```json
// NOT FOUND - These endpoints are missing:
"/api/labels/consent": {
  "post": {
    "operationId": "update_consent_toggle",
    "summary": "Update user consent for label collection"
  }
},
"/api/labels/export": {
  "get": {
    "operationId": "export_training_data",
    "summary": "Export user training data"
  }
},
"/api/labels/purge": {
  "delete": {
    "operationId": "purge_user_data",
    "summary": "Purge user training data"
  }
}
```

### ChatGPT Actions Integration
The following endpoints are ACTIONS-ready with proper operationIds:

✅ **Implemented & ACTIONS-Ready:**
- `login_api_auth_login_post`
- `signup_api_auth_signup_post`
- `list_tenants_api_tenants_get`
- `list_candidates_api_rules_candidates_get`
- `dryrun_rule_promotion_api_rules_dryrun_post`
- `accept_candidate_api_rules_candidates__id__accept_post`
- `reject_candidate_api_rules_candidates__id__reject_post`
- `upload_statement_api_upload_post`
- `propose_journal_entries_api_post_propose_post`
- `approve_journal_entries_api_post_approve_post`
- `export_quickbooks_api_export_quickbooks_post`
- `export_xero_api_export_xero_post`

❌ **Missing ACTIONS Integration:**
- No `/actions` endpoint for ChatGPT Actions discovery
- No Actions-specific schema definitions
- No webhook endpoints for Actions callbacks

## Schema Definitions

### Key Request/Response Models
- `LoginRequest` / `LoginResponse` - Authentication
- `TenantSettings` - Tenant configuration
- `CandidateResponse` - Rule candidates
- `DryRunRequest` / `DryRunResponse` - Rule simulation
- `NotificationSettings` - Notification preferences
- `CheckoutRequest` / `CheckoutResponse` - Billing integration

### Security Schemes
```json
{
  "securitySchemes": {
    "cookieAuth": {
      "type": "apiKey",
      "in": "cookie",
      "name": "access_token"
    },
    "bearerAuth": {
      "type": "http",
      "scheme": "bearer",
      "bearerFormat": "JWT"
    }
  }
}
```

## Validation Rules

### Tenant Settings
- `autopost_threshold`: 0.80 - 0.98
- `llm_tenant_cap_usd`: 0.0 - 10000.0

### Authentication
- Email format validation
- Password requirements (implemented in backend)
- Magic token support for dev mode

## Error Handling

### Standard Error Format
```json
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "error message",
      "type": "error_type"
    }
  ]
}
```

### Common Error Codes
- `401` - Unauthorized (authentication required)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found (resource doesn't exist)
- `422` - Validation Error (invalid request data)
- `500` - Internal Server Error

## File Operations

### Supported Upload Formats
- **Receipts:** PDF, images
- **Bank Statements:** CSV, OFX
- **Chart of Accounts:** CSV, IIF
- **Export Formats:** IIF (QuickBooks Desktop), CSV (QBO, Xero)

### Multipart Form Handling
All file upload endpoints use `multipart/form-data` with proper file validation and processing.

## Streaming Responses

### Audit CSV Export
```json
{
  "/api/audit/export.csv": {
    "get": {
      "description": "Stream audit log as CSV (memory-bounded for 100k+ rows)",
      "responses": {
        "200": {
          "content": {
            "application/json": {}
          }
        }
      }
    }
  }
}
```

## Next Steps for OpenAPI Completeness

1. **Add QBO OAuth2 Endpoints**
   - `/api/auth/qbo` - OAuth2 initiation
   - `/api/auth/qbo/callback` - OAuth2 callback
   - `/api/auth/qbo/refresh` - Token refresh

2. **Implement Label Pipeline APIs**
   - Consent management endpoints
   - Data export/purge functionality
   - Training data collection APIs

3. **Add ChatGPT Actions Integration**
   - `/actions` discovery endpoint
   - Actions-specific schema definitions
   - Webhook endpoints for Actions callbacks

4. **Enhance Error Documentation**
   - Detailed error code documentation
   - Error recovery guidance
   - Rate limiting information

5. **Add Webhook Support**
   - Stripe webhook (already implemented)
   - QBO/Xero webhook endpoints
   - Notification webhook system

## OpenAPI File Location
- **Current:** `docs/openapi-latest.json`
- **Size:** ~50KB (comprehensive documentation)
- **Last Updated:** 2025-10-15
- **Generated From:** Live FastAPI application running on localhost:8001

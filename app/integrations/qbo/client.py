"""
QuickBooks Online API client for OAuth2 and journal entry posting.
"""

import os
import httpx
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

# QBO Configuration from environment
QBO_CLIENT_ID = os.getenv("QBO_CLIENT_ID", "")
QBO_CLIENT_SECRET = os.getenv("QBO_CLIENT_SECRET", "")
QBO_REDIRECT_URI = os.getenv("QBO_REDIRECT_URI", "http://localhost:8000/api/auth/qbo/callback")
QBO_SCOPES = os.getenv("QBO_SCOPES", "com.intuit.quickbooks.accounting")
QBO_BASE = os.getenv("QBO_BASE", "https://sandbox-quickbooks.api.intuit.com")
QBO_AUTHZ_URL = os.getenv("QBO_AUTHZ_URL", "https://appcenter.intuit.com/connect/oauth2")
QBO_TOKEN_URL = os.getenv("QBO_TOKEN_URL", "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer")

# HTTP client configuration
HTTP_TIMEOUT = 30.0
MAX_RETRIES = 3


class QBOClient:
    """QuickBooks Online API client."""
    
    def __init__(self):
        self.client_id = QBO_CLIENT_ID
        self.client_secret = QBO_CLIENT_SECRET
        self.base_url = QBO_BASE
    
    def get_authorization_url(self, state: str, redirect_uri: Optional[str] = None) -> str:
        """
        Generate OAuth2 authorization URL.
        
        Args:
            state: CSRF protection state token
            redirect_uri: OAuth redirect URI (optional)
        
        Returns:
            Authorization URL for redirect
        """
        params = {
            "client_id": self.client_id,
            "scope": QBO_SCOPES,
            "redirect_uri": redirect_uri or QBO_REDIRECT_URI,
            "response_type": "code",
            "state": state
        }
        
        return f"{QBO_AUTHZ_URL}?{urlencode(params)}"
    
    async def exchange_code_for_tokens(
        self,
        code: str,
        redirect_uri: Optional[str] = None,
        realm_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Exchange authorization code for access and refresh tokens.
        
        Args:
            code: Authorization code from OAuth callback
            redirect_uri: OAuth redirect URI (must match authorization)
            realm_id: QuickBooks company ID (realmId)
        
        Returns:
            {
                "access_token": str,
                "refresh_token": str,
                "expires_in": int,
                "expires_at": datetime,
                "realm_id": str
            }
        """
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            response = await client.post(
                QBO_TOKEN_URL,
                auth=(self.client_id, self.client_secret),
                headers={"Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"},
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": redirect_uri or QBO_REDIRECT_URI
                }
            )
            
            if response.status_code != 200:
                logger.error(f"QBO token exchange failed: {response.status_code} {response.text}")
                raise Exception(f"Token exchange failed: {response.status_code}")
            
            data = response.json()
            
            # Calculate expiration
            expires_in = data.get("expires_in", 3600)
            expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            
            return {
                "access_token": data["access_token"],
                "refresh_token": data["refresh_token"],
                "expires_in": expires_in,
                "expires_at": expires_at,
                "realm_id": realm_id or data.get("realmId")
            }
    
    async def refresh_tokens(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh access token using refresh token.
        
        Args:
            refresh_token: Refresh token from previous OAuth flow
        
        Returns:
            {
                "access_token": str,
                "refresh_token": str,
                "expires_in": int,
                "expires_at": datetime
            }
        """
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            response = await client.post(
                QBO_TOKEN_URL,
                auth=(self.client_id, self.client_secret),
                headers={"Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"},
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token
                }
            )
            
            if response.status_code != 200:
                logger.error(f"QBO token refresh failed: {response.status_code}")
                raise Exception(f"Token refresh failed: {response.status_code}")
            
            data = response.json()
            
            # Calculate expiration
            expires_in = data.get("expires_in", 3600)
            expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            
            return {
                "access_token": data["access_token"],
                "refresh_token": data["refresh_token"],
                "expires_in": expires_in,
                "expires_at": expires_at
            }
    
    async def get_chart_of_accounts(
        self,
        realm_id: str,
        access_token: str
    ) -> List[Dict[str, Any]]:
        """
        Get chart of accounts from QuickBooks.
        
        Args:
            realm_id: QuickBooks company ID
            access_token: OAuth access token
        
        Returns:
            List of account dictionaries
        """
        url = f"{self.base_url}/v3/company/{realm_id}/query"
        query = "SELECT * FROM Account"
        
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            response = await client.get(
                url,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json"
                },
                params={"query": query}
            )
            
            if response.status_code == 401:
                raise Exception("QBO_UNAUTHORIZED")
            
            if response.status_code != 200:
                logger.error(f"QBO CoA fetch failed: {response.status_code}")
                raise Exception(f"QBO API error: {response.status_code}")
            
            data = response.json()
            return data.get("QueryResponse", {}).get("Account", [])
    
    async def post_journal_entry(
        self,
        realm_id: str,
        access_token: str,
        je_payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Post journal entry to QuickBooks Online.
        
        Args:
            realm_id: QuickBooks company ID
            access_token: OAuth access token
            je_payload: Journal entry payload (QBO format)
        
        Returns:
            {
                "qbo_doc_id": str,
                "sync_token": str,
                "txn_date": str
            }
        
        Raises:
            Exception with QBO error code on failure
        """
        url = f"{self.base_url}/v3/company/{realm_id}/journalentry"
        
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            response = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                },
                json=je_payload
            )
            
            # Handle errors
            if response.status_code == 401:
                logger.warning("QBO authorization expired")
                raise Exception("QBO_UNAUTHORIZED")
            
            if response.status_code == 429:
                # Rate limited
                retry_after = response.headers.get("Retry-After", "60")
                logger.warning(f"QBO rate limited, retry after {retry_after}s")
                raise Exception(f"QBO_RATE_LIMITED:{retry_after}")
            
            if response.status_code >= 500:
                logger.error(f"QBO upstream error: {response.status_code}")
                raise Exception("QBO_UPSTREAM")
            
            if response.status_code >= 400:
                # QBO validation error
                error_data = response.json()
                error_msg = error_data.get("Fault", {}).get("Error", [{}])[0].get("Message", "Unknown error")
                logger.error(f"QBO validation error: {error_msg}")
                raise Exception(f"QBO_VALIDATION:{error_msg}")
            
            # Success
            data = response.json()
            journal_entry = data.get("JournalEntry", {})
            
            return {
                "qbo_doc_id": journal_entry.get("Id"),
                "sync_token": journal_entry.get("SyncToken"),
                "txn_date": journal_entry.get("TxnDate")
            }
    
    def build_journal_entry_payload(
        self,
        txn_date: str,
        lines: List[Dict[str, Any]],
        ref_number: Optional[str] = None,
        private_note: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Build QBO journal entry payload from simplified format.
        
        Args:
            txn_date: Transaction date (YYYY-MM-DD)
            lines: List of {amount, postingType, accountRef}
            ref_number: Optional reference number
            private_note: Optional private note
        
        Returns:
            QBO-formatted journal entry payload
        """
        qbo_lines = []
        
        for line in lines:
            qbo_lines.append({
                "Amount": float(line["amount"]),
                "DetailType": "JournalEntryLineDetail",
                "JournalEntryLineDetail": {
                    "PostingType": line["postingType"],
                    "AccountRef": {
                        "value": str(line["accountRef"]["value"])
                    }
                }
            })
        
        payload = {
            "TxnDate": txn_date,
            "Line": qbo_lines
        }
        
        if ref_number:
            payload["DocNumber"] = ref_number
        
        if private_note:
            payload["PrivateNote"] = private_note
        
        return payload


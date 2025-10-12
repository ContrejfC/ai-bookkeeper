"""
Notification Triggers (Phase 2a).

Wire-up guide for 5 alert types:
1. PSI > 0.20
2. LLM budget fallback
3. JE imbalance
4. Export completed
5. Cold-start graduated
"""
from sqlalchemy.orm import Session
from app.notifications.sender import send_notification


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Trigger 1: PSI Alert (Data Drift)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def trigger_psi_alert(
    tenant_id: str,
    psi_vendor: float,
    psi_amount: float,
    db: Session
):
    """
    Trigger PSI alert when vendor OR amount PSI > 0.20.
    
    Location to integrate: Where PSI is calculated (drift detection).
    
    Usage:
    ```python
    from app.notifications.triggers import trigger_psi_alert
    
    # After PSI calculation
    if psi_vendor > 0.20 or psi_amount > 0.20:
        trigger_psi_alert(
            tenant_id=tenant_id,
            psi_vendor=psi_vendor,
            psi_amount=psi_amount,
            db=db
        )
    ```
    """
    send_notification(
        tenant_id=tenant_id,
        notification_type="psi_alert",
        subject="⚠️ Data Drift Detected",
        message=(
            f"Population Stability Index exceeds threshold:\n\n"
            f"• Vendor PSI: {psi_vendor:.3f}\n"
            f"• Amount PSI: {psi_amount:.3f}\n\n"
            f"This indicates significant distribution shift. "
            f"Please review recent transactions and consider retraining."
        ),
        db=db
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Trigger 2: Budget Fallback
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def trigger_budget_fallback(
    tenant_id: str,
    spend_usd: float,
    cap_usd: float,
    db: Session
):
    """
    Trigger alert when LLM budget exceeded and fallback activated.
    
    Location to integrate: LLM budget tracker when fallback flips to true.
    
    Usage:
    ```python
    from app.notifications.triggers import trigger_budget_fallback
    
    # In LLM budget tracker
    if llm_budget_status.fallback_active:
        trigger_budget_fallback(
            tenant_id=tenant_id,
            spend_usd=current_spend,
            cap_usd=budget_cap,
            db=db
        )
    ```
    """
    send_notification(
        tenant_id=tenant_id,
        notification_type="budget_fallback",
        subject="⚠️ LLM Budget Exceeded",
        message=(
            f"LLM budget cap reached. System has fallen back to Rules/ML only.\n\n"
            f"• Current Spend: ${spend_usd:.2f}\n"
            f"• Monthly Cap: ${cap_usd:.2f}\n\n"
            f"LLM calls will resume next billing cycle or when budget is increased."
        ),
        db=db
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Trigger 3: JE Imbalance
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def trigger_je_imbalance(
    tenant_id: str,
    imbalance_count: int,
    db: Session
):
    """
    Trigger alert when unbalanced journal entries detected.
    
    Location to integrate: After JE validation in propose endpoint.
    
    Usage:
    ```python
    from app.notifications.triggers import trigger_je_imbalance
    
    # After checking je_imbalance_count
    if je_imbalance_count > 0:
        trigger_je_imbalance(
            tenant_id=tenant_id,
            imbalance_count=je_imbalance_count,
            db=db
        )
    ```
    """
    send_notification(
        tenant_id=tenant_id,
        notification_type="je_imbalance",
        subject="⚠️ Journal Entry Imbalance Detected",
        message=(
            f"Unbalanced journal entries found:\n\n"
            f"• Count: {imbalance_count} transaction(s)\n\n"
            f"Please review and correct imbalanced entries before posting. "
            f"Debits must equal credits for each entry."
        ),
        db=db
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Trigger 4: Export Completed
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def trigger_export_completed(
    tenant_id: str,
    posted_count: int,
    skipped_count: int,
    total_lines: int,
    db: Session
):
    """
    Trigger alert when QBO/Xero export finishes.
    
    Location to integrate: After export endpoint completes.
    
    Usage:
    ```python
    from app.notifications.triggers import trigger_export_completed
    
    # After export completes
    trigger_export_completed(
        tenant_id=tenant_id,
        posted_count=posted,
        skipped_count=skipped,
        total_lines=total_lines,
        db=db
    )
    ```
    """
    send_notification(
        tenant_id=tenant_id,
        notification_type="export_completed",
        subject="✅ Export Complete",
        message=(
            f"QBO/Xero export has finished:\n\n"
            f"• Posted: {posted_count} journal entries ({total_lines} lines)\n"
            f"• Skipped: {skipped_count} (duplicates)\n\n"
            f"Export file is ready for import."
        ),
        db=db
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Trigger 5: Cold-Start Graduated
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def trigger_coldstart_graduated(
    tenant_id: str,
    vendor_normalized: str,
    suggested_account: str,
    label_count: int,
    db: Session
):
    """
    Trigger alert when vendor graduates cold-start (≥3 consistent labels).
    
    Location to integrate: Cold-start tracking when label_count reaches threshold.
    
    Usage:
    ```python
    from app.notifications.triggers import trigger_coldstart_graduated
    
    # In cold-start tracking
    if label_count >= 3 and consistent:
        trigger_coldstart_graduated(
            tenant_id=tenant_id,
            vendor_normalized=vendor,
            suggested_account=account,
            label_count=label_count,
            db=db
        )
    ```
    """
    send_notification(
        tenant_id=tenant_id,
        notification_type="coldstart_graduated",
        subject="✅ Vendor Ready for Auto-Post",
        message=(
            f"Vendor has graduated cold-start and is eligible for auto-posting:\n\n"
            f"• Vendor: {vendor_normalized}\n"
            f"• Suggested Account: {suggested_account}\n"
            f"• Consistent Labels: {label_count}\n\n"
            f"Future transactions from this vendor can be auto-posted if confidence ≥ 0.90."
        ),
        db=db
    )


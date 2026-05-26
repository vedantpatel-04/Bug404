"""
Billing endpoints — Razorpay subscription management.
"""
from fastapi import APIRouter, Depends, HTTPException

from backend.app.core.security import TokenPayload, get_current_user, require_role, UserRole
from backend.app.services.billing import razorpay

router = APIRouter()


@router.get("/plans")
async def list_plans(
    user: TokenPayload = Depends(get_current_user),
):
    """List all ShelfIQ pricing plans (INR)."""
    plans = []
    for key, plan in razorpay.PLANS.items():
        plans.append({
            "key": key,
            "name": plan["name"],
            "price_inr": plan["amount"] / 100 if plan["amount"] > 0 else "Custom",
            "period": plan["period"],
            "description": plan["description"],
            "features": plan["features"],
        })
    return {"plans": plans, "currency": "INR", "gst_extra": True}


@router.post("/subscribe")
async def create_subscription(
    plan_key: str,
    user: TokenPayload = Depends(require_role(UserRole.STORE_OWNER)),
):
    """Create a Razorpay subscription for the org."""
    if plan_key not in razorpay.PLANS:
        raise HTTPException(status_code=400, detail=f"Unknown plan: {plan_key}")

    result = await razorpay.create_subscription(
        plan_id=f"plan_{plan_key}",  # Would be real Razorpay plan ID
        org_id=user.org_id or "unknown",
        customer_email=user.sub,
    )
    return result


@router.post("/verify")
async def verify_payment(
    razorpay_payment_id: str,
    razorpay_subscription_id: str,
    razorpay_signature: str,
    user: TokenPayload = Depends(get_current_user),
):
    """Verify a Razorpay payment after checkout."""
    is_valid = await razorpay.verify_payment(
        razorpay_payment_id, razorpay_subscription_id, razorpay_signature,
    )
    if not is_valid:
        raise HTTPException(status_code=400, detail="Payment verification failed")

    return {"status": "verified", "subscription_id": razorpay_subscription_id}


@router.get("/status")
async def billing_status(
    user: TokenPayload = Depends(get_current_user),
):
    """Get billing status for current org (grace period check)."""
    # In production, fetch plan_expires from DB
    from datetime import datetime, timedelta
    demo_expires = datetime.now() + timedelta(days=25)
    status = razorpay.check_grace_period(demo_expires)
    return {
        "org_id": user.org_id,
        "plan": "growth",
        "plan_expires": demo_expires.isoformat(),
        **status,
    }

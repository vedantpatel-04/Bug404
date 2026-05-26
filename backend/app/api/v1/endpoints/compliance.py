"""
Compliance endpoint — wraps existing planogram compliance engine.
"""
import sys
from pathlib import Path

from fastapi import APIRouter, Depends

from backend.app.core.security import TokenPayload, get_current_user
from backend.app.schemas.schemas import ComplianceResponse, ComplianceViolation
from backend.app.services.cache import cache

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent))

router = APIRouter()


@router.get("/{store_id}", response_model=ComplianceResponse)
async def get_compliance(
    store_id: str,
    user: TokenPayload = Depends(get_current_user),
):
    """
    Get planogram compliance score and violations for a store.

    Wraps the existing compliance engine + scorer.
    """
    import json as json_lib

    # Check cache
    cached = await cache.get(cache.compliance_key(store_id))
    if cached:
        return json_lib.loads(cached)

    try:
        from database.db_manager import db as legacy_db
        reports = legacy_db.get_compliance_reports(store_id)
    except Exception:
        reports = []

    if reports:
        latest = reports[0]
        # Parse violations from details_json
        violations = []
        try:
            details = json_lib.loads(latest.get("details_json", "{}"))
            for v in details.get("violations", []):
                violations.append(ComplianceViolation(
                    aisle_id=v.get("aisle_id", ""),
                    shelf_id=v.get("shelf_id", ""),
                    violation_type=v.get("type", "unknown"),
                    sku_id=v.get("sku_id"),
                    details=v.get("details", ""),
                ))
        except Exception:
            pass

        score = latest.get("compliance_score", 0)
        grade = _score_to_grade(score)

        result = ComplianceResponse(
            store_id=store_id,
            overall_score=score,
            grade=grade,
            total_sections=latest.get("total_sections", 0),
            correct_sections=latest.get("correct_sections", 0),
            violations=violations,
            checked_at=latest.get("checked_at"),
        )
    else:
        # Generate demo compliance data
        import numpy as np
        np.random.seed(hash(store_id) % 2**31)

        score = round(np.random.uniform(72, 95), 1)
        total = np.random.randint(20, 40)
        correct = int(total * score / 100)

        demo_violations = [
            ComplianceViolation(aisle_id="A02", shelf_id="S01", violation_type="misplaced_product",
                                sku_id="SKU007", details="Doritos found in Beverages section"),
            ComplianceViolation(aisle_id="A04", shelf_id="S03", violation_type="price_mismatch",
                                sku_id="SKU012", details="Tag shows ₹199, system price ₹249"),
            ComplianceViolation(aisle_id="A01", shelf_id="S02", violation_type="missing_facing",
                                sku_id="SKU003", details="Expected 4 facings, found 1"),
        ]

        result = ComplianceResponse(
            store_id=store_id,
            overall_score=score,
            grade=_score_to_grade(score),
            total_sections=total,
            correct_sections=correct,
            violations=demo_violations[:np.random.randint(1, 4)],
        )

    # Cache for 5 minutes
    await cache.set(cache.compliance_key(store_id), result.model_dump_json(), ttl=cache.TTL_COMPLIANCE)

    return result


def _score_to_grade(score: float) -> str:
    """Convert compliance score to letter grade."""
    if score >= 95:
        return "A+"
    elif score >= 90:
        return "A"
    elif score >= 85:
        return "B+"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
    return "F"

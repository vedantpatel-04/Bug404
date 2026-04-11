
"""
Compliance scorer — calculates aggregate compliance metrics and trends over time.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from datetime import datetime, timedelta
import numpy as np
from typing import Optional

from planogram.schemas import StoreComplianceReport


class ComplianceScorer:
    """
    Calculates and tracks compliance scores across time periods.
    Provides trend analysis and improvement recommendations.
    """

    def __init__(self):
        self.history = []  # List of past compliance reports

    def calculate_score(self, report: StoreComplianceReport) -> dict:
        """
        Calculate detailed compliance metrics from a report.

        Returns:
            Dict with score breakdown and grade.
        """
        total = report.total_sections
        if total == 0:
            return {"overall_score": 0, "grade": "N/A"}

        # Base score from compliant sections
        base_score = report.overall_score

        # Penalty deductions
        misplaced_penalty = (report.total_misplaced / total) * 15
        unauthorized_penalty = (report.total_unauthorized / total) * 25
        price_penalty = (report.total_price_mismatches / total) * 10

        adjusted_score = max(0, base_score - misplaced_penalty - unauthorized_penalty - price_penalty)

        # Grade assignment
        if adjusted_score >= 95:
            grade = "A+"
        elif adjusted_score >= 90:
            grade = "A"
        elif adjusted_score >= 85:
            grade = "B+"
        elif adjusted_score >= 80:
            grade = "B"
        elif adjusted_score >= 70:
            grade = "C"
        elif adjusted_score >= 60:
            grade = "D"
        else:
            grade = "F"

        return {
            "overall_score": round(adjusted_score, 1),
            "base_score": round(base_score, 1),
            "misplaced_penalty": round(misplaced_penalty, 1),
            "unauthorized_penalty": round(unauthorized_penalty, 1),
            "price_penalty": round(price_penalty, 1),
            "grade": grade,
            "total_sections": total,
            "compliant": report.compliant_sections,
            "violations": {
                "misplaced": report.total_misplaced,
                "missing": report.total_missing,
                "unauthorized": report.total_unauthorized,
                "price_mismatches": report.total_price_mismatches,
            },
            "aisle_scores": {
                ar.aisle_id: round(ar.compliance_score, 1)
                for ar in report.aisle_results
            },
        }

    def get_aisle_scores(self, report: StoreComplianceReport) -> list:
        """Get compliance scores per aisle, sorted worst-first."""
        scores = []
        for ar in report.aisle_results:
            scores.append({
                "aisle_id": ar.aisle_id,
                "aisle_name": ar.aisle_name,
                "score": round(ar.compliance_score, 1),
                "violations": ar.total_violations,
                "shelves": len(ar.shelf_results),
            })
        scores.sort(key=lambda x: x["score"])
        return scores

    def generate_recommendations(self, report: StoreComplianceReport) -> list:
        """Generate actionable recommendations from compliance report."""
        recs = []

        if report.total_missing > 0:
            recs.append({
                "priority": "HIGH",
                "category": "Stockout",
                "message": f"Restock {report.total_missing} empty sections to prevent revenue loss.",
                "impact": f"Estimated ${report.total_missing * 25:.0f}/day revenue at risk",
            })

        if report.total_misplaced > 0:
            recs.append({
                "priority": "MEDIUM",
                "category": "Product Placement",
                "message": f"Correct {report.total_misplaced} misplaced products to improve customer experience.",
                "impact": "Customer satisfaction and findability improvement",
            })

        if report.total_unauthorized > 0:
            recs.append({
                "priority": "HIGH",
                "category": "Unauthorized Products",
                "message": f"Remove {report.total_unauthorized} unauthorized products from shelves.",
                "impact": "Planogram integrity and vendor compliance",
            })

        if report.total_price_mismatches > 0:
            recs.append({
                "priority": "MEDIUM",
                "category": "Pricing",
                "message": f"Fix {report.total_price_mismatches} price tag mismatches.",
                "impact": "Customer trust and regulatory compliance",
            })

        # Worst aisle recommendation
        aisle_scores = self.get_aisle_scores(report)
        if aisle_scores and aisle_scores[0]["score"] < 70:
            worst = aisle_scores[0]
            recs.append({
                "priority": "HIGH",
                "category": "Focus Area",
                "message": f"{worst['aisle_name']} needs immediate attention (score: {worst['score']}%).",
                "impact": f"{worst['violations']} violations across {worst['shelves']} shelves",
            })

        return recs

    def simulate_trend_data(self, store_id: str, days: int = 30) -> list:
        """Generate simulated compliance trend data for dashboard."""
        np.random.seed(hash(store_id) % 2**31)
        base_score = np.random.uniform(70, 85)
        trend = []

        for d in range(days):
            date = datetime.now() - timedelta(days=days - d)
            # Gradual improvement trend with daily noise
            score = base_score + (d / days) * 10 + np.random.normal(0, 3)
            score = min(100, max(50, score))
            trend.append({
                "date": date.strftime("%Y-%m-%d"),
                "compliance_score": round(score, 1),
                "misplaced": max(0, int(np.random.poisson(3 - d / days * 2))),
                "missing": max(0, int(np.random.poisson(5 - d / days * 3))),
                "unauthorized": max(0, int(np.random.poisson(1))),
            })

        return trend

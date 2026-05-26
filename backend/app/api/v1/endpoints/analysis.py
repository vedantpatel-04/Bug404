"""
CV Analysis endpoint — triggers shelf analysis pipeline.
"""
import sys
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends

from backend.app.core.security import TokenPayload, get_current_user, require_role, UserRole
from backend.app.schemas.schemas import AnalysisRunRequest, AnalysisRunResponse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent))

router = APIRouter()


@router.post("/run", response_model=AnalysisRunResponse)
async def run_analysis(
    body: AnalysisRunRequest,
    user: TokenPayload = Depends(require_role(UserRole.STORE_MANAGER)),
):
    """
    Queue a CV pipeline analysis job.

    Wraps ShelfAnalysisPipeline.analyze_image/analyze_store.
    In production, this would be dispatched to a Celery GPU worker.
    For now, runs synchronously.
    """
    job_id = str(uuid.uuid4())

    try:
        from pipeline.shelf_analysis_pipeline import ShelfAnalysisPipeline

        pipeline = ShelfAnalysisPipeline()

        if body.image_path:
            result = pipeline.analyze_image(
                image_path=body.image_path,
                store_id=body.store_id,
                aisle_id=body.aisle_id or "A01",
            )
            pipeline.save_results(result)
            msg = f"Analysis complete: {result.num_detections} detections, health {result.shelf_health_score}%"
        else:
            results = pipeline.analyze_store(body.store_id)
            for r in results:
                pipeline.save_results(r)
            msg = f"Store analysis complete: {len(results)} cameras processed"

        return AnalysisRunResponse(job_id=job_id, status="completed", message=msg)

    except Exception as e:
        return AnalysisRunResponse(
            job_id=job_id,
            status="error",
            message=f"Analysis failed: {str(e)}",
        )

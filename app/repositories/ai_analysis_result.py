from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_analysis_result import AIAnalysisResult


async def create_ai_analysis_result(db: AsyncSession, **kwargs) -> AIAnalysisResult:
    result = AIAnalysisResult(**kwargs)
    db.add(result)
    await db.commit()
    await db.refresh(result)
    return result


async def get_ai_analysis_result_by_record_and_model(
    db: AsyncSession, record_id: int, ai_model: str
) -> AIAnalysisResult | None:
    stmt = select(AIAnalysisResult).where(
        AIAnalysisResult.record_id == record_id, AIAnalysisResult.ai_model == ai_model
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def list_ai_analysis_results_by_record(
    db: AsyncSession, record_id: int
) -> list[AIAnalysisResult]:
    stmt = (
        select(AIAnalysisResult)
        .where(AIAnalysisResult.record_id == record_id)
        .order_by(AIAnalysisResult.created_at.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())

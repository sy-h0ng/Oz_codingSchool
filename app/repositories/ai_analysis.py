from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_analysis_result import AIAnalysisResult


async def get_analysis_by_record_and_model(
    db: AsyncSession, record_id: int, ai_model: str
) -> AIAnalysisResult | None:
    result = await db.execute(
        select(AIAnalysisResult).where(
            AIAnalysisResult.record_id == record_id,
            AIAnalysisResult.ai_model == ai_model,
        )
    )
    return result.scalar_one_or_none()


async def create_analysis(db: AsyncSession, **kwargs) -> AIAnalysisResult:
    analysis = AIAnalysisResult(**kwargs)
    db.add(analysis)
    await db.commit()
    await db.refresh(analysis)
    return analysis


async def list_analyses_by_record(db: AsyncSession, record_id: int) -> list[AIAnalysisResult]:
    result = await db.execute(
        select(AIAnalysisResult)
        .where(AIAnalysisResult.record_id == record_id)
        .order_by(AIAnalysisResult.created_at.desc())
    )
    return list(result.scalars().all())

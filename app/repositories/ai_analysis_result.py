from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_analysis_result import AIAnalysisResult


async def get_result_by_record_and_model(
    db: AsyncSession, record_id: int, ai_model: str
) -> AIAnalysisResult | None:
    result = await db.execute(
        select(AIAnalysisResult).where(
            AIAnalysisResult.record_id == record_id,
            AIAnalysisResult.ai_model == ai_model,
        )
    )
    return result.scalar_one_or_none()


async def create_result(
    db: AsyncSession,
    *,
    record_id: int,
    is_pneumonia: bool,
    confidence: Decimal,
    ai_model: str,
    heatmap_url: str | None = None,
) -> AIAnalysisResult:
    analysis_result = AIAnalysisResult(
        record_id=record_id,
        is_pneumonia=is_pneumonia,
        confidence=confidence,
        ai_model=ai_model,
        heatmap_url=heatmap_url,
    )
    db.add(analysis_result)
    await db.commit()
    await db.refresh(analysis_result)
    return analysis_result


async def list_results_by_record_id(
    db: AsyncSession, record_id: int
) -> list[AIAnalysisResult]:
    result = await db.execute(
        select(AIAnalysisResult)
        .where(AIAnalysisResult.record_id == record_id)
        .order_by(AIAnalysisResult.id.desc())
    )
    return list(result.scalars().all())

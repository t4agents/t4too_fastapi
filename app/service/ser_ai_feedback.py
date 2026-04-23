from uuid import UUID

from app.db.models.ai.ai_feedback_event import FeedbackEventDB
from app.schemas.sch_ai_feedback import FeedbackCreateRequest
from app.schemas.sch_ai import JWType

from sqlalchemy.ext.asyncio import AsyncSession


def _parse_uuid(value: str | None) -> UUID | None:
    if not value:
        return None
    try:
        return UUID(str(value))
    except (TypeError, ValueError):
        return None


async def log_feedback_event(payload: FeedbackCreateRequest, zjwt: JWType, db: AsyncSession) -> None:
    session_id = _parse_uuid(payload.session_id)
    message_id = _parse_uuid(payload.message_id)

    meta = payload.meta or {}
    if payload.session_id and session_id is None:
        meta = {**meta, "client_session_id": payload.session_id}
    if payload.message_id and message_id is None:
        meta = {**meta, "client_message_id": payload.message_id}

    db.add(
        FeedbackEventDB(
            ten_id=zjwt.ztid,
            biz_id=zjwt.zbid,
            user_id=zjwt.zuid,
            session_id=session_id,
            message_id=message_id,
            route=payload.route,
            model=payload.model,
            feedback_type=payload.feedback_type,
            rating=payload.rating,
            reason=payload.reason,
            comment=payload.comment,
            context=payload.context,
            meta=meta,
        )
    )
    await db.flush()

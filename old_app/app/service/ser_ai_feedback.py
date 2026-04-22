from uuid import UUID

from app.core.dependency_injection import ZMeDataClass
from app.db.models.ai_feedback_event import FeedbackEventDB
from app.schemas.sch_ai_feedback import FeedbackCreateRequest


def _parse_uuid(value: str | None) -> UUID | None:
    if not value:
        return None
    try:
        return UUID(str(value))
    except (TypeError, ValueError):
        return None


async def log_feedback_event(payload: FeedbackCreateRequest, zme: ZMeDataClass) -> None:
    session_id = _parse_uuid(payload.session_id)
    message_id = _parse_uuid(payload.message_id)

    meta = payload.meta or {}
    if payload.session_id and session_id is None:
        meta = {**meta, "client_session_id": payload.session_id}
    if payload.message_id and message_id is None:
        meta = {**meta, "client_message_id": payload.message_id}

    zme.zdb.add(
        FeedbackEventDB(
            ten_id=zme.ztid,
            biz_id=zme.zbid,
            user_id=zme.zuid,
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
    await zme.zdb.flush()

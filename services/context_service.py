"""Persistence operations for per-discussion context selections."""
import os
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import Activity, Artifact, ChatContext, ChatContextItem

MAX_ACTIVITIES = int(os.environ.get('MAX_ACTIVITIES', '200'))
MAX_ARTIFACTS = int(os.environ.get('MAX_ARTIFACTS', '50'))
MAX_TOKENS_CONTEXT = int(os.environ.get('MAX_TOKENS_CONTEXT', '60000'))
DISCUSSION_NOT_FOUND = 'Discussion not found'


def get_selection(db: Session, discussion_id: str, user_id: int) -> dict:
    context = db.scalar(select(ChatContext).where(
        ChatContext.discussion_id == discussion_id, ChatContext.user_id == user_id
    ))
    if context is None:
        raise HTTPException(status_code=404, detail=DISCUSSION_NOT_FOUND)
    items = db.execute(select(ChatContextItem.item_type, ChatContextItem.item_id).where(
        ChatContextItem.discussion_id == discussion_id
    )).all()
    return {
        'discussion_id': discussion_id,
        'context_version': context.context_version,
        'activities': [item_id for item_type, item_id in items if item_type == 'activity'],
        'artifacts': [item_id for item_type, item_id in items if item_type == 'artifact'],
    }


def toggle_item(db: Session, discussion_id: str, user_id: int, item_type: str,
                item_id: int, selected: bool) -> dict:
    if item_type not in {'activity', 'artifact'}:
        raise HTTPException(status_code=422, detail='item_type must be activity or artifact')
    model = Activity if item_type == 'activity' else Artifact
    try:
        owned = db.scalar(select(model.id).where(model.id == item_id, model.user_id == user_id))
        if owned is None:
            raise HTTPException(status_code=404, detail='Item not found')

        context = db.scalar(select(ChatContext).where(ChatContext.discussion_id == discussion_id))
        if context is None:
            if not selected:
                raise HTTPException(status_code=404, detail=DISCUSSION_NOT_FOUND)
            context = ChatContext(discussion_id=discussion_id, user_id=user_id, context_version=0)
            db.add(context)
            db.flush()
        elif context.user_id != user_id:
            raise HTTPException(status_code=404, detail=DISCUSSION_NOT_FOUND)

        context = db.scalar(select(ChatContext).where(
            ChatContext.discussion_id == discussion_id
        ).with_for_update())
        existing = db.get(ChatContextItem, (discussion_id, item_type, item_id))
        changed = False
        if selected and existing is None:
            limit = MAX_ACTIVITIES if item_type == 'activity' else MAX_ARTIFACTS
            count = db.scalar(select(func.count()).select_from(ChatContextItem).where(
                ChatContextItem.discussion_id == discussion_id,
                ChatContextItem.item_type == item_type,
            ));
            if count >= limit:
                raise HTTPException(status_code=422, detail=f'Limite {item_type} atteinte ({limit})')
            db.add(ChatContextItem(discussion_id=discussion_id, item_type=item_type, item_id=item_id))
            changed = True
        elif not selected and existing is not None:
            db.delete(existing)
            changed = True

        if changed:
            context.context_version += 1
            context.updated_at = datetime.now(timezone.utc)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return get_selection(db, discussion_id, user_id)

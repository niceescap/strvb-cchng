"""Build the read-only, per-discussion payload for downstream context consumers."""
import json
import os
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import Activity, Artifact, ChatContext, ChatContextItem, User
from services.context_service import DISCUSSION_NOT_FOUND

MAX_TOKENS_CONTEXT = int(os.environ.get('MAX_TOKENS_CONTEXT', '60000'))

# Compact summary schema versions. Extend this map when compact_json gains a version.
LEGENDE = {
    1: {
        'fv': 'version du format compact',
        'd': 'date UTC (YYYY-MM-DD)',
        't': 'durée chronométrée active en minutes',
        'mv': 'durée en mouvement en minutes',
        'pz': 'pauses en minutes',
        'kg': 'poids utilisé pour le calcul en kg',
        'km': 'distance en kilomètres',
        'dp': 'dénivelé positif en mètres',
        'v': 'vitesse moyenne en km/h',
        'w': 'puissance [moyenne, normalisée, maximale] en watts',
        'ftp': 'FTP en watts',
        'if': 'facteur d’intensité',
        'tss': 'Training Stress Score',
        'zp': 'durée dans les zones de puissance Z1 à Z7, en minutes',
        'cad': 'cadence moyenne hors zéros, en rpm',
        'hr': 'fréquence cardiaque [moyenne, maximale] en bpm',
        'zh': 'durée dans les zones cardiaques Z1 à Z5, en minutes',
        'cur': 'curseur cardio de 0 à 1',
        'ef': 'efforts intenses détectés',
        'tl': 'séries temporelles compactes (pas, puissance, fréquence cardiaque)',
        'dec': 'dérive puissance/fréquence cardiaque en pourcentage',
    }
}


def _utc_date(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).strftime('%Y-%m-%d')


def build_context(db: Session, discussion_id: str, user_id: int) -> dict:
    context = db.scalar(select(ChatContext).where(
        ChatContext.discussion_id == discussion_id,
        ChatContext.user_id == user_id,
    ))
    if context is None:
        raise HTTPException(status_code=404, detail=DISCUSSION_NOT_FOUND)

    athlete_row = db.execute(select(
        User.ftp_watts, User.weight_kg, User.max_heartrate
    ).where(User.id == user_id)).one()
    athlete = {
        'ftp_watts': athlete_row.ftp_watts,
        'weight_kg': float(athlete_row.weight_kg) if athlete_row.weight_kg is not None else None,
        'max_heartrate': athlete_row.max_heartrate,
    }

    activity_rows = db.execute(
        select(Activity).join(
            ChatContextItem,
            (ChatContextItem.item_id == Activity.id)
            & (ChatContextItem.discussion_id == discussion_id)
            & (ChatContextItem.item_type == 'activity'),
        ).where(Activity.user_id == user_id).order_by(Activity.occurred_at, Activity.id)
    ).scalars().all()
    activities = []
    for activity in activity_rows:
        resume = activity.compact_json
        missing = resume is None
        if isinstance(resume, dict) and resume.get('fv') not in LEGENDE:
            resume = {**resume, 'version_inconnue': True}
        record = {
            'id': activity.id,
            'date': _utc_date(activity.occurred_at),
            'sport': activity.sport,
            'titre': activity.title,
            'resume': resume,
        }
        if missing:
            record['resume_manquant'] = True
        activities.append(record)

    artifact_rows = db.execute(
        select(Artifact).join(
            ChatContextItem,
            (ChatContextItem.item_id == Artifact.id)
            & (ChatContextItem.discussion_id == discussion_id)
            & (ChatContextItem.item_type == 'artifact'),
        ).where(Artifact.user_id == user_id).order_by(Artifact.id)
    ).scalars().all()
    artifacts = [{
        'id': artifact.id,
        'titre': artifact.title,
        'categorie': artifact.category,
        'contenu': artifact.markdown,
    } for artifact in artifact_rows]

    payload = {
        'discussion_id': discussion_id,
        'context_version': context.context_version,
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'athlete': athlete,
        'legende': LEGENDE,
        'activities': activities,
        'artifacts': artifacts,
    }
    estimated_tokens = len(json.dumps(payload, ensure_ascii=False)) // 4
    if estimated_tokens > MAX_TOKENS_CONTEXT:
        raise HTTPException(status_code=422, detail=(
            f'Contexte trop volumineux : estimation {estimated_tokens} tokens, '
            f'limite {MAX_TOKENS_CONTEXT}'
        ))
    return payload

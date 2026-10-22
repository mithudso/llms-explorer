"""Shared statement identity and optional temporal applicability contract.

Absent or null dates mean unknown. valid_to is exclusive. recorded_at is the
researcher's observation time, never a substitute for source fetch or verification.
"""
import re
from datetime import UTC, date, datetime


def _instant(value, *, timestamp=False):
    if not isinstance(value, str):
        raise ValueError('temporal dates must be ISO strings or null')  # noqa: TRY004
    try:
        if not timestamp and re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
            return datetime.combine(date.fromisoformat(value), datetime.min.time(), UTC)
        if not re.match(r'^\d{4}-\d{2}-\d{2}T', value):
            raise ValueError('timestamp needs an ISO date and T separator')
        result = datetime.fromisoformat(value)
        if result.tzinfo is None:
            raise ValueError('timestamp needs a timezone')
        return result.astimezone(UTC)
    except ValueError as error:
        raise ValueError('temporal dates require YYYY-MM-DD or a timestamp with timezone') from error


def validate_temporal(value):
    if value is None:
        return
    allowed = {'valid_from', 'valid_to', 'recorded_at', 'applicability_version'}
    if not isinstance(value, dict) or set(value) - allowed:
        raise ValueError('temporal must contain only applicability dates, version and recorded_at')
    dates = {k: _instant(v, timestamp=k == 'recorded_at') for k, v in value.items()
             if k != 'applicability_version' and v is not None}
    if ('valid_from' in dates and 'valid_to' in dates
            and dates['valid_from'] >= dates['valid_to']):
        raise ValueError('temporal valid_to must be after valid_from (exclusive)')
    version = value.get('applicability_version')
    if version is not None and (not isinstance(version, str) or not version.strip()):
        raise ValueError('temporal applicability_version must be a nonempty string or null')


def claim_identity(slug, claim):
    identity = {'concept_slug': slug, 'text': claim['text'], 'sources': sorted(set(claim['sources'])),
                'confidence': claim['confidence'], 'verified_as_of': claim.get('verified_as_of'),
                'volatile': bool(claim.get('volatile'))}
    if 'temporal' in claim:
        validate_temporal(claim['temporal'])
        identity['temporal'] = claim['temporal']
    return identity

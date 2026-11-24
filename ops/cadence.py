"""Reads ops/cadence.json (Mohammad, 23 Nov 2026). Every reader of spacing, gaps, the buffer and the ahead alert uses
this; the defaults below apply only when the file cannot be read, and say so."""
import datetime as _dt
import json as _json
import os as _os

PATH = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), 'cadence.json')
DEFAULTS = {'timezone_offset_h': 4, 'day_spacing_min': 30, 'night_spacing_min': 60, 'night_start': '00:00',
            'night_end': '08:00', 'day_max_gap_min': 60, 'night_max_gap_min': 120, 'buffer_target': 6,
            'ahead_alert_min': 2, 'lead_min': 15, 'quick_spacing_min': 10, 'reel_after_quick_h': 2, 'reel_xt_max_h': 24}


def load(path=None):
    try:
        with open(path or PATH, encoding='utf-8') as f:
            d = _json.load(f)
        return {**DEFAULTS, **{k: v for k, v in d.items() if k in DEFAULTS}}
    except (OSError, ValueError):
        return dict(DEFAULTS, _missing=True)


C = load()
SPACING = {'day': int(C['day_spacing_min']), 'night': int(C['night_spacing_min'])}
MAX_GAP = {'day': int(C['day_max_gap_min']), 'night': int(C['night_max_gap_min'])}
BUFFER = int(C['buffer_target'])
AHEAD_MIN = int(C['ahead_alert_min'])
LEAD_MIN = int(C['lead_min'])
QUICK_SPACING = int(C['quick_spacing_min'])      # quick posts among themselves (24 Nov 2026), apart from the Reel spacing
REEL_AFTER_QUICK_H = float(C['reel_after_quick_h'])
REEL_XT_MAX_H = float(C['reel_xt_max_h'])


def is_quick(labels):
    """A quick post (label kind:quick): left out of the Reel spacing, the Reel buffer and the ahead alert."""
    return 'kind:quick' in set(labels or ())
TZ = _dt.timezone(_dt.timedelta(hours=float(C['timezone_offset_h'])))


def _mins(hhmm):
    h, m = str(hhmm).split(':')
    return int(h) * 60 + int(m)


def band(x):
    """'night' or 'day' for a UTC (or aware) time, by the Dubai clock and the file's night window."""
    if x.tzinfo is None:
        x = x.replace(tzinfo=_dt.timezone.utc)
    d = x.astimezone(TZ)
    m, a, b = d.hour * 60 + d.minute, _mins(C['night_start']), _mins(C['night_end'])
    inside = a <= m < b if a <= b else (m >= a or m < b)
    return 'night' if inside else 'day'

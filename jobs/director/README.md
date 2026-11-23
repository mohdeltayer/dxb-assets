# Director verdicts (Mohammad, 23 Nov 2026)

The Director writes one plain file per Reel here, `jobs/director/<job name>.json`, and commits it. Nothing else: no
command records an approval. The server's publish step (`templates/serverpost.py`, `server-post.yml`) reads it.

```json
{"story": "2026-11-23-<slug>", "out": "cards/2026-11/<slug>-reel-v1.mp4", "verdict": "pass",
 "reasons": ["text true against the primary", "clear to an Arab reader", "no graphic content"],
 "at": "2026-11-23T09:10:00Z", "by": "director-p2"}
```

A fix: `"verdict": "fix"`, `"reason"` (wrong_subject, framing, overlap, unreadable_text move the Reel to the 16:9 showcase
layout; factual_error, unclear_text, graphic need `"job_patch"` with the corrected job fields, or the Reel is held),
`"fix"` (the one fix, one line). The server renders once more and schedules the new Reel. No file 20 minutes after the
render: the server schedules anyway and notes "no director verdict". Check a file: `python3 templates/serverpost.py check <file>`.

# Reel views by template (advisor, 14 Oct 2026)

Weekly Instagram views are recorded next to each Reel's template in the format
ledger (`templates/assets/format-ledger.json`), so the Tuesday audit can say
which templates reach and which do not.

Routine: Mohammad sends the Instagram views per Reel on Tuesday morning before
the audit (the Reels tab, or the insights screenshots). For each Reel:

    python3 templates/formats.py views <reel name> <views>
    python3 templates/formats.py templates      # median views per template

`formats.py` alone lists the last ten Reels with their views. A re-render keeps
its views. Append each Tuesday's per-template table below with the date, and
read it with the caveats: a Reel's views keep growing for about a week, so
compare Reels of the same age; one 14K outlier (the Hollow Knight bundle) moves
a template's mean, which is why the median is shown.

## Tables

(none yet; the first Tuesday is 20 Oct 2026)

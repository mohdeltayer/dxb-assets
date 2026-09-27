# Digital Lounge house glossary

Used with the `arabic-games-film-editor` skill. Explicit decisions by
Mohammad override the skill's defaults. A term is "approved" only when he
has said so; everything else is a working suggestion.

## House rules that override the skill

| Topic | House rule | Status |
|---|---|---|
| Game, series, character, platform names | English only, as the publisher writes them | Approved 26 Sep 2026 |
| Company, studio, outlet, people names | Arabic, then the English in brackets at first mention; Arabic alone after | Approved 26 Sep 2026 (the skill's default of English-only does not apply) |
| Voice | Outlet voice, no first person. His own play time is credited: "انطباعات محرر ديجيتال لاونج" | Approved 26 Sep 2026 |
| Nintendo | نينتيندو (Nintendo), his spelling, also in نينتيندو لايف (Nintendo Life) | Approved 26 Sep 2026 |
| HANDS ON chip | نظرة أولى (fallback انطباعات; not تجربة, which reads as a test) | Approved 26 Sep 2026 |

## Terms

| English | Arabic | Context / excluded meanings | Status |
|---|---|---|---|
| Docked (Switch) | وضع التلفاز | not وضع الإرساء, not "التوصيل بالقاعدة" (DeepL's literal) | Suggested 27 Sep 2026 |
| Handheld mode | الوضع المحمول | | Suggested 27 Sep 2026 |
| Locked 30fps | معدل ثابت يبلغ 30 إطارًا في الثانية | only when the source measured stability | Suggested 27 Sep 2026 |
| Upscaled from X to Y | مُرقّاة من X | keep which number is internal and which is output | Suggested 27 Sep 2026 |
| Dungeons (Fire Emblem: Fortune's Weave) | الزنزانات | RPG dungeon areas, not a prison | Unresolved, ask |
| A bit disappointing | مخيّب للآمال بعض الشيء | never intensify | Suggested 27 Sep 2026 |

## Tools

1. `arabic-games-film-editor` skill (this repo, `.claude/skills/`), writes.
1b. `arabic-writing` skill (same folder), checks: grammar, spelling, smell test.
2. DeepL (connector, Free plan), the alternative when needed: translation only.
   Its Write/rephrase and correct tools do not support Arabic, and context,
   custom instructions and glossaries need DeepL Pro. Its raw output needs the
   house rules applied after (it left "Digital Lounge" in Latin and rendered
   "docked" literally).
3. Jais Chat (jaischat.ai, G42/Inception), used by Mohammad by hand with the
   house prompt when he wants a second Arabic read.

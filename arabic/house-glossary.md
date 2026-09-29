# Digital Lounge house glossary

Used with the `arabic-games-film-editor` skill. Explicit decisions by
Mohammad override the skill's defaults. A term is "approved" only when he
has said so; everything else is a working suggestion.

## House rules that override the skill

| Topic | House rule | Status |
|---|---|---|
| Game, series, character, platform names | English only, as the publisher writes them | Approved 26 Sep 2026 |
| Company, studio, outlet, people names | Arabic, then the English in brackets at first mention; Arabic alone after | Approved 26 Sep 2026 (the skill's default of English-only does not apply) |
| Voice | Outlet voice, no first person. His play time runs uncredited as the account's own: "انطباعات أولية بعد 10 ساعات مع …" (no "محرر ديجيتال لاونج": readers are already on the account) | Approved 27 Sep 2026 |
| Nintendo | نينتيندو (Nintendo), his spelling, also in نينتيندو لايف (Nintendo Life) | Approved 26 Sep 2026 |
| Game and series names as subjects | Feminine agreement, because the unstated noun is لعبة or سلسلة: ستحصل Minecraft, تواصل Control Resonant (not يحصل Minecraft) | Approved 27 Sep 2026 |
| Bandai Namco | بانداي نامكو (Bandai Namco); never باندا نامكو, which reads as "Panda Namco" | Approved 27 Sep 2026 |
| HANDS ON chip | نظرة أولى (fallback انطباعات; not تجربة, which reads as a test) | Approved 26 Sep 2026 |
| Text direction | Every post, paragraph and line starts with an Arabic word, so X and Instagram set it right to left: تصل DYNASTY WARRIORS 3، not DYNASTY WARRIORS 3 تصل. A paragraph that opens on an English name (or a digit before one) can register as English and align left. Hashtag lines lead with the Arabic tags: #ألعاب #أخبار_الألعاب #DynastyWarriors | Approved 27 Sep 2026 |

## Terms

| English | Arabic | Context / excluded meanings | Status |
|---|---|---|---|
| Docked (Switch) | وضع التلفاز | not وضع الإرساء, not "التوصيل بالقاعدة" (DeepL's literal) | Suggested 27 Sep 2026 |
| Handheld mode | الوضع المحمول | | Suggested 27 Sep 2026 |
| Locked 30fps | معدل ثابت يبلغ 30 إطارًا في الثانية | only when the source measured stability | Suggested 27 Sep 2026 |
| Upscaled from X to Y | مُرقّاة من X | keep which number is internal and which is output | Suggested 27 Sep 2026 |
| Dungeons (Fire Emblem: Fortune's Weave) | مناطق الاستكشاف | not الزنزانات (reads as prison cells) | Approved 27 Sep 2026 |
| N hours with a game | بعد 10 ساعات من <game> (من, not مع); the skill's own example is بعد عشر ساعات من اللعب | Approved 27 Sep 2026 |
| A bit disappointing | مخيّب للآمال بعض الشيء | never intensify | Suggested 27 Sep 2026 |
| Expansion (DLC) | إضافة، والمثنى الإضافتان (وتضم الإضافتين Hearts of Stone وBlood and Wine) | not توسعة or توسيع | Approved 27 Sep 2026 |
| Steam store in a country | متجر Steam في الإمارات، متجر Steam في السعودية | not متجر Steam الإمارات (a construct with a Latin word in the middle reads broken) | Suggested 29 Sep 2026 |
| Nintendo Everything | نينتيندو إفريثينغ (Nintendo Everything) | follows the house spelling of نينتيندو; on 29 Sep it went out as نينتندو | Suggested 29 Sep 2026 |
| Instead of (price was X) | بدلًا من | not bare بدل in formal copy | Suggested 29 Sep 2026 |
| Shaping up to be | يبدو في طريقه ليكون | not تتشكل لتكون (a calque) | Suggested 29 Sep 2026 |
| Service ends (online game) | تنتهي خدمة <game>، تُوقف <company> خدمة <game> | not تتوقف <game> alone, which DeepL read back as "taking a break" | Suggested 29 Sep 2026 |
| N years after launch | بعد مرور سبع سنوات على إطلاقها | not بعد سبع سنوات من إطلاقها; and not لتتوقف بعد…, which reads as "only to be" | Suggested 29 Sep 2026 |
| Update or game released today | تطرح <company> اليوم تحديثًا…، or once it is live: أصبح … متوفرًا الآن (chip متوفر الآن) | not يصل اليوم, which reads as a physical delivery | Approved 29 Sep 2026 |

## Tools

1. `arabic-games-film-editor` skill (this repo, `.claude/skills/`), writes.
1b. `arabic-writing` skill (same folder), checks: grammar, spelling, smell test.
2. DeepL (connector, Free plan), the alternative when needed: translation only.
   Its Write/rephrase and correct tools do not support Arabic, and context,
   custom instructions and glossaries need DeepL Pro. Its raw output needs the
   house rules applied after (it left "Digital Lounge" in Latin and rendered
   "docked" literally).
2b. DeepL back-translation (Arabic to English) is the cross-check that the
    meaning survived: compare it with the English source before queuing.
3. Jais Chat (jaischat.ai, G42/Inception), used by Mohammad by hand with the
   house prompt when he wants a second Arabic read.

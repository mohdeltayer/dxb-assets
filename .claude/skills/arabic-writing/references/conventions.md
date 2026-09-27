# Conventions: names, transliteration, numerals, dates, units, bidi

Table of contents:
1. Transliterating foreign names (النقحرة)
2. Brand and product names
3. Technical terms
4. Numerals
5. Dates and month names (regional!)
6. Percent, currency, units
7. Bidirectional (RTL/LTR) text mechanics

---

## 1. Transliterating foreign names (النقحرة)

Arabic romanization is **transcription by sound**, not letter-mapping. Arabic lacks /p/, /v/,
hard /g/, and /tʃ/:

- **MSA assimilation** (formal/news/most UI): p → ب (باريس), v → ف (فيديو), g → ج / غ / ق
  (Google → جوجل / قوقل), ch → تش (تشرشل).
- **Extended letters** (branding, dialect, precision): پ = p, ڤ = v, گ = hard g, چ = ch.

Rules:
- **Consistency is paramount** — spell a given name the same way every time in a document.
- Give the **Latin original in parentheses on first mention** of a non-standard transliteration.
- Don't insert long vowels that aren't in the source (a common error: تووني for Tony).
- A taa marbuta in transliteration → -a (or -at in an iḍāfa).

## 2. Brand and product names

- In **UI and documentation**, keep trademarks in **Latin** and do not inflect them or add ال
  (Windows، HTML، iPhone). Microsoft's guidance: trademarks aren't localized and take no article.
- In **consumer marketing**, transliteration dominates (Coca-Cola → كوكا كولا، McDonald's →
  ماكدونالدز). Pick one registered form and keep it.
- Use one rendering per name throughout; never alternate.

## 3. Technical terms

Decide by audience among **transliterate / coin / use common usage**:
- Settled: إنترنت (universal)، تطبيق ("app")، بريد إلكتروني (formal) vs إيميل (colloquial)،
  حاسوب (formal/Levant) vs كمبيوتر (Gulf/Egypt).
- Acronyms are usually **spelled out** in Arabic (RAM → ذاكرة الوصول العشوائي), with the English
  kept only when space-constrained or when the acronym itself is the brand.
- Never mix two renderings of the same term in one product.

## 4. Numerals

Two glyph sets, identical math:
- **Arabic-Indic** ٠١٢٣٤٥٦٧٨٩ — Mashreq + Gulf (Egypt, Saudi, Iraq, Levant).
- **Western** 0123456789 — Maghreb, UAE, and most global/technical contexts.

- Numbers always run **left-to-right even inside RTL text**.
- The localization default has **shifted toward Western digits** (Unicode CLDR now defaults bare
  `ar` to ASCII digits). Use locale extensions (`ar-EG-u-nu-arab` vs `…-latn`) for control.
- A common editorial rule: write out **0, 1, 2** rather than as digits (لا يوجد طلاب / طالب واحد
  / طالبان), and use figures for larger numbers.
- Pick **one numeral system per document** and stay consistent.

## 5. Dates and month names (regional!)

- Format is **DD/MM/YYYY**. Gregorian is the digital default; Hijri (هـ) is used for
  religious/official dates, often dual-displayed in the Gulf.
- **The biggest gotcha is month names**, which diverge by region:
  - **Mashreq transliteration** (Egypt, Gulf, pan-Arab media): يناير، فبراير، مارس، أبريل، مايو…
  - **Levant** (Aramaic-derived): **كانون الثاني = January**, شباط = February, آذار = March,
    نيسان = April, أيار = May… (كانون الأول = December).
  - **Maghreb** (French-derived): جانفي، فيفري، مارس، أفريل…
- So كانون الثاني is **January**, not December. Let the target locale drive month names; when
  unsure, the transliterated set (يناير…) is the safest pan-Arab choice.

## 6. Percent, currency, units

- Percent sign goes to the **left** of the number, no space: 50% (✓), % 50 (✗). With
  Arabic-Indic digits: ٪١٢.
- The **currency symbol** is treated as part of the number (placed to the left); the currency
  **name** follows the figure: ١٠٠ دولار، 100 ريال.
- With Arabic-Indic digits use the Arabic decimal separator ٫ (U+066B) and thousands ٬ (U+066C).
- Degree sign goes to the **right**: 37.5° م.
- Use a **non-breaking space** between a unit/version and its number.

## 7. Bidirectional (RTL/LTR) text mechanics

- Latin runs, brand names, numbers, URLs, phone numbers, and code are **LTR "islands"** inside
  RTL text. The Unicode Bidi Algorithm handles most cases automatically.
- **Isolate** ambiguous runs with U+2066…U+2069 (or LRE…PDF) so adjacent punctuation doesn't
  flip.
- Copy-pasting numbers into CAT / editing tools can invert them — verify, or type manually.
- In CSS, use **logical properties** (margin-inline-start, etc.) rather than left/right.

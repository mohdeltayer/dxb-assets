# Register, naturalness & style

Table of contents:
1. Diglossia and the register ladder
2. Choosing a register by purpose and market
3. Connectors (أدوات الربط) — coordination over subordination
4. The حيث problem
5. Techniques for natural MSA
6. Tone and transcreation

---

## 1. Diglossia and the register ladder

Arabic is diglossic: a High variety (MSA / الفصحى) for writing and formal speech, and Low
varieties (the dialects / العامية) for everyday speech. **No one speaks MSA natively**, so the
chief register error is leaking dialect into formal text — or, conversely, writing stiff
classical Arabic where a lighter touch is wanted.

Badawi's five levels (a gradient, not a binary):
1. فصحى التراث — heritage classical (Qur'an, classical literature).
2. فصحى العصر — contemporary MSA (news, books, official text).
3. عامية المثقفين — **Educated Spoken Arabic ("white Arabic")**: a pan-regional, lightly
   colloquial middle ground that "sounds human" without committing to one dialect.
4. عامية المتنورين — everyday educated colloquial.
5. عامية الأميين — basilectal colloquial.

Levels 2 and 3 cover almost all practical writing.

## 2. Choosing a register by purpose and market

- **MSA (level 2):** legal, medical, academic, official, news, manuals, B2B documents,
  subtitles (e.g. Netflix mandates MSA, no dialect), and most UI body text.
- **Dialect or white Arabic (level 3):** ads, social posts, voiceover, chat, conversational
  UX, microcopy — or whenever the user names a market/dialect. Stiff MSA in consumer microcopy
  reads like "a consumer app writing in Shakespearean English."
- **Segment by market.** Don't ship one Arabic for 22 countries; pick the dialect of the target
  country and keep it consistent. See the dialect files.
- **Never mix:** one register and one dialect per piece.

## 3. Connectors (أدوات الربط) — coordination over subordination

**Central fact:** Arabic favors **coordination (parataxis)** where English favors
**subordination (hypotaxis)**. Arabic chains clauses with particles and freely opens sentences
and paragraphs with و / فـ. Translating English's nested subordinate clauses literally produces
heavy, un-Arabic sentences.

Precise senses (don't use و for everything, and don't over-explicitate):
- **و** — pure addition (no order, no cause).
- **فـ** — sequence / immediate result ("so, then").
- **ثم** — later sequence (a time gap).
- **لكن / لكنّ** — contrast.
- **بل** — correction after a negation ("rather").
- **حتى** — "even / until."
- **إذ** — causal-temporal "since / as" (and إذ إنّ with kasra).
- **إذن** — inference "therefore."
- **أمّا … فـ …** — a topic-shift frame ("as for X, …").
- Heavier transitions (بالإضافة إلى ذلك، علاوة على ذلك، من ناحية أخرى) are fine **occasionally**
  — but stacking them is the #1 translationese tell (see translationese.md).

Example — English subordinated → Arabic coordinated:
"After the minister arrived, he met the delegation, which had requested talks because of the
crisis." → وصل الوزيرُ فاستقبل الوفدَ، وكان الوفدُ قد طلب المباحثاتِ بسبب الأزمة.

EN→AR you may **join** short clauses; AR→EN you should **segment** long ones.

## 4. The حيث problem

حيث is properly a **locative** ("where / in which") and classically takes a **full clause**
(with the following noun nominative; and حيث إنّ with kasra). MT abuses it as a catch-all for
"where / whereby / whereas / because," often followed by a bare noun in the genitive. Fix by
choosing the precise connector:

- cause → إذ / لأنّ
- result "such that" → بحيث
- relative "which/who" → الذي / التي
- contrast → بينما
- reserve **حيث** for a genuine place or locus.

## 5. Techniques for natural MSA

1. **Cut filler preambles.** أريد أن أقول لك بأن المشروع قد انتهى الآن → انتهى المشروع.
2. **Prefer finite verbs / verbal sentences;** kill the قام بـ + maṣdar and تمّ + maṣdar
   over-nominalization: الحكومةُ قامت بإصدار قرار بشأن زيادة الأسعار → أصدرت الحكومةُ قرارًا
   برفع الأسعار.
3. **Vary connectors to mark real logic** (غير أنّ، نظرًا لأنّ، ومن ثَمّ) instead of stringing
   everything with و — but without over-explicitating.
4. **Prefer the active voice** (see translationese.md §2).
5. **Choose precise, evocative vocabulary** — Arabic is synonym-rich; the exact word reads
   better than a generic one.
6. **Vary sentence length** for rhythm; favor الإيجاز (concision) and avoid حشو (padding).
7. **Read aloud.** If it only parses by recalling the English, rewrite it.

## 6. Tone and transcreation

A sentence can be grammatically perfect yet "commercially dead." Blunt/aggressive English tone
reads as rude in Arabic, which values eloquence, subtlety, and community/respect framing over
individualist hard-sell. In formal and UI contexts, **soften bare imperatives** (من فضلك،
يُرجى). For marketing, **transcreate** — rewrite the idea for the culture rather than translate
the words (global brands re-express slogans, they don't calque them).

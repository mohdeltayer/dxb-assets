T0 (breaking): publish the minute it passes checks, never into a slot; chip عاجل, breaking treatment and music. A message from Mohammad starting with T0: is breaking by definition.

# Reel check (adv-20261102-reel-checklist with its addenda; adv-20261102-story-brief part 4)

Read this file, `newsroom/editorial-memory.md` (the entries of your story type) and `newsroom/names-ar.md` before any build.
Before any render, fill this list into the job file as `"reel_check"`: one entry per line, `yes` or `no`, and the
evidence (shot path, music file, crop decision, the Arabic text). No render with a `no`; T0 skips slots, not checks.
Enforcement in render_job.check and the pre-submit check is queued for the build desk; until then the director reads it.
Every editorial rule Mohammad gives is added here the same day, as one line.

## 1. SOURCE
- [ ] Primary read in full (publisher, platform, store, official account); its time and the first report anywhere noted.
- [ ] Not already posted (ledger find, Publer last 7 days); a repeat is an update with something new, or it is dropped.
- [ ] Older than 24 hours at the first report and nothing new since: dropped, unless regional news nobody covered.

## 2. ANGLE BEFORE LINES (written into the job before any line)
- [ ] hook: the one surprising thing · why now · what it means for players here · payoff.
- [ ] Every item the story type needs (section 3), each with its source.

## 3. STORY TYPE: what each must carry
- INTERVIEW: who said it and where; the two or three tidbits that are news, as short attributed quotes. Never only "an interview was published", never the whole interview.
- DELAY: old date, new date, the reason or «لم يُذكر سبب».
- OUT NOW: platforms, the AED price where listed, what it is in one line.
- NUMBERS: the figure, the period, the source, the comparison that gives it meaning.
- REVIEWS: outlet, its own scale (never converted), date, quote attribution, Metacritic and OpenCritic totals with the time read.
- TRAILER OR FIRST LOOK: what the footage shows that is new; the actual trailer, credited.
- PEOPLE: who, their role, the news about them; their official photo in the first 3 to 4 seconds.
- EVENT: when in Dubai time, where to watch.

## 4. STORY (the lines)
- [ ] One spoken paragraph first: hook, explanation, demonstration, consequence, payoff; then cut into beats.
- [ ] Subject named before any pronoun; no line opens on و unless it continues the line before.
- [ ] Release verbs: تصدر for a date, متوفرة الآن or صدرت اليوم, قادمة إلى or تصل إلى + platform, أُعلن عن; never a bare تصل.
- [ ] Every name matches `newsroom/names-ar.md`; a new one is added there. Every recurring term matches its Terms section; a term not on it is added with the wording used and flagged on the board for Mohammad.

## 5. WRITING THE POST (Arabic, our own rules)
- [ ] العنوان على الشاشة: ما حدث بأسماء يعرفها القارئ، فعل قوي، ورقم إن وُجد؛ لا سؤال إلا إن أجابت عنه القصة، ولا إثارة مضللة. مثال: «خوادم DARK SOULS II وDARK SOULS III متوقفة الآن على جميع المنصات».
- [ ] السطور: افتتاحية للقصة لا تكرار للعنوان، تبدأ بأقوى اقتباس أو رقم، ولها بداية واضحة ونهاية تفي بالوعد، وتُقرأ بصوت عالٍ بسهولة. مثال: قال سودا51 إن Travis Touchdown «سيعود بالتأكيد».
- [ ] الشرح (Instagram): السطر الأول يحمل الخبر وسبب أهميته للاعب، والمصدر مسمّى، وأفعال الإصدار صحيحة، ودعوة واحدة فقط حين تناسب. مثال: «إعلان Death Stranding Isolations الأول: أول نظرة على مسلسل الأنمي الذي يُعرض على ديزني بلس في 2027».
- [ ] نص X وThreads: جملة أو جملتان، الخبر وسبب أهميته، والرابط الرسمي على X؛ لا يُلصق الشرح كما هو.
- [ ] التعليق المثبت أو الأول: المصدر، وللمقابلات أين تُقرأ كاملة. مثال: «في مقابلة أجرتها فاميتسو (Famitsu)».
- [ ] الاستعجال: لا عاجل ولا تحديث إلا إذا كان صحيحًا؛ وما لم يُؤكد يُقال صراحة. مثال: «ولم يوضح الاستوديو طبيعة الخلل».
- [ ] النبرة: محايدة وبسيطة، بلا غضب ولا انحياز في نقاشات القراء. مثال: «وبدلًا من الاحتماء من الحر، يحتاج اللاعب إلى البحث عن الدفء» (Dune: Awakening).

## 6. SOUND
- [ ] Footage keeps its own sound, or series music, or our bed; music named by file in the job.
- [ ] No interview or narration speech under Arabic lines (it reads as a translation of them).
- [ ] Separated stems are a last resort: (1) a music-only stretch of the trailer; (2) series music or our bed, credited; (3) a separated music stem only if the artifact check passes. The decision log says which and why.
- [ ] Our effects only on our graphics, on the frame of the event; none over footage, no whoosh on cuts.

## 7. PICTURE
- [ ] Footage first: a trailer, reveal, update or gameplay story uses official footage. Stills with our bed only for sales, business, people, delays or outages, or when no footage is reachable: reason and sources tried in the job note.
- [ ] Every Reel shows the game: no text-card-only Reel; a notice or figure is a line or strip over the game.
- [ ] Not the same picture as any of the last 5 Reels (`picture:` written in the job note).
- [ ] One visual requirement per beat; the shot shows what its line says; the subject whole in frame.
- [ ] Crop judged per beat: when 9:16 cuts the subject, full frame with designed bands. Never a blurred fill of the same picture.
- [ ] Headline in the band, never over a face or the subject. No face in the footage behind an open photo box.
- [ ] Text moves only on entry and exit; footage holds steady (no drift, no pan over a still, no zoom under text).
- [ ] Credit on every clip that is not ours, for its whole duration; chip present; event badge when there is one.
- [ ] Lifeless score below threshold, once the check is live (report-only for its first 3 days).

## 8. CHECKS (before render, and the director again on the file)
- [ ] What am I seeing? What am I hearing? Why this cut here? Does the subject stay in frame? Does the music belong to this moment?
- [ ] Decision log complete: per beat the shot chosen and the alternatives, the crop decision, the music and why.

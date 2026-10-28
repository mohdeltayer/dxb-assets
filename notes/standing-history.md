# Standing history: retired platforms and publishing routes

Moved word for word out of CLAUDE.md when the operations desk's instructions were trimmed (adv-20261028-three-desks,
step 3). Not in force unless CLAUDE.md or Mohammad brings a part back.

<!-- moved from CLAUDE.md lines 253 to 448 (28 Oct 2026 version), word for word -->
@the_digilounge on X (display name DIGI-ديجي until 26 Sep, joined Jan 2024; 19
followers and 1,565 posts as of 24 Sep 2026). Connected to Postiz on
26 Sep 2026 as integration `cmuifxrd70mbdo80y235utthm` (DXB-KNIGHT is
`cmtk7cltp0030my0yj6glcyru`); check the id on every Arabic job.json.
Digital Lounge Instagram joined Postiz on 27 Sep 2026 as integration
`cmujo38ww12j3o80ygi3webqt` (Postiz name "The DIGI-Lounge"). Its job.json
takes `"platform": "instagram"` and `"settings": {"post_type": "post"}`
(or "story"); every post needs media, captions stop at 2200 characters.
`publish.py` needs no change for it.
Stories work with `"post_type": "story"` (a Reel fits as it is, the
safe zone clears the story bars; no caption shows). Not used by default
(Mohammad, 28 Sep 2026): post one only when he asks.
Digital Lounge TikTok (@the_digilounge) joined Postiz on 27 Sep 2026 as
integration `cmuk0rett044oo80y3ycfes66`, platform `tiktok-business` (Postiz
shows it as "Mohammed", the name TikTok had when it was connected; Postiz
keeps the name and picture from connect time, so reconnect after the
display name changes on 4 Oct). Its job.json takes `"platform":
"tiktok-business"` and settings `{"content_posting_method": "DIRECT_POST",
"privacy_level": "PUBLIC_TO_EVERYONE", "duet": true, "stitch": true,
"comment": true, "autoAddMusic": "no", "brand_content_toggle": false,
"brand_organic_toggle": false}` plus an optional `title` (90 characters).
UPLOAD only drops the video in the TikTok app inbox for him to finish by
hand. Every post needs media; captions stop at 2200 characters.
Hold lifted (Mohammad, 28 Sep 2026): the public profile shows the_digilounge
with the bio and play mark, which is fine until the name becomes
"ديجيتال لاونج | أخبار الألعاب" on 4 Oct (reminder set). Every Digital Lounge
story with a video goes to TikTok with the rest of Digital Lounge: same
Reel file, same time as its X, Instagram and YouTube posts, the Instagram
caption as text (Arabic hashtags first). Postiz still labels the channel
"Mohammed" until it is reconnected; that label is not seen by anyone.
TikTok on hold (Mohammad, 28 Sep 2026, 21:30 Dubai, for 48 hours):
every post after the first three sat at 0 views while the account check
showed no issues, and a phone upload did no better, so the account is
not being sent to For You after a burst of about nine posts on day one.
Until about 21:30 on 30 Sep no new TikTok jobs are drafted or queued
(posts already in Postiz stay). The first post back is posted from his
phone, built from our own graphics (a sales chart, not a trailer), with
a location and a headline cover; after that 1 to 3 TikToks a day, the
strongest stories only. This overrides "every Digital Lounge story
goes to TikTok" until he says otherwise.
Shorts format for TikTok and YouTube (Mohammad, 29 Sep 2026, after
every Short sat at 0 to 8 views): the Instagram Reel shrinks the clip to a
16:9 strip that reads as a slide on a full-screen feed, and reposted
trailers lose to the publisher's own upload. TikTok and YouTube therefore
take `templates/short.py`, not the `ig_ar` Reel: `clip()` puts the
footage at full 9:16 height with the chip and one big headline low in the
frame on a soft band behind the text only (not a shade over the lower half;
Mohammad, 29 Sep) and a small brand line; `chart()` opens on a question and the box
art, then the top 5 countdown; both end on a 1 second end card (the
outro's final frame). Original material first (our charts, his gameplay,
his voice), trailers last; one or two a day on these two. A 7-day test
from 30 Sep against the old baseline (2 to 8 views per Short); if nothing
moves, effort goes back to X and Instagram. X and Instagram keep their
cards.
Native upload test (Mohammad, 1 Oct 2026): both accounts check clean
(YouTube Studio shows no restrictions, TikTok "No outstanding issues"),
yet every API-posted Short sits at 0 to 18 views while the same stories
reach about 1,000 on Instagram. He deleted the API Zelda Short on both
and posted the same file from his phone at about 18:55 Dubai (TikTok
with in-app edits and filters, YouTube uploaded by hand); the Famitsu
chart Short at 19:15 went through Postiz as the control. Compare both
the next morning. No new automated TikTok or YouTube jobs until the
result is in. YouTube's channel verification (video selfie or ID) is
optional and his call; it was left until after this test.
TikTok and YouTube dropped (Mohammad, 1 Oct 2026, 21:00 Dubai): no
TikTok or YouTube posts at all, automated or for his phone, until the
cause of the zero views is found. This overrides every rule above that
sends Digital Lounge stories or Shorts to either platform. Digital Lounge
runs on X and Instagram only; reel.py files still render 9:16 so either
platform can come back without new work. Nothing was queued on either
when the drop started.
YouTube lane for original material (advisor trial, 17 Oct 2026, agreed with
Mohammad). The Famitsu 5 to 11 Oct Short, uploaded by him by hand, reached 140
views in 1 day 9 hours (the first of the last ten; the channel had 510 views in
28 days) where every earlier Short sat at 0 to 28; his hand upload of the Zelda
trailer on 1 Oct got 9. So the difference is the content (our own data and
graphics), perhaps helped by the account ageing since the 27 Sep burst. This
overrides the 1 Oct drop for original material only; TikTok stays dropped.
1. YouTube takes original material only: Famitsu weekly, numbers Reels, list
   pieces, the Gulf price roundup, retro and his handson. Trailer Reels never
   go to YouTube.
2. Every YouTube post is a YouTube cut under 35 seconds (Famitsu: top five plus
   hardware, not the full ten; the full Famitsu Reel held 24.7% average viewed).
   The title opens on an Arabic word, carries the game or the news word in its
   first five words, and passes the grammar stage (the Famitsu title wrote
   «الاسبوع» for «الأسبوع»).
3. Route test: the next two original pieces go to YouTube through Postiz
   (integration `cmuk20rj302oqpr0ygqzcdzch`, settings as above; Postiz has no
   category field, so Gaming comes from the channel's Studio defaults). If both
   are distributed like the Famitsu Short (views in the hundreds within 48
   hours), the lane runs through Postiz at one or two a day. If they stay near
   zero, the lane is manual: production prepares the cut, title and
   description, and Mohammad uploads from his phone.
4. Judged after two weeks against the 140-view baseline, in
   `newsroom/experiments.md`.
Preflight enforces it: a YouTube job.json carries `"original"` set to the kind
(famitsu, numbers, list, gulf_prices, retro, handson; publish.py does not send
it), a clip under 35 s, an Arabic-first title of 2 to 100 characters, `"type":
"public"` and `"selfDeclaredMadeForKids": "no"`.
TikTok photo-mode test (Mohammad, 3 Oct 2026, after TikTok showed a
"post photos to get more views" prompt): one swipe-through photo set built
from our own graphics, posted by hand from his phone, to see whether the
account gets any reach outside the video format. `templates/photos.py`
renders 1080x1920 slides: `famitsu_set(rows, hw, week, date, outdir)` gives
a question cover with the week's box art, entries 5 to 1 (art full bleed,
rank, title, this week and since launch), consoles, and an end slide.
Nothing goes to TikTok through Postiz; the 1 Oct drop otherwise stands.
It got 0 views by the morning of 4 Oct, so the account itself is not
being distributed. Plan (Mohammad, 4 Oct 2026): nothing on TikTok for two
weeks, then one original post from his phone (about 18 Oct); if that is 0
too, a fresh account posted from the phone only, never through the API.
History: an account he used about two years ago was labelled a bot and
barred from monetising but still reached people. That account seems gone:
in Sep 2026 TikTok made him register from scratch, so @the_digilounge is
effectively new and the old label is not the likely cause. More likely: a
brand-new account posting about nine videos on day one through a
third-party app (Postiz), most of them reposted publisher trailers, which
reads as automated, unoriginal content. The same mix went to YouTube,
which also sat near zero.
Snapchat paused (Mohammad, 9 Oct 2026: "forget snapchat for now"): no
Snapchat copies or captions are made or handed to him until he brings it
back. The rules below stay for when it returns.
Snapchat test (Mohammad, 4 Oct 2026): Digital Lounge gets a Snapchat
public profile, because Saudi Arabia and the UAE are among Snapchat's
strongest markets and Spotlight (its TikTok-style feed) takes the same 9:16
Reels. He posts by hand from his phone; nothing goes through Postiz until the
account shows reach, and then only after he says so. Start at one or two
posts a day, strongest stories and original material first (our charts and
stills, his gameplay), trailers last. Each approved Reel is handed to him
with a short Arabic Spotlight caption. Judge it after two weeks against
Instagram Reels (about 1,000 views each). Same name and mark as the other
Digital Lounge accounts.
Created 4 Oct 2026 about 08:05 Dubai: username the_digilounge, name
ديجيتال لاونج, the play mark as picture; public profile set up next.
Spotlight's detector flagged the FF7 Revelation Reel (Square Enix CG trailer)
as "undisclosed AI-generated content" on 4 Oct; the in-app appeal (tap the
"!" on the tile, then "here") stating it is the publisher's official
trailer with our text was granted within about half an hour. Appeal any
such flag on official footage; never add the AI label to work around it.
Snapchat filter (Mohammad, 5 Oct 2026, after a second AI flag, this time
on Konami's Metal Gear Solid Δ launch trailer): the detector trips on
photorealistic in-engine CG, so Snapchat only gets our own graphics (sales
charts, the PS Store Reel kind), stylised or animated games (Nintendo,
anime-style art) and, later, his gameplay. Reels built on photorealistic CG
trailers (Metal Gear, FF7, Call of Duty and the like) skip Snapchat and go to
X, Instagram and Threads as normal. Any flag that still comes is appealed in
the app with the publisher's name and the trailer it came from.
Posting route (Mohammad, 5 Oct 2026): Snapchat stays hand-posted, from his
phone or from Snap's web uploader at my.snapchat.com (Post to Spotlight / My
Story). Postiz has no Snapchat channel; API services (ShortSync, bundle.social,
Ayrshare) were compared on 5 Oct and parked, and browser automation of his
account is out (Snap's terms forbid automated or semi-automated access). For
every approved Reel that passes the filter, hand him the `-snap.mp4` copy
together with its Arabic Spotlight caption (about 160 characters, Arabic
first, two or three hashtags) in one message, ready to drag and paste.
Snapchat copies drop the platform row (Snap's recommendation guidelines,
Quality, read 4 Oct 2026: a username paired with another app's name or logo
is not eligible for Spotlight, nor are off-platform links, unoriginal
reposts without creative transformation, letterboxed or blurry video,
strobes without a warning, or wholly AI-made video). `outro.snap_cut(reel,
out, accent=G.ACCENTS[theme])` writes `<name>-snap.mp4`: the same Reel with
an end card of mark, name and handle only. Hand him that file for Snapchat,
never the X/Instagram one. The profile intro and Story can show the other
accounts; only Spotlight posts can't.
Threads (Mohammad, 4 Oct 2026): Digital Lounge Threads (@the_digilounge,
made from the Instagram account) joined Postiz on 4 Oct 2026 as integration
`cmuu27hg405tls00yikmo4ij3`, platform `threads`, no settings (`"settings":
{}`), 500 characters a post. A small test, judged after two weeks like
Snapchat: does it reach anyone beyond the Instagram crowd. Every story
(Mohammad, 10 Oct 2026: "should carry all stories at the same time"; was one
or two a day): every Digital Lounge story goes to Threads at the same time as
its X and Instagram posts, carrying the short X text and the same Reel; no
hashtags. Digital Lounge runs on X, Instagram and Threads. Preflight knows
the account.
Digital Lounge YouTube (@the_digilounge, the old "Digi-ديجي" channel)
was rebranded on 27 Sep 2026: name "ديجيتال لاونج | أخبار الألعاب", Arabic
description, banner `live/2026-09-27/youtube/digi-youtube-banner.png`
(2560x1440, `yt_banner.py`). The Reels go there as Shorts (vertical, 3
minutes or less). Connected to Postiz on 27 Sep 2026 as integration
`cmuk20rj302oqpr0ygqzcdzch`, platform `youtube` (Postiz name matches the
channel). Its job.json takes `"platform": "youtube"` and settings
`{"title": "...", "type": "public", "selfDeclaredMadeForKids": "no"}`,
optional `tags` as `[{"value": "..", "label": ".."}]`. The title (2 to
100 characters) starts with an Arabic word like every Arabic line; the
content is the description (5000 characters). Every post needs a video.
YouTube Shorts are standard (Mohammad, 27 Sep 2026, after the Dynasty
Warriors 3 test looked right): every Digital Lounge story with a video goes
to YouTube with the rest of Digital Lounge, same Reel file and same time as
its X and Instagram posts. Title: the story in one Arabic-first line.
Description: the Instagram caption.
Studio upload defaults (Mohammad, 28 Sep 2026): video and title
language Arabic, category Gaming, tags and channel keywords "ألعاب, أخبار
الألعاب, أخبار الألعاب بالعربي, بلايستيشن, نينتندو, إكس بوكس, gaming news";
country United Arab Emirates. Whether Postiz uploads inherit them is
unchecked: look at the first Short of 29 Sep, and if they did not carry
over, send them from job.json where Postiz has the fields.

<!-- moved from CLAUDE.md lines 1603 to 1655 (28 Oct 2026 version), word for word -->
Instagram (Mohammad, 27 Sep 2026): every Digital Lounge story also goes to
Instagram, on its own card and caption, at the same time as its X post:
one time per story, both job.json files carry the same date. (The first
batch ran later on Instagram only because the channel was being set up.) Empty space is the thing to avoid:
blurred fill and bare panels read as wasted.
- Card: `templates/ig_ar.py`, `ig_ar(media, date, source, out, headline,
  summary, label=None, country=None, theme='cold', video=None,
  clip_start=0, clip_seconds=8, audio=True, subtitles=(), src_crop=None)`.
  The news layout: chip and a short headline on top, the media at full
  width and 16:9 (never cropped), a lighter panel with one or two
  sentences (not bullets), then the footer laid out as on X (mark and name
  right with @the_digilounge and the X and Instagram glyphs under it,
  source centre, date left). Stills are 3:4, 1080x1440, which Instagram
  shows uncropped in feed and grid. Video is a 9:16 Reel with the same
  stack in the middle 1350px the feed shows, a subtitle band between the
  clip and the panel, and the blurred clip behind. `src_crop` trims a
  trailer's own letterbox (ffmpeg cropdetect).
  Reels safe zone (Mohammad, 27 Sep 2026; also for TikTok later): the
  Reels UI covers the right edge (like, comment, share, menu) and the
  bottom (account name, caption), so text, chips and the footer sit in
  x 96 to 910, y 285 to 1480 (`SAFE_*` in ig_ar.py); only the clip runs
  full width. That fits a two-line headline and a two-line summary.
  Text fills the space (Mohammad, 30 Sep 2026: the fixed 46/33 sizes left
  an empty band under the panel on the Crimson Desert Reel): `_reel_sizes`
  picks the largest headline and summary from `REEL_SIZES` (up to 62/44)
  that still end above the footer, so short copy runs bigger.
  The left edge moved from 64 to 96 on 27 Sep 2026 (Mohammad): tall
  phones zoom a Reel or Short to fill the screen and trim about 55px off
  each side (measured on YouTube), which left the date almost touching
  the edge. Stills keep 64.
  Colour on the grid (Mohammad, 29 Sep 2026: "the account is starting
  to look like a purple wall"): Instagram shows a Reel's first frame as
  its grid tile, and Postiz cannot set a cover, so every Reel now opens
  on the clip full screen with the chip and headline low in the frame
  (`cover=0.8` seconds, inside the 3:4 grid window and the safe zone),
  then fades into the card. Behind the card the blurred clip shows
  through more (`bg_dim=0.5`, was 0.72), with a soft indigo band behind
  the headline so white text holds on pale footage. The mark, chips,
  Dubai type, footer lines and end card stay as they are.
  Stills take the same treatment (Mohammad, 30 Sep 2026, after a batch of
  six stills came out on flat indigo): the story's own art, blurred to
  fill the 3:4 frame, sits behind the card under the same `bg_dim=0.5`,
  with the soft band behind the headline. `bg_dim=1` restores the flat
  ground.
  The right column stays the blurred clip, nothing else (Mohammad,
  27 Sep 2026): a vertical brand strip there was tried and dropped,
  since rotated text reads slowly and the strip crossing the footer
  distracted. The brand stays horizontal, in the footer.
  Accent (Mohammad, 27 Sep 2026, for posts from then on): on Instagram
  the rule under the media, the panel edge and the footer's top line
  take the story's theme colour (cold azure, stylized periwinkle,
  playful mint, spectacle amber; `ACCENTS` in ig_ar.py). The chip stays
  azure on every story, and headline and summary stay ink.

<!-- moved from CLAUDE.md lines 2891 to 2941 (28 Oct 2026 version), word for word -->
## Postiz shut down: publishing paused (advisor, 22 Oct 2026)

Postiz shut down for all customers after a suspected breach at its host,
Railway (Railway disclosed exposed customer credentials on 21 Oct; from
22:36Z on 21 Oct api.postiz.com and the app answered Railway's "Application
not found"). Mohammad is disconnecting Postiz from every social account.
This overrides every queuing and publishing rule below until he lifts it.
1. Stop publishing. Nothing is pushed to queue/** in dxb-queue and no publish
   run is started. publish.yml's job carries `if: false` (dxb-queue f105e8a,
   22 Oct about 02:05Z; the session's tools cannot press Disable workflow, so
   Mohammad may also disable it in Actions). Folders already queued stay as
   they are; Xbox cloud playtime and BioWare legacy were moved to drafts/ and
   handed to him at 01:40Z.
2. Keep building. Render, gate and bank Reels as normal; the gap and spacing
   rules (and the gap alarm in the hourly watch) are suspended until
   publishing returns.
3. Manual posting for the strongest stories only: for fresh reveals and
   breaking news, Mohammad gets the final mp4, the Instagram caption and the
   short X text in one message, ready to post from his phone. The story file
   says "posted by hand" once he confirms.
4. The Postiz connector and API are not used until Mohammad says Postiz is
   safe and has issued a new API key (then `if: false` comes out of
   publish.yml).
5. Morning digest: every Reel banked overnight, with its strip, so he can
   choose what to post by hand.

## Instagram via Meta Business Suite while Postiz is down (advisor, 22 Oct 2026, agreed with Mohammad)

Replaces point 3 of "Postiz shut down: publishing paused". Mohammad schedules
Instagram himself in Meta Business Suite (Meta's own tool). Postiz stays off,
publish.yml stays disabled.
1. Batches, twice a day: a morning batch by 08:00 Dubai (covers 09:00 to
   18:00) and an evening batch by 18:00 Dubai (covers 18:30 to 08:00 the next
   day). Each holds the banked Reels that passed the gate, in the order and
   spacing of "Constant coverage" (30 minutes apart by day, 60 at night); the
   gate is re-run on each just before sending. Per Reel, in slot order: the
   final mp4 named from its Dubai time ("0930-serious-sam-the-third-
   encounter.mp4"), the suggested time (Dubai), and the Instagram caption in a
   plain code block. Then one summary line: count, first and last time, and
   any Reel with a time constraint (embargo, launch hour).
2. Fresh reveals and breaking news go at once, outside the batch, marked
   "post now", with the Instagram caption and the short X text (X and Threads
   stay manual, for these stories only).
3. Records: when Mohammad confirms a batch is scheduled, each story file is
   marked "scheduled by hand (Business Suite) HH:MM Dubai" and the slots go in
   the format ledger, so variety and gap checks still read correctly. X and
   Threads: only stories he posts by hand are recorded there.
4. Unchanged: every quality step, the gate, the variety rules, the director
   review. Nothing goes to Postiz or its API until Mohammad says it is safe and
   has issued a new key.



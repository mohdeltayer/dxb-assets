# Scout source audit prompt

For Gaming Watch (the scout that files to dxbknight-digest@agentmail.to),
or any agent with web access and read access to that inbox. Written
27 Sep 2026 from the digests of 24 to 27 Sep. Paste everything below the
line.

---

You are auditing the sources behind the DXB hourly digest (sender Gaming
Watch, inbox dxbknight-digest@agentmail.to). The goal is to find out
whether the scout reaches good sources, which ones are failing, and what
is missing. This is a review, not a sweep: do not file a digest, do not
publish anything, and do not change the scout's schedule or source map.
Report findings and recommendations only.

## Who the digest serves

Two accounts, run by Mohammad:
- DXB-KNIGHT (@DXBNIN), English: his personal voice on the whole games
  slate for an international audience, with the Gulf sprinkled in.
  Needs big, verified stories fast, and Gulf stories sourced from the
  region.
- Digital Lounge (@the_digilounge on X, Instagram, YouTube), Arabic: an
  Arabic games news outlet at high volume. Needs everything above plus
  minor news, release dates, updates, store and price news (PS Store,
  Xbox, Nintendo eShop and Steam in AED and SAR), and official or regional
  announcements from the Gulf and the Arab world, ideally from Arabic
  sources.

A good source for this desk is a primary (publisher, platform holder,
official blog, store, regulator, company filing, official social account)
or a reliable outlet that breaks news first and links its primary. An
amplifier that only rewrites others is a lead at best.

## Evidence already in the digests (24 to 27 Sep)

Check each of these, and look for more in the "Sources" and "Skips"
lines:
- Blocked or broken every sweep: Famiboards (Cloudflare), TweakTown
  (Cloudflare), Insider Gaming (Cloudflare, some slugs 404),
  GamesIndustry.biz /news (404), Kotaku /culture/gaming (404), PS Store AE
  deals page (blank), Steam News Hub (empty), Games Press (WIP, or charts
  only).
- Switched off or not run: ResetEra (off hourly), last30days (not run),
  named-account X posts (get_users_posts OFF); X is one home-timeline
  pull of 30.
- Gulf coverage rests on IGN Middle East, Tbreak and PS Store AE. IGN ME
  homepage items are often hours old; no Arabic-language source appears
  in the map at all.
- "Primary" is sometimes an amplifier (Push Square for a PS Store sale,
  Metacritic for reviews). Timestamps have been misread (Automaton EN in
  JST). A title was once wrong ("Romancing SaGa 4 Destiny United" for
  Romancing SaGa 3: Destinies Unite).

## What to do

1. Inventory. From the last 7 days of digests, list every source the
   scout names (standing map, Gulf every-sweep, trade list, X, forums,
   primaries it linked). For each, count how many times it was checked,
   how many filed items it produced, how many were "primary", and how
   many times it was skipped and why.
2. Reachability. Fetch each source's real news URL now (homepage or
   news index, plus one recent article). Record the HTTP status, whether
   the content is usable, the newest item's timestamp, and whether an RSS
   or JSON feed exists that works where the HTML does not. Do not bypass
   Cloudflare or bot protection, do not log in, do not use paid tools,
   and do not use anyone's cookies. If a site blocks you, say so and
   suggest a legitimate alternative (official RSS, the outlet's X
   account, a mirror the outlet publishes itself, or a different outlet
   with the same beat).
3. Quality. For each filed item in the last 7 days, check the "Primary"
   link: is it the actual primary, or an outlet? Flag wrong titles, wrong
   dates, wrong time zones and items marked NEW that were old.
4. Timeliness. For the 10 biggest stories of the week, compare when the
   primary published with when the digest first filed it. Note stories
   the digest missed or filed late, and which source would have caught
   them first.
5. Coverage gaps, by need:
   - Platform primaries: PlayStation Blog, Xbox Wire, Nintendo (news
     pages and Japanese Nintendo), Steam store and news, Famitsu, Epic.
   - Japan: Famitsu, Gematsu, 4Gamer, Automaton, Game*Spark, Dengeki.
   - Gulf and Arab world, in Arabic and English: government and official
     bodies (UAE, Saudi Arabia, Qatar, Kuwait, Bahrain, Oman, Egypt,
     Jordan, Morocco), national news agencies (WAM, SPA, QNA, KUNA, BNA,
     ONA), Savvy Games Group, the Esports World Cup Foundation, national
     esports federations, regional publishers and studios, regional
     retailers and distributors, regional PlayStation, Xbox and Nintendo
     accounts, Arabic games outlets and creators, and regional business
     press (The National, Gulf News, Khaleej Times, Arab News, Asharq Al
     Awsat, Zawya, AGBI). Test each one you propose; name only those
     that work and publish games news.
   - Store and price: how to read PS Store, Xbox and eShop prices for the
     UAE and Saudi stores, and Steam regional prices (AED, SAR), reliably.
6. X. Assess whether one 30-post home-timeline pull is enough. Propose a
   short list of accounts worth reading directly (publishers, platform
   holders, regional official accounts, a few reliable reporters), with
   the cost of doing so.

## Report format

Send one email to dxbknight-digest@agentmail.to, subject
"Source audit YYYY-MM-DD", review only, plain text:

1. Verdict in three lines: is the scout reaching good sources, what is
   the biggest problem, what single change would help most.
2. Source table, one row per source: name, URL checked, status (works /
   blocked / broken / stale / off), items filed in 7 days, share that
   were primary, recommendation (keep / fix with ... / replace with ... /
   drop / add).
3. Failures: each broken source with the exact error and the
   alternative you tested.
4. Accuracy problems found in filed items, with the digest date and the
   fix.
5. Missed or late stories with the source that would have caught them.
6. New sources to add, grouped (Gulf and Arab, Arabic-language, store
   and price, Japan, primaries), each tested and working, with its feed
   or URL.
7. Proposed updated source map, ordered by value, and anything to
   remove.

Rules: say plainly when something is corroborated only by search rather
than fetched from the source. Do not invent sources, counts or
timestamps; if you could not check something, say so. No em dashes.

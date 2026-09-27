# Scout optimisation prompt (additive only)

For Gaming Watch. Written 28 Sep 2026 from its own source audit
(`notes/scout-source-audit-2026-09-28.md`). Mohammad's condition: full,
quality coverage without changing how the scout works now or risking the
sources it already has. Everything below adds to the current setup;
nothing is removed or replaced. Paste everything below the line.

---

This is an additive update to your sweep. Your current source map,
schedule, run times, X usage, filters and digest format stay exactly as
they are. Do not remove, replace, reorder or skip any source you use
today, even the ones your audit found blocked. The changes below only add
fallbacks, extra sources and quality labels on top.

## Ground rules

1. Existing sources run first, every sweep, as now. New checks run after
   them.
2. If the new checks would make a run noticeably longer than usual, do
   them in rotation (half on one sweep, half on the next) rather than
   delaying the digest or cutting an existing source.
3. No new cost: no extra X API calls, no named-account reads, no extra
   runs, no paid tools. Those need Mohammad's approval separately.
4. No bypassing Cloudflare or bot checks, no logins, no cookies.
5. If anything in this update causes an error or a missed digest, drop
   the new part for that run, send the digest as normal, and note it in
   Skips. Never let an addition cost a digest.

## 1. Fallback feeds (only when the current page fails)

Keep checking each page exactly as now. Only when it fails (blocked,
404, blank, JS shell), read its feed instead and note "via RSS" in the
Sources line:
- TweakTown: tweaktown.com/feeds/news-mf.xml
- Insider Gaming: insider-gaming.com/feed
- Kotaku: kotaku.com/feed
- GamesIndustry.biz: gamesindustry.biz/feed
- Steam News Hub: store.steampowered.com/feeds/news/?l=english (not
  feeds/news.xml, which is stale)
- IGN Middle East: when the English feed is older than 6 hours, also read
  me.ign.com/ar/feed.xml
- Automaton EN: when stale, also read automaton-media.com/feed/ (JP)
- Push Square, Pure Xbox, Nintendo Life: when blocked, use the platform
  primary below for the same story

## 2. Extra sources (added, not replacing)

Primaries, every sweep, read by feed:
- PlayStation Blog: blog.playstation.com/feed/
- Xbox Wire: news.xbox.com/en-us/feed/
- Steam news: store.steampowered.com/feeds/news/?l=english
- Nintendo: nintendo.com/us/whatsnew/ and nintendo.co.jp/ir/en/

Arabic games outlets, every sweep, as leads (they are outlets, not
primaries):
- IGN Middle East Arabic: me.ign.com/ar/feed.xml
- True Gaming: true-gaming.net/home/feed/
- Saudi Gamer: saudigamer.com/feed/
- VGA4A: vga4a.com/feed

Japan, every sweep, as leads:
- Automaton JP: automaton-media.com/feed/
- Denfaminicogamer: news.denfaminicogamer.jp/feed
- 4Gamer: 4gamer.net/rss/index.xml
- Game*Spark: gamespark.jp/rss/index.rdf

Gulf official and business, overnight runs only, keyword check (games,
esports, Savvy, الألعاب, الرياضات الإلكترونية): spa.gov.sa (Arabic and
English), esportsworldcup.com/en/news, savvygames.com/media-center,
gulfnews.com/technology/gaming, arabnews.com/rss.xml.

Prices, overnight runs only, for games already in the news that day
(free, no login):
- Steam: store.steampowered.com/api/appdetails?appids=<id>&cc=ae (AED)
  and &cc=sa (SAR), filters=price_overview
- Xbox: displaycatalog.mp.microsoft.com/v7.0/products?bigIds=<id>&market=AE
  and market=SA
- PS Store: product pages store.playstation.com/en-ae/product/<id> and
  en-sa (these stores price in USD; say so, never convert to AED or SAR)
- Nintendo: no official eShop in the UAE or Saudi Arabia; report regional
  retail announcements only, never an eShop price for those countries

## 3. Quality labels (same items, better labelled)

These change how an item is labelled, not which items you file:
- Primary line: trace every item to its publisher, platform, store,
  regulator, filing or official account and link that. If you cannot,
  keep filing it but label the line "Outlet report: <outlet URL>"
  instead of "Primary".
- Age: take the time from the primary, convert to Dubai (JST minus 5h,
  UTC plus 4h, PDT plus 11h, PST plus 12h) and label NEW, SAME_DAY or
  AGE (with hours) from that, not from when an outlet rewrote it.
- No refiles: keep a 7-day ledger of filed stories (title, primary URL,
  first filed). If a story is already in it, file it again only when
  something material changed, and say what.
- Titles: copy game names from the publisher's own page.

## 4. Trial and report

Run this for 7 days. For those 7 days, put anything that came only from
a new source (section 2) under its own heading "From new sources" at the
end of the digest, so it can be compared with what the current map
found. Everything else stays where it is now.

After 7 days, send one email to dxbknight-digest@agentmail.to, subject
"Additive trial report YYYY-MM-DD", review only:
- stories found only by new sources, and how much earlier than the
  current map found them (if it did at all)
- fallback feeds used, and how often
- any run that was slower or failed because of the additions
- items relabelled "Outlet report" and refiles avoided
- a recommendation per new source: keep, rotate, or drop

Do not change anything beyond this document without Mohammad's approval.
No em dashes.

# Scout source audit, 28 Sep 2026 (Gaming Watch report, verbatim)

Received 28 Sep 2026 00:17 Dubai in dxbknight-digest. Not yet acted on; changes need Mohammad's approval.

```
SOURCE AUDIT, Gaming Watch (DXB-KNIGHT / Digital Lounge), review only
Window: digests sent Sep 21 05:45 to Sep 27 23:43 Dubai. Checks run Sep 28 00:05 to 01:00 Dubai. All times Dubai (UTC+4).
Basis: 106 "DXB digest" mails in gamingwatch@agentmail.to (about 101 sweeps plus 4 hunt packs/dig-deeps and 1 stub). 26 digests read in full (21 local copies in /workspace plus 5 via AgentMail). Per-source mention counts come from AgentMail full-text search across all 106 and are lower bounds (abbreviations like "IGN ME" do not always match). Primary-link counts come from 20 local digests Sep 22 to Sep 27 (85 Primary links). No digest was filed, nothing was posted, no routine or map was changed.

1. VERDICT
Reaching good sources: partly. 10 of the 14 standing and Gulf sources fail as configured (blocked, 404, JS shell, stale or off), and only about 29% of sampled Primary links (25 of 85) were real primaries.
Biggest problem: outlets and rewrites filed as "primary", which lets old items go out as new and get refiled (SteamOS 3.9.2 33h late and filed twice, Nintendo $4.5M judgment filed three times, Sony patent 4 days late).
Single change that would help most: switch to a feed-first map led by platform primaries (PlayStation Blog, Xbox Wire, Steam news RSS, Nintendo) and require the Primary line to be a publisher, platform, store, regulator or filing URL, otherwise label it "outlet report".

2. SOURCE TABLE
Columns: source | URL checked | status now | digests naming it (of 106, lower bound) | used as Primary link (of 85 sampled) | real primary? | recommendation
Note: an exact per-source count of filed items was not possible without reading all 101 sweeps; the Primary-link column is the measured proxy. For an outlet the "share primary" is 0% by definition.

STANDING MAP
X home timeline | get_users_timeline max 30 (not called in audit) | works, leads only | every sweep | 1 | no (leads) | keep, add author expansion, add named accounts (section 6)
TweakTown | tweaktown.com/news/gaming/ and tweaktown.com/feeds/news-mf.xml | HTML broken (404 / challenge script), RSS works, newest Sep 27 23:20 | 54 (19+ skips) | 0 | no | fix with RSS
Dexerto | dexerto.com/feed | works, newest Sep 27 19:27 | 51 | 1 | no (breaks some stories) | keep via RSS
Insider Gaming | insider-gaming.com and /feed | HTML blocked (captcha), RSS works, newest Sep 27 23:36 | 59 (10+ skips) | 5 | own exclusives only | fix with RSS
TheGamer | thegamer.com/feed | works, newest Sep 27 21:20 | 54 | 1 | no (amplifier) | keep as lead only
Kotaku | kotaku.com/culture/gaming and /feed | section 404, RSS works, newest Sep 27 23:49 | 52 | 3 | no | fix with RSS
Automaton EN | automaton-media.com/en/feed/ | stale, newest Sep 25 17:00 | 51 | 2 | no | replace with Automaton JP feed
Games Press | gamespress.com/en-US, /rss, /en-US/News | homepage 200 but /rss and /News 404, digests say WIP or charts only | 73 (22+ skips) | 5 | hosts publisher releases | drop from every sweep, use publisher newsrooms
Famiboards | famiboards.com | blocked (Cloudflare challenge, forum path 404) | 91 (35+ skips) | 0 | no (forum) | drop
ResetEra | resetera.com | off hourly, 403 challenge | n/c | 0 | no (forum) | drop
last30days | overnight tool | not run in most overnights | n/c | 0 | no | drop or keep overnight only
GULF EVERY SWEEP
IGN Middle East EN | me.ign.com/en/feed.xml | stale, newest Sep 26 19:22 (28h) | 31+ | n/c | no | replace with IGN ME Arabic feed
Tbreak | tbreak.com/feed/ | works, newest Sep 27 23:11 | 61 | 2 | no (regional outlet) | keep, never as primary
PS Store AE deals | store.playstation.com/en-ae deals page | broken (client-rendered shell, no prices) | 32+ "blank" | 0 | store | replace with product-page reads (section 6)
PLATFORM AND TRADE (named in digests)
Steam News Hub | store.steampowered.com/news/ | HTML is a JS shell | 16+ "empty" | 3 (store pages) | yes | replace with store.steampowered.com/feeds/news/?l=english (newest Sep 28 00:03)
PlayStation Blog | blog.playstation.com/feed/ | works, newest Sep 25 21:20 | n/c | 1 | yes | add every sweep
Xbox Wire | news.xbox.com/en-us/feed/ | works, newest Sep 26 22:00 | n/c | 2 | yes | add every sweep
Nintendo | nintendo.com/us/whatsnew/, nintendo.co.jp/ir/en/, nintendo.com/jp/topics | US and IR work, JP topics JS-rendered (JSON 400, RSS 404) | n/c | 1 | yes | add US whatsnew + IR + @Nintendo on X
Famitsu | famitsu.com/news/, RSS | broken (404 on /news, /news/latest, RSS) | 20 (/news 404 in 6 Sep 27 digests) | 0 | no | replace with Denfaminicogamer, 4Gamer, Game*Spark feeds
Epic / Fortnite | store.epicgames.com news, fortnite.com/news | blocked (Cloudflare challenge) | n/c | 0 | yes | replace with @Fortnite on X
GamesIndustry.biz | gamesindustry.biz/news and /feed | /news 404, RSS works, newest Sep 25 19:30 | n/c | 0 | trade outlet | fix with RSS
Gematsu | gematsu.com/feed | works, newest Sep 26 05:59 (quiet since) | n/c | 10 | no (links JP releases) | keep, cite its linked release instead
VGC | videogameschronicle.com/feed | works, newest Sep 27 11:54 | n/c | 4 | no | keep as lead
Nintendo Everything | nintendoeverything.com/feed/ | works, newest Sep 27 20:00 | n/c | 6 | no (amplifier) | lead only
GoNintendo | gonintendo.com/feeds/all.xml | works, newest Sep 27 19:44 | n/c | 1 | no | lead only
Push Square | pushsquare.com/news and /feeds/latest | blocked (403 Access denied) | n/c | 4 | no | drop, use PlayStation Blog
Pure Xbox | purexbox.com/news and /feeds/latest | blocked (403) | n/c | 3 | no | drop, use Xbox Wire
Nintendo Life | nintendolife.com/news and /feeds/latest | blocked (403) | n/c | 5 | no | drop, use Nintendo primaries
Nintendo Insider | nintendo-insider.com | blocked (403 challenge) | n/c | 1 | no | drop
GamingOnLinux | gamingonlinux.com/article_rss.php | works, newest Sep 26 11:34 | n/c | n/c | no | lead only, cite Steam app feed
DSOGaming | dsogaming.com | works (200) | n/c | n/c | no | lead only, cite GitHub release
IGN SEA | sea.ign.com | works (200) | n/c | 1 | no | lead only
IGN global | ign.com/rss/v2/articles/feed | works, newest Sep 27 22:56 | n/c | 1 | no | keep as lead
Eurogamer | eurogamer.net/feed | works, newest Sep 27 19:25 | n/c | 0 | no | optional lead
Game Informer | gameinformer.com/rss.xml | works, newest Sep 26 01:55 | n/c | 1 | own covers only | keep for exclusives
Metacritic | metacritic.com | challenge script | n/c | n/c | no | use publisher review round-ups or OpenCritic (not tested)
SteamDB | steamdb.info | blocked (403) | n/c | 0 | no | use Steam API instead

3. FAILURES (exact error, alternative tested)
- Famiboards: HTTP 200 but Cloudflare "Just a moment" challenge page, forum path 404. No feed. Alternative: none needed; rumors are covered by Insider Gaming RSS (works) and reporters on X. Drop.
- TweakTown: /news/gaming/ 404; homepage serves a challenge script. Alternative tested: tweaktown.com/feeds/news-mf.xml, 200, newest Sep 27 23:20. Use it.
- Insider Gaming: homepage carries captcha scripts, some slugs 404. Alternative tested: insider-gaming.com/feed, 200, newest Sep 27 23:36.
- Kotaku: /culture/gaming 404. Alternative tested: kotaku.com/feed, 200, newest Sep 27 23:49.
- GamesIndustry.biz: /news 404. Alternative tested: gamesindustry.biz/feed, 200, newest Sep 25 19:30 (it had Build A Rocket Boy at 13:55 Sep 25).
- Games Press: /rss 404, /en-US/News 404; homepage 200 but WIP or charts only in digests, assets login-walled. Alternative: publisher newsrooms (PlayStation Blog, Xbox Wire, prnewswire, company IR) all tested 200.
- PS Store AE deals: page is client-rendered, the HTML has no product or price data (why digests say "blank"). Alternative tested: product pages store.playstation.com/en-ae/product/<id> are server-rendered with prices (see 6).
- Steam News Hub: JS shell. Alternative tested: store.steampowered.com/feeds/news/?l=english (200, newest Sep 28 00:03), per-app feeds such as /feeds/news/app/1675200/ (Steam Deck, 200, newest Sep 27 22:46), api.steampowered.com/ISteamNews/GetNewsForApp/v2/ (200). Note feeds/news.xml is stale (Jul 17), do not use.
- Famitsu: /news/, /news/latest, /category/news, famitsu_news.rdf and /feed all 404; homepage 200. Alternatives tested: Denfaminicogamer feed (newest Sep 27 18:50), 4Gamer rss/index.xml (Sep 27 19:00), Game*Spark rss/index.rdf (Sep 27 15:30), Automaton JP feed (Sep 27 12:59).
- Automaton EN: feed works but newest item Sep 25 17:00, 2+ days stale. Alternative: Automaton JP feed (above).
- IGN Middle East EN: feed newest Sep 26 19:22 at check time. Alternative tested: me.ign.com/ar/feed.xml, newest Sep 27 22:48, 40 items.
- Push Square, Pure Xbox, Nintendo Life: HTML and /feeds/latest all 403 "Access denied". Alternatives: PlayStation Blog, Xbox Wire, nintendo.com/us/whatsnew (all 200).
- Epic / fortnite.com: Cloudflare challenge on store news, epicgames.com news and fortnite.com/news. Alternative: @Fortnite on X (the old @FortniteGame bio says it moved there; handle not looked up).
- Dengeki Online RSS 404 (homepage 200). Alternative: 4Gamer / Game*Spark feeds.
- Nintendo JP topics: JSON endpoint 400, rss.xml 404, HTML is JS-rendered. Alternative: @Nintendo on X (verified, 5.7M followers) plus nintendo.co.jp/ir/en/ (200).
- ResetEra: 403 challenge. No alternative needed.

4. ACCURACY PROBLEMS IN FILED ITEMS
- SteamOS 3.9.2 beta (Sep 27 12:26 and 13:19): the official Steam post went up Sat Sep 26 03:16 Dubai, and GamingOnLinux followed at 11:22. Filed at 12:26 as ICYMI, then refiled at 13:19 as SAME_DAY with GoL as primary. Fix: primary store.steampowered.com/news/app/1675200/view/674006995886409302, label AGE (33h), file once.
- SharpEmu v0.0.4 (Sep 27 13:19): the GitHub release was Sep 26 02:20 and DSOGaming Sep 27 00:33. Filed as SAME_DAY with DSO as primary. Fix: primary github.com/sharpemu/sharpemu/releases (Atom feed works), label AGE.
- Sony contactless DualSense patent (Sep 27 14:25): USPTO published it Sep 17, and Dexerto, GamesRadar and IGN ME ran it Sep 23. VGC's rewrite was Sep 27 11:54. No earlier digest filing found. Filed as new with VGC as primary. Fix: cite the patent (US20260273403A1), label AGE (4 days), credit Dexerto. Patent and Dexerto dates are from search plus the VGC feed, not a USPTO fetch.
- Garfield: Escape from Monday (Sep 27): marked "confirmed by primary" with only Nintendo Everything linked. The game launched Sep 24 and the trailer was on PlayStation YouTube Sep 24 (search only). Fix: cite publisher Microids or the platform trailer, label AGE.
- FNAF x Fortnitemares (Sep 27 23:43): marked "confirmed" while fortnite.com was unfetched (Cloudflare). TheGamer says Oct 11. Tbreak, Insider Gaming, Denfaminicogamer (18:50), Beebom, Forbes and others say Oct 1, from Epic's trailer. Fix: cite @Fortnite or Epic's trailer post, state Oct 1 and flag TheGamer's Oct 11 as the outlier.
- Nintendo maintenance (Sep 27 23:43): Nintendo Everything (20:00) used as primary. Fix: nintendo.co.jp/netinfo (page 200, but status is loaded by script, so contents were not verified).
- Minecraft Ice Caves trailer (Sep 27 10:27): IGN SEA (Sep 26 22:58) used as primary. Fix: minecraft.net/en-us/articles (200) or Xbox Wire's Minecraft Live posts (Sep 26 21:45 to 22:00), label AGE.
- Nintendo $4.5M Archbox judgment: filed three times. Sep 24 18:54 (primary "court judgment relayed via Aftermath then NE"), Sep 24 23:47 again, and Sep 25 14:24 again as "Not filed in prior hourly" with TorrentFreak. Fix: a 7-day filed-story ledger, and cite the court docket.
- Hartvick GTA 6 comments: first filed Sep 25 06:05 (Dexerto Sep 25 00:17). The later refile you flagged was not found by my search.
- Outlet-as-primary pattern (examples): Tbreak for a Microsoft patent (Sep 26 09:30); Gematsu for LEVEL-5 (Sep 26 10:26); Automaton for @kazkodaka and @PROJECT_ACES quotes (Sep 25 11:22, cite the X posts); NE eShop charts "confirmed by primary" (Sep 27 10:27); Gamefile for Meta Horizon (Sep 25 09:30, cite Meta newsroom); IGN SEA for the PS disc-polling rumor (Sep 25 09:30); Push Square for Warzone and a DW3 demo. In the sample, Gematsu (10), Nintendo Everything (6), Insider Gaming (5), Nintendo Life (5), VGC (4) and Push Square (4) were the most-used "primaries".
- Soft items filed despite do-not-send rules: NE "best SD cards" feature (Sep 26 09:30), PS5 next-week slate guide, Game Pass October guide.
- Automaton EN JST misread and the wrong "Romancing SaGa 4 Destiny United" title: not located in the digests I read or by text search (the Sep 21 13:25 digest has "Romancing SaGa Destinies Unite... numeral not verified"). Fixes: JST minus 5h = Dubai; copy titles from the publisher page.

5. MISSED OR LATE STORIES (top 10 of the week; primary time vs first digest filing)
1) Xbox "Continuing Our Reset" (268 roles, Halo to Activision, Ninja Theory): Xbox Wire Sep 22 18:00. Filed Sep 22 19:01. On time.
2) Meta VR Glasses ($1,299.99, Spring 2027): Meta newsroom published_time Sep 23 15:42 (not cross-checked against keynote time). First filed Sep 24 06:01 overnight, about 14h later. No match in the Sep 23 evening hourlies or overnight. Would catch: about.fb.com/news (200).
3) Armed Fantasia cancelled: Gematsu Sep 24 22:00 (Digital Bros results PDF, time not established). Missed by the Sep 24 23:47 overnight, filed Sep 25 06:06, about 8h late. Would catch: Gematsu feed (works).
4) GTA 6 preorder PS5 skew (The Verge) plus Xbox CSO reply: Verge Sep 24 20:00. Missed by the 23:47 overnight, filed Sep 25 06:06, about 10h late. Would catch: The Verge / @tomwarren.
5) Build A Rocket Boy administration: GamesIndustry.biz Sep 25 13:55. Missed by the 14:24 to 19:21 hourlies, filed Sep 26 02:32, about 12.5h late. Would catch: GamesIndustry.biz /feed (the scout was hitting the 404 /news URL).
6) GTA 6 Game Informer cover: GI Sep 25 22:00 (13:00 CDT). Filed Sep 26 02:32, 4.5h late because the Sep 25 overnight run was missed. Would catch: GI rss.xml.
7) Nintendo $4.5M piracy judgment: filed Sep 24 18:54 on time, but refiled twice (see 4).
8) Minecraft Live / The Sift: Xbox Wire Sep 26 21:45 to 22:00. Filed Sep 26 23:43. On time.
9) FNAF x Fortnite: TheGamer Sep 27 17:27, Denfaminicogamer 18:50 (Epic trailer time not checked). Missed by the 18:25 and 19:24 hourlies, filed 23:43, 6h+ late. Would catch: @Fortnite on X, TheGamer / Kotaku RSS.
10) Sony contactless controller patent: Dexerto Sep 23. First filing found Sep 27 14:25, about 4 days late and labelled new. Would catch: Dexerto RSS.
Also late: SteamOS 3.9.2 beta, 33h after the Steam post (see 4).
Pattern: the 11:30 PM overnight misses US-afternoon stories that land 20:00 to 23:00 (items 3, 4, 6). The feeds and official accounts in section 6 would have surfaced 2, 3, 5, 6 and 9 at the next sweep.

6. NEW SOURCES TO ADD (each tested Sep 28, 00:05 to 01:00 Dubai)
GULF AND ARAB (official and business)
- PlayStation Arabia @PlayStation_ME (id 24512707, 356K followers, business-verified), PlayStation Saudi @PlayStationSA (id 86523463, 821K), Xbox Arabia @XboxArabia (id 185984745), Saudi Esports Federation @Saudi_Esports (id 939828926863552512), Savvy Games Group @SavvyGamesGroup (id 1476627826480582667), Esports World Cup @EWC_EN (id 1532693504413028354). All confirmed with one X user lookup.
- Esports World Cup news: esportsworldcup.com/en/news, 200, newest dated item Sep 18.
- Savvy Games Group media center: savvygames.com/media-center, 200, items Sep 3 to Sep 7 (MoUs with Ministry of Education, MCIT, Gosu Academy).
- SPA (Saudi Press Agency): spa.gov.sa/en and spa.gov.sa (Arabic), both 200, server-rendered. Games content not measured, so use keyword checks for Savvy, esports and "الرياضات الإلكترونية".
- Arab News RSS: arabnews.com/rss.xml, 200, newest Sep 27 23:54. Low yield (1 games item in 50: "Riyadh event to unite gaming industry leaders").
- Gulf News gaming section: gulfnews.com/technology/gaming, 200, items to Sep 19. Main RSS stories.rss 200 but 0 games items in 18.
- Low yield, keyword check only: The National (Arc RSS 200, newest 22:31, 0 games items in 83; gaming section 503), Asharq Al-Awsat aawsat.com/feed (200, 300 items, no games items), AGBI /feed/ (200, 0 of 10, newest Sep 25), Zawya (200).
- Not usable: WAM (200 but a 4KB JS shell, all three URLs), KUNA (TLS error), BNA (405 human verification), ONA Oman (SSL certificate error), MAP Morocco (403 challenge), Petra Jordan and MENA Egypt (200 with challenge scripts), QNA (200 with captcha, RSS page 404), Saudi Esports Federation website (403), Geekay (403), Virgin Megastore AE (captcha), nintendo.ae (TLS error), nintendo.com/en-ae (404), abudhabigaming.com (TLS error), dubaigaming.ae and esportsworldcupfoundation.com (DNS failure), Khaleej Times RSS (404).
ARABIC-LANGUAGE GAMES OUTLETS (leads, Arabic copy)
- IGN Middle East Arabic: me.ign.com/ar/feed.xml, 200, newest Sep 27 22:48, 40 items.
- True Gaming: true-gaming.net/home/feed/, 200, newest Sep 28 00:08 (e.g. 23:57 "Hell Is Us تصل إلى السويتش 2 الشهر المقبل").
- Saudi Gamer: saudigamer.com/feed/, 200, newest Sep 27 23:44.
- VGA4A: vga4a.com/feed, 200, newest Sep 27 23:51.
- Official Arabic primaries: playstation.com/ar-ae (200), xbox.com/ar-AE and ar-SA (200), plus the Arabic X accounts above.
STORE AND PRICE
- Steam: store.steampowered.com/api/appdetails?appids=<id>&cc=ae&filters=price_overview returns AED (Cyberpunk 2077: AED 229.00). With cc=sa it returns SAR (SAR 229.00). No login. For sales: api/featuredcategories?cc=ae (200).
- PS Store: product pages store.playstation.com/{en-ae,ar-ae,en-sa,ar-sa}/product/<productId> are server-rendered with prices. UAE and KSA stores price in USD, not AED or SAR (ASTRO BOT, three listed SKUs: UAE 59.99 / 69.99 / 10.00 USD, KSA 65.99 / 76.99 / 11.00 USD). Deals, category and search pages are client-rendered and useless for scraping. Use a watch list of product IDs, plus PlayStation Blog and @PlayStation_ME for sale announcements.
- Xbox: displaycatalog.mp.microsoft.com/v7.0/products?bigIds=<id>&market=AE returns USD, and market=SA returns SAR (Forza Horizon 5: AE USD 22.84 sale / 57.12 MSRP, SA SAR 115.60 / 289.00). No login. The xbox.com/en-AE product page also embeds price JSON.
- Nintendo eShop: api.ec.nintendo.com/v1/price?country=AE (and SA) returns sales_status "not_found", while country=US works. There is no official eShop in UAE or KSA, so do not report AED or SAR eShop prices. Report regional retail announcements only.
JAPAN
- Automaton JP automaton-media.com/feed/ (newest Sep 27 12:59), Denfaminicogamer news.denfaminicogamer.jp/feed (18:50), 4Gamer 4gamer.net/rss/index.xml (19:00), Game*Spark gamespark.jp/rss/index.rdf (15:30), Gematsu gematsu.com/feed (English, links JP releases). Famitsu and Dengeki have no working feed.
PRIMARIES
- PlayStation Blog feed, Xbox Wire feed, Steam news RSS plus per-app feeds and the ISteamNews API, nintendo.com/us/whatsnew/ (200), Nintendo IR nintendo.co.jp/ir/en/ (200), sonyinteractive.com/en/news/ (200), Sony press sony.com/en/SonyInfo/News/Press/ (200), Capcom IR news (200), Meta newsroom about.fb.com/news (200), minecraft.net/en-us/articles (200), GitHub releases Atom for emulator and tool items, UK Companies House for insolvency. Blocked: Epic, Square Enix press (403), SEGA news (429).

X ASSESSMENT
- One 30-post home-timeline pull per run is not enough for primaries. It only sees what the account follows and caps at 30 per run. The Sep 25 06:06 overnight digest noted that timeline posts came without author fields (no expansions), so the scout cannot tell an official post from a fan rewrite. FNAF (Epic trailer) and the Kodaka / PROJECT_ACES posts reached the digest through outlets, hours later.
- Proposed direct reads (get_users_posts, max_results 5, since_id). All handles were confirmed by one batch user lookup costing about $0.19 to $0.20; balance was $89.48 before it.
  Tier A, every run (14 a day): PlayStation (10671602), XBOX (24742040), Nintendo JP (307902310), NintendoAmerica (5162861), Steam (36803580), RockstarGames (29758446), PlayStation_ME, PlayStationSA, Fortnite (handle from @FortniteGame bio, not looked up).
  Tier B, overnights only (2 a day): XboxArabia, SavvyGamesGroup, EWC_EN, Saudi_Esports, tomwarren (Verge), Chris_Dring (The Game Business), gematsu.
  Rejected: jasonschreier (bio says no longer on X), Okami13_ (an aggregator account "KAMI", not a reporter), IGNMiddleEast (not found), tbreak (unrelated account).
- Cost at $0.005 per post returned: $0.025 per call at max_results 5. Worst case with every call full: Tier A 9 x 5 x 14 = 630 posts ($3.15) plus Tier B 7 x 5 x 2 = 70 posts ($0.35), so $3.50 a day. With since_id you pay only for new posts; at roughly 5 to 10 posts a day per official account that is about $0.50 to $1.50 a day. Current timeline spend is about $1.2 a day (Sep 27). Combined, $89.48 lasts about 4 to 5 weeks at the realistic rate. Needs your approval (named reads are OFF).

7. PROPOSED SOURCE MAP (ordered by value)
Every sweep:
1. Platform primaries by feed: PlayStation Blog, Xbox Wire, Steam news RSS (plus Steam Deck app feed), nintendo.com/us/whatsnew.
2. X: home timeline 30 with author expansion, plus Tier A named accounts (after approval).
3. Breaking outlets by RSS, as leads that must be traced to a primary: Insider Gaming, Dexerto, VGC, IGN, Kotaku, TweakTown, GamesIndustry.biz (all feeds tested 200). The Verge via @tomwarren (Verge feed not tested).
4. Gulf and Arabic: IGN ME Arabic feed, True Gaming, Saudi Gamer, VGA4A, Tbreak. Arabic official X accounts (Tier A/B).
5. Japan: Automaton JP, Denfaminicogamer, 4Gamer, Game*Spark, Gematsu.
Daily or overnight:
6. Prices: Steam appdetails cc=ae / cc=sa for a watch list, PS Store product pages en-ae / en-sa (USD), Xbox displaycatalog market=AE / SA, Steam featuredcategories cc=ae for sales.
7. Gulf official and business, keyword check: SPA en/ar, EWC news, Savvy media center, Gulf News gaming, Arab News RSS, The National RSS, Asharq Al-Awsat feed.
8. Company IR and filings: Nintendo IR, Sony IR / SIE news, Capcom IR, Companies House, GitHub releases.
Rules: Primary must be a publisher, platform, store, regulator, filing or official account URL, otherwise "outlet report". Keep a 7-day filed-story ledger and do not refile. Use AGE labels computed from the primary timestamp, converted to Dubai (JST minus 5h, UTC plus 4h, PT plus 11h in PDT).
Remove: Famiboards, ResetEra, Games Press (every sweep), PS Store deals page, Steam News Hub HTML, Famitsu /news, Automaton EN, IGN ME English (demote to lead), Push Square / Pure Xbox / Nintendo Life / Nintendo Insider as primaries, last30days (unless you want it overnight), Metacritic as primary.

Not checked: only 26 of about 101 sweeps were read in full. The dxbknight-digest inbox was not listed separately. Epic pages (Cloudflare), Nintendo netinfo contents, Meta keynote time, Digital Bros PDF time and Epic trailer time were not verified. PS Store GraphQL was not tested. Individual UAE, Qatar, Kuwait, Bahrain, Oman, Egypt, Jordan and Morocco gaming bodies (beyond their news agencies), national esports federations other than Saudi, regional studios and distributors, and Arabic creators were not individually tested.


```

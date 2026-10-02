# What the agent can and cannot use

Written 2 Oct 2026 from what has actually been used or tried in the
sessions so far. Recheck a line before relying on it in a new kind of
job, and update this file when something changes.

## Available

| Capability | Through | Notes |
|---|---|---|
| Reading web pages, press sites, publisher blogs, Steam, PlayStation Blog, Nintendo, Japanese sites | WebFetch, curl | Network opened 23 Sep 2026. Google Patents, pbs.twimg.com and news.xbox.com refuse automated requests |
| Web search | WebSearch | A lead, not a source: on 2 Oct it still dated the Esports Nations Cup to Nov 2026 after its own site moved it to 2027 |
| Official footage | Steam trailers (`trailer.py`), IGN video pages (assets.ign.com MP4), gmedia.playstation.com, Nintendo store `publicId` MP4s | |
| Transcription | faster-whisper (`trailer.transcribe`) | `pip install faster-whisper` in a new container |
| Video and image work | ffmpeg, ffprobe, Pillow, the templates | Dubai fonts must be uploaded again in a new container (`/root/fonts-private/dubai/`) |
| Browser automation | Chromium and Playwright | Pre-installed |
| Publishing | Postiz, through dxb-queue (`publish.py` in GitHub Actions) and the Postiz MCP for reading posts | Integrations: DXB-KNIGHT X, Digital Lounge X, Digital Lounge Instagram (TikTok and YouTube connected but dropped) |
| Scout digests | AgentMail, `dxbknight-digest@agentmail.to` | Read and mark read; sending needs his approval |
| Translation check | DeepL (Free) | Translation only; Arabic rewriting and glossaries need Pro |
| Arabic skills | `arabic-games-film-editor`, `arabic-writing`, `perfect-arabic`, `arabic-grammar-review` | |
| Storage that survives a session | the git repos (dxb-assets, dxb-queue) | The container is wiped, so state lives in git: the ledger, glossary, notes |
| Reminders | `send_later` and Routines | Only when he asks; no scheduled sweep by his choice |
| Notion | Notion MCP | Not used for the newsroom so far |

## Partly available

| Capability | Limit |
|---|---|
| YouTube | No downloads (sign-in wall); trailers come from IGN or publishers instead |
| RSS and Atom | Feeds can be read, but nothing runs between sessions to poll them; the scout does the hourly watching |
| Notifications | `send_later` brings a message back into the session; the scout's email reaches his phone. No push alerts straight from the agent tested |
| Post performance | Read by hand from X and Instagram, or from screenshots he sends. The Postiz MCP has no analytics tool; whether the Postiz API exposes analytics is unchecked |

## Not available

| Capability | What it would take | Needed? |
|---|---|---|
| Reading X (accounts, lists, replies, images) | X API access | Optional: the scout and official sites cover discovery |
| Cross-platform analytics | Metricool or similar (paid), or Postiz analytics if it exists | Optional: his call (newsroom item 8) |
| vidIQ | Connector | Not while YouTube is dropped |
| Firecrawl | Connector | Not needed: WebFetch and curl cover it |
| Canva | Needs authorising in his claude.ai connector settings | Not used |

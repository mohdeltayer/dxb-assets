# Rights register (dxb-assets copy)

Names, terms and licences only: never a token, a login or a private link. Started 29 Oct 2026 by the build desk for
phase 1 INTAKE of adv-20261029-server-handover (prepared trailers, back office service 4).

BUILD.md section 3 names `ops/rights-register.md` in **dxb-queue** as the register; the build desk could not write
there on 29 Oct (no access from this session), so this copy lives in dxb-assets. The machine-readable side the prepare
service reads is `ops/backoffice/prepare/rights.yaml`; the two are kept in step (its test fails when a publisher in
rights.yaml is missing here). When the dxb-queue register is reachable, merge this table into it and keep one source.

## 1. Footage: the terms each prepared asset relies on

Every prepared asset's `manifest.json` carries: source page, exact URL, credit line, rights basis, the terms below,
any embargo sentence found on the page, the publisher's music flag and any music sentence on the page.

| Publisher | Basis | What it allows us to rely on | Credit on screen | Excerpts only | Trailer music |
|---|---|---|---|---|---|
| Square Enix | press grant | Square Enix press site grant for editorial use of its press assets in news coverage | yes | no | no flag |
| Ubisoft | per-kit editorial terms | each press kit states its own editorial terms; the kit's terms page is the basis for that asset | yes | no | **flagged separately**: read the kit's music note before using the sound |
| SEGA | per-kit editorial terms | each press release or kit states its terms; the release that links the file is the basis | yes | no | no flag |
| Bandai Namco Entertainment | per-kit editorial terms | each press kit states its terms | yes | no | no flag |
| Nintendo | fan guidelines | Nintendo's Game Content Guidelines; **not a press licence** | yes | **yes**: short excerpts | no flag |
| Epic Games | fan guidelines | Epic's fan content policy; **not a press licence** | yes | **yes**: short excerpts | no flag |
| Capcom | unreviewed | not yet reviewed; official trailers used editorially, entry pending | yes | no | **flagged separately** |
| Electronic Arts | unreviewed | not yet reviewed; official trailers used editorially, entry pending | yes | no | **flagged separately** (licensed tracks) |
| Sony Interactive Entertainment | unreviewed | not yet reviewed; PlayStation Blog and gmedia clips used today, entry pending | yes | no | no flag |
| Xbox (Microsoft) | unreviewed | not yet reviewed; Xbox Wire press assets, entry pending | yes | no | no flag |
| any publisher not listed | unreviewed | prepared only from steps 1 to 3, flagged `rights_review: true` in the manifest; reviewed before use | yes | yes | check |

"unreviewed" rows: the build desk has no stated term on file. The prepare service still prepares their trailers (it
publishes nothing), and the manifest says `rights_review: true` so the brief sees it. Mohammad or the advisor fills in
the basis; the build desk changes the row and rights.yaml together.

### Acquisition order the service follows (a rule)

1. Publisher-issued file: an MP4 linked from the publisher's own release or news page, on its own host (or a generic
   CDN the publisher's own page links). Ubisoft and SEGA publish real MP4 links.
2. Public press asset: the publisher's press-asset site, one level from the page (Square Enix press hubs).
3. Steam store data: each trailer is a streaming manifest ffmpeg reads with no login.
4. Authorised live feed (Twitch via streamlink): not wired into prepare; live shows stay with event capture.
5. YouTube, a bounded fallback only: one attempt, no retry loops, never cookies. Off in prepare until Mohammad answers
   the 28 Sep rule (media toolbox E2).

Never: logins, cookies, third-party downloaders, social-media rippers, reposts or fan uploads.

## 2. Tools and models the prepare service uses

| Tool | Version pinned | Licence | Used for | Where it lives |
|---|---|---|---|---|
| PySceneDetect (`scenedetect`) | 0.6.6 | BSD-3-Clause | shot boundaries (AdaptiveDetector) | prepare venv |
| OpenCV (`opencv-python-headless`) | 4.11.0.86 | Apache-2.0 (OpenCV 4.5+) | decoding frames, DNN runtime, YuNet API | prepare venv |
| YuNet face detector, `face_detection_yunet_2023mar.onnx` | sha256 8f2383e4... | MIT (OpenCV Zoo) | faces and a side-on (yaw) proxy | model cache, never git |
| NanoDet-Plus m 416, `object_detection_nanodet_2022nov.onnx` | sha256 4b82da99... | Apache-2.0 (OpenCV Zoo) | people, vehicles, animals (replaces YOLOv8 here) | model cache, never git |
| librosa | 0.11.0 | ISC | beat grid per music bed and per trailer | prepare venv |
| numpy | 2.2.6 | BSD-3-Clause | everything numeric | prepare venv |
| PyYAML | 6.0.2 | MIT | reading rights.yaml | prepare venv |
| tesseract-ocr | system package | Apache-2.0 | burnt-in text (PaddleOCR, Apache-2.0, later: media toolbox E3) | apt (already on the server for render checks) |
| ffmpeg / ffprobe | system package | LGPL-2.1+ / GPL build | probe, decode check, stream copy from Steam | apt (already on the server) |
| streamlink | not installed by prepare | BSD-2-Clause | step 4, live feeds (stub; event capture installs it today) | runner venv |
| MERL Cocktail Fork | commit 19b3de8 | MIT (code and weights) | optional audio split, PREPARE_SPLIT=on | `$DXB_CACHE/cocktail-fork/<sha>` as render-live installs it |

Model files come only from the official OpenCV Zoo mirrors (huggingface.co/opencv, then GitHub's LFS media host for
opencv/opencv_zoo), checked against the sha256 above before use.

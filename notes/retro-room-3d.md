# The den built in code (11 Oct 2026)

Mohammad sent three reference images for the "on this day" Reels (a warm 80s
den with the set inside it, a Game Boy in the hand, a Game Boy on cartridges)
and then the "Lights on, one by one" prompt pack: a scene built entirely in
code with Claude, rendered frame by frame. The references themselves could
not be used (AI renders of unknown origin full of licensed posters, and a
collector's photo), so the pack's method is applied instead: every model,
texture and light is ours, and nothing in the frame is anyone's property.

## What is where

- `templates/room3d/room.html`: the scene, three.js 0.160 through a local
  copy of `three.module.js` (fetched from jsDelivr, not committed; MIT).
  `window.renderAt(t)` draws the moment t with no dependence on the wall
  clock or previous frames; all randomness from one seeded generator
  (mulberry32, seed 7); every motion (lamp flicker, the set's own flicker,
  the LED, dust) runs a whole number of cycles per 10 s loop.
  `window.screenQuad()` returns the screen's four corners in frame pixels.
  `?t=3.3` freezes a moment, `?scale=2` renders at 2160x3840.
- `templates/room3d/render.mjs`: Playwright in headless Chromium
  (SwiftShader), one PNG per frame, then ffmpeg to `room-loop.mp4`
  (H.264, CRF 16) and `quad.json`. About 1.6 s a frame at 1080x1920.
  `node render.mjs <out> 24 8 1` for the loop, `... 1 2.5` for one frame.
  Needs `node_modules -> /opt/node22/lib/node_modules` in the folder.
- `templates/assets/retro/room3d-loop.mp4` and `room3d-quad.json`: the
  render retro.py uses. `retro.render(dict(..., scene='room3d'), out)`
  loops the video under the picture, warps the footage onto the quad
  (ffmpeg `perspective`), and lays the console-coloured scrims over the
  title band and the sheet.

## The scene, in numbers

Camera at (0.05, 1.02, 3.2) looking at (0, 0.70, 0), fov 50, 9:16. A
wood-panelled back wall at z -0.62, plank floor, a dark burgundy rug with
a small diamond pattern. The set: 0.82 x 0.64 x 0.5 wood case, a 0.64 x
0.48 screen on an open wooden cabinet 1.1 wide with a grey console box and a
black tape deck (green LED) inside. A floor lamp at x 0.58 (warm point and
spot lights, 2048 PCF shadows), a window with slats at x -0.78 (cool
directional light from outside), two shelves of plain coloured boxes above
the set, two geometric prints of our own, a plant, a controller on the
rug, a vignette plane in front of the camera. ACES tone mapping, exposure
0.92. Cool outside, warm inside.

## Fixes folded in after the first frames

Too bright and toy-like: ambient 0.35 to 0.12, moon 0.9 to 0.5, exposure
1.05 to 0.92, rug darkened and its diamonds halved, the night deepened.
A black slab for a set: wood case, silver bezel (narrowed on the second
pass), dark inset, matte tube. A closed black block for a stand: an open
cabinet built from five slabs so the console shows. Dust read as snow:
120 motes at 0.006, opacity 0.35, kept in the lamp's cone. The lamp cut
by the frame edge: moved to x 0.58, smaller shade.

## Checks before a loop goes out

- renderAt(8) matches renderAt(0) (whole cycles only).
- The quad in `quad.json` matches the render it shipped with.
- Frames reviewed as an art director: no text over the picture, the set's
  picture inside the bezel, nothing cut by the frame edge.

## The photoreal den (Blender Cycles, 11 Oct 2026)

Mohammad: "The coded one look good as a first try. How do we make it look
photorealistic". The same den, path-traced instead of rasterised.

- `templates/room3d/den_cycles.py <out.png> [scale] [samples] [pass]`, run
  with the `bpy` wheel (Blender 5.0.1 as a Python module, in
  `/root/blender-env/venv`, Python 3.11; `pip install bpy` in a new container).
  Writes the frame and `<out>.quad.json`, the screen's corners in
  1080x1920 frame pixels from the camera's own projection.
- Models and textures: Poly Haven, all CC0, fetched to `/root/den-assets/dl`
  with `fetch.py <ids>` (glTF 1k) and `tex.py <id:res>` (diffuse, normal,
  roughness). Not committed: they are large and re-fetchable.
  Models: Television_01, modern_wooden_cabinet, portable_cassette_player,
  potted_plant_02, book_encyclopedia_set_01, boombox. Textures:
  dark_paneled_wood (walls, shelf), herringbone_parquet (floor),
  floral_jacquard (rug, tinted brown).
- Brand marks: Television_01 carries a "VTECH" plate on the front and the
  side. Both are painted out of its diffuse texture after every fetch
  (median colour of the plate beside it); check any new model for logos,
  labels and screen text before it goes in a frame.
- Our own pieces: the floor lamp (brass pole, linen shade with a
  translucent mix), the wall shelf, the venetian blind (slats 1 m in front
  of a 4 mm spot, out of shot, so the stripes stay sharp on the wall) and
  the emissive plane over the tube that the footage replaces.
- Light: warm point inside the shade (excluded from the moon by light
  linking, so the blind's stripes never land on the glowing shade), an area
  light in front of the screen facing the room (it first faced the set and
  bleached its bezel), the cool moon spot, a faint warm fill. AgX, Medium
  High Contrast. Camera 45 mm, f/4 on the screen, 2.6 m back.
- Times on 4 CPU cores: half size at 32 samples about 40 s; full size at
  128 samples about 10 minutes.
- `retro.render(dict(..., scene='room3d', room3d='cycles'), out)` uses
  `assets/retro/den-cycles-loop.mp4` and `den-cycles-quad.json`. The first
  loop is the still held for 8 s; lamp and set flicker come once the look
  is approved (render the lamp and TV states and blend them per frame).

## Next: rooms per era (Mohammad, 12 Oct 2026, parked for news)

One room per era, colourful and fun. The 70s den stays for Atari only. For
80s and 90s consoles, the mood is his two references in `notes/refs/`
(mood only, not for use: they carry film posters and brand marks). Build it
the same way as `den_cycles.py`: a kid's bedroom with a shag rug, a bean
bag, posters of our own wall to wall, shelves of unbranded tapes and
cartridges, a desk lamp and a lava lamp, a starry ceiling, a cereal bowl
and a controller in front. Warm practical lights against the TV's glow.

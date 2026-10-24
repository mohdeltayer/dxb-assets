// Digital Lounge motion kit (pilot, advisor memo 24 Oct 2026). One set of movements for every Reel; game skins
// change colours and plate shapes through kit.css tokens, never these timings. Every animation is under 0.5 s,
// nothing moves while text is being read, and the text is readable the moment it settles. No loops, no shake.
// Each block adds itself to a paused GSAP timeline `tl` at time `t` and returns the times its sound blips land on.

const KIT = {
  // the play triangle (pointing right, as in the mark) as four points so it can open into a rectangle:
  // top-left, tip, tip, bottom-left -> top-left, top-right, bottom-right, bottom-left
  TRI_SMALL: 'polygon(46% 44%, 54% 50%, 54% 50%, 46% 56%)',
  TRI: 'polygon(28% 16%, 82% 50%, 82% 50%, 28% 84%)',
  RECT: 'polygon(0% 0%, 100% 0%, 100% 100%, 0% 100%)',

  // f. card transition / a. photo box opening: a quick wipe through the play triangle (0.35 s)
  triWipeIn(tl, el, t) {
    gsap.set(el, { clipPath: KIT.TRI_SMALL, opacity: 0 });   // hidden until its wipe, frame 0 included
    tl.set(el, { clipPath: KIT.TRI_SMALL, opacity: 1 }, t);
    tl.to(el, { clipPath: KIT.TRI, duration: 0.14, ease: 'power2.out' }, t);
    tl.to(el, { clipPath: KIT.RECT, duration: 0.21, ease: 'power3.inOut' }, t + 0.14);
    return [t];
  },
  triWipeOut(tl, el, t) {
    tl.to(el, { clipPath: KIT.TRI, duration: 0.14, ease: 'power3.in' }, t);
    tl.to(el, { clipPath: KIT.TRI_SMALL, opacity: 0, duration: 0.12, ease: 'power2.in' }, t + 0.14);
    return [];
  },

  // a. photo box: triangle wipe, a thin frame draws round it, the name plate slides in (about 0.6 s in all,
  // each piece under 0.35 s). `frame` is an SVG rect with pathLength 1000.
  photoBox(tl, { box, frame, plate }, t) {
    const s = KIT.triWipeIn(tl, box, t);
    tl.fromTo(frame, { strokeDashoffset: 1000 }, { strokeDashoffset: 0, duration: 0.3, ease: 'power2.inOut' }, t + 0.18);
    tl.fromTo(plate, { y: 26, opacity: 0 }, { y: 0, opacity: 1, duration: 0.25, ease: 'power3.out' }, t + 0.32);
    return s.concat([t + 0.32]);
  },
  photoBoxOut(tl, { box, frame, plate }, t) {
    tl.to(plate, { opacity: 0, duration: 0.1 }, t);
    tl.to(frame, { opacity: 0, duration: 0.1 }, t);
    return KIT.triWipeOut(tl, box, t + 0.04);
  },

  // b. number: counts up (0.45 s) with a soft tick, then settles with a small pop (scale 1.04, under 5%)
  countUp(tl, { el, wrap }, t, to, decimals = 0) {
    const o = { v: 0 };
    const show = () => { document.querySelector(el).textContent = o.v.toFixed(decimals); };
    tl.set(o, { v: 0, onUpdate: show, onComplete: show }, t);
    tl.to(o, { v: to, duration: 0.45, ease: 'power2.out', onUpdate: show, onComplete: show }, t);
    tl.to(wrap, { scale: 1.04, duration: 0.08, ease: 'power1.out' }, t + 0.45);
    tl.to(wrap, { scale: 1, duration: 0.12, ease: 'power1.inOut' }, t + 0.53);
    return [t + 0.05, t + 0.15, t + 0.27, t + 0.45];          // ticks, then the settle
  },

  // c. bar: fills like an XP bar (0.45 s) with one short glint at the end (0.25 s)
  xpBar(tl, { fill, glint }, t, pct) {
    tl.fromTo(fill, { width: '0%' }, { width: pct + '%', duration: 0.45, ease: 'power2.out' }, t);
    tl.fromTo(glint, { xPercent: -120, opacity: 0.9 }, { xPercent: 420, opacity: 0, duration: 0.25, ease: 'power1.in' }, t + 0.45);
    return [t + 0.45];
  },

  // d. chip: presses in like a controller button with one small bounce (0.3 s)
  chipPress(tl, el, t) {
    tl.fromTo(el, { scale: 1.12, y: -6, opacity: 0 }, { scale: 0.94, y: 2, opacity: 1, duration: 0.12, ease: 'power2.in' }, t);
    tl.to(el, { scale: 1.02, y: 0, duration: 0.1, ease: 'power2.out' }, t + 0.12);
    tl.to(el, { scale: 1, duration: 0.08, ease: 'power1.inOut' }, t + 0.22);
    return [t + 0.12];
  },

  // e. record or milestone: an "unlocked" banner slides in from the top (0.3 s), holds about 1.5 s, slides out
  unlockBanner(tl, el, t, hold = 1.5) {
    tl.fromTo(el, { y: -160, opacity: 0 }, { y: 0, opacity: 1, duration: 0.3, ease: 'back.out(1.4)' }, t);
    tl.to(el, { y: -160, opacity: 0, duration: 0.25, ease: 'power2.in' }, t + 0.3 + hold);
    return [t, t + 0.12];
  },
};

# How the evolution drawings are made

The 21 drawings in `animations/motifs/` are generated: each has a Python
script here, `NN-slug.py`, that draws it with `pen.py` and writes
`../NN-slug.svg`. Run a script from this folder (`python3 12-quastenflosser.py`)
to rebuild its drawing. A drawing made by editing an older SVG keeps that SVG
in `base/` and its script reads it from there, so it can be rerun.

Drawings made before October 19 have no script here (theirs were lost); their
SVGs are kept as they are.

## The look

Maxim: "use a sketchy style, the dragonfly is a very good example". The set reads
as one hand: pen-and-ink natural-history engraving, black lines on ivory.

- Stroke-only SVG, viewBox 0 0 1000 1000, black strokes 0.6 to 3 wide, round caps.
  No fills: dark areas are hatching, solid spots are tight spirals (`pen.blot`).
- Contours heavier (about 1.6 to 2.6), inner detail lighter (1 to 1.4), hatching
  and fur fine (0.6 to 0.9).
- Hatching lines at least 5 units apart; they follow the form where they can.
- Roughly 800 to 4000 strokes, 15 000 to 55 000 units of ink. The engine lays at
  most 52 000 dashes per drawing (`pen.report()` estimates them).
- The subject fills most of the square (about 700 to 900 units across) and sits
  near its middle.
- Subjects face right as drawn. On the page drawings 10 to 20 are mirrored to
  face the text (`pen.save(path, mirror=True)`); 01 to 09 and 21 are not.

## How the page shows them

`animations/sketch.js` lays tiny dark yellow dashes along every stroke, more,
thicker and darker where a stroke is heavier, and streams them from drawing to
drawing. Maxim's laptop is a standard (1x) screen, where texture that looks
clean at 2x can turn into dark scribble, so every drawing is judged at 1x too.

## Rendering for review

    node animations/motifs/tools/render.mjs <out dir> animations/motifs/NN-slug.svg

writes `NN-slug.png` (pen lines, 1000 px, facing right), `NN-slug-1x.png` and
`NN-slug-2x.png` (the engine's dashes in a 700 px box on a standard and a sharp
screen). `--sheet` adds a contact sheet of all the drawings given, as faced.

## Passing

A drawing passes when an independent reviewer (not its maker) scores it at
least 8 of 10 on each of: clear at a glance, accurate, of a piece with the
passed set. Previews of passed drawings are kept in the project's shared folder
under `website/motifs/previews-v5/`.

# Anatomy figure

`../adversarialeval-anatomy.png` is drawn with the **Anatomy** skill
([wheresryan22/anatomy](https://github.com/wheresryan22/anatomy), MIT): an isometric figure
of an invented machine whose working is the concept.

**The object:** a dimple-key test bench. Two keys look identical but for one dimple: a sound
answer, and a plausible but wrong one. A shortcut judge compares length and outline and
can't tell them apart. The lock checks every pin. With the wrong key in the channel, pin 4
(the one lit part) rides 2.7 proud of the shear line, so the turn knob stays locked. The
numbers come from `MODEL` in `build.mjs` and the project's verified reports.

The palette is ink on paper: black outlines, warm-grey shading, and one orange accent on the lit part (pin 4). The README's pipeline diagram uses the same colours.

**Rebuild:** clone wheresryan22/anatomy, copy `build.mjs` to
`examples/adversarialeval/build.mjs`, and run `node build.mjs`. It writes
`adversarialeval-anatomy.html`; screenshot that at 1600×900, device scale 2.

# Defender — Uxn / Varvara

A horizontal shoot-'em-up for the [Varvara/Uxn](https://wiki.xxiivv.com/site/uxntal.html)
platform, ported from the TIC-80 Forth cart `perso/demo90s.fth` (its "Defender"
shooter mode). The ship, the two enemy types and the projectile are the same
assets, re-encoded from TIC-80 4bpp sprites to Varvara 1bpp.

```
make            # assemble defender.rom
make run        # assemble + run with uxn11 (X11)
make run2       # assemble + run with uxn2 at zoom x2
make clean
```

The ROM is assembled headless with `drifloon`:

```sh
cat defender.tal | ../uxncli ../drifloon.rom > defender.rom
```

## Controls

| Key                | Action                                          |
|--------------------|--------------------------------------------------|
| Arrow keys         | Move the ship                                   |
| Left Ctrl (A) / `a`| Start / restart                                 |
| Left Alt (B) / `x` | Fire (also starts from the title screen, not on game over) |

`a` and `x` are plain letter-key aliases read from `Controller/key` (the
raw-key path every uxn emulator already supports for text input) — no
emulator change needed, they only work because `defender.tal` listens for
them (see `@on-controller` / `extra-btn` in the source).

The ship moves freely over the **full width and full height** of the screen
(the TIC-80 original was boxed into a middle band for its demo overlay; that
constraint is gone here). Enemies likewise spawn across the whole height.

Firing plays a short "pew", and every collision (enemy destroyed or ship hit)
plays an impact sound.

## Rules

- Fire projectiles to destroy enemies; each kill is **+1 score**.
- Enemies arrive from **both sides**:
  - **Type 1** (green, frame-animated) is flipped to face its travel direction.
  - **Type 2** (orange, colour-animated diamond) is direction-agnostic.
- Colliding with an enemy costs **one life bar** (4 total). While hit the ship
  flashes its damage frames and is briefly invulnerable (`HIT-DUR` frames).
- At **0 lives** the game ends; press A to restart.

## Defender mode (score ≥ 20)

Reaching 20 points latches **Defender mode** (a flashing `DEFENDER` label
appears in the HUD):

- The ship gains a **facing**. Tapping the **backward** arrow (opposite to the
  facing) reverses it — and flips the **starfield scroll direction**. Shots then
  fire in the new facing direction.
- Holding the **forward** arrow accelerates: the starfield scroll speeds up.

## Implementation notes

- **Screen vector** drives the per-frame loop (update + redraw); the whole
  screen is cleared each frame with a fill-pixel (`#80 .Screen/pixel`).
- **1bpp sprites**, drawn transparent via blend nibbles `05`/`0a`/`0f`
  (colours 1/2/3 = white / green / orange over a dark-blue background).
  The blend table and the `0x80` two-bpp bit were read from `../src/uxn2.c`.
- Fixed-size object pools (no allocation): 8 shots, 8 enemies, 24 stars, each a
  set of parallel arrays. Loop indices live in the `li`/`lj` bytes so nested
  loops (shot×enemy collision) don't clash.
- Positions are 16-bit; off-screen despawn uses a single unsigned `x > 240`
  test that also catches leftward underflow (wrapped to a large value).
- An 8×8 bitmap **font** (digits + the letters used in the HUD) is embedded at
  `@font`; `draw-str` / `draw-number` render the HUD and screens.
- Sprite provenance: TIC-80 tiles `#33..#41` (ship idle/thrust/damage + shot),
  `#48/#49` (enemy 1), `#50/#51` (enemy 2), reduced to 1bpp silhouettes.
- **Sound**: noise comes from a 512-byte random buffer `@noise` — because it is
  **larger than `0x100`** the Audio device plays it in sample mode (sequential
  bytes), so it reads as noise, not a pitched tone; `@wave-saw` is a 32-byte
  single cycle (≤ `0x100`, pitched). The four channels are used in parallel:
  - **`sfx-fire`** layers two voices that mix in the output — noise on Audio0
    (`|30`) + saw on Audio1 (`|40`).
  - **`sfx-hit`** (enemy destroyed) on Audio2 (`|50`).
  - **`sfx-boom`** (ship hit) on Audio3 (`|60`) — lower pitch, heavier.

  A sound is triggered by writing the pitch port; duration comes from the ADSR
  nibbles — the **release nibble must be non-zero** (or, more precisely, A+D+S+R
  must be non-zero) or the envelope never ends. All values were dialled in with
  `sndtest.tal`. Needs an emulator with audio (e.g. `uxn2`).

## Tuning the sounds (`sndtest.tal`)

`sndtest.tal` is a small interactive bench to design the SFX by ear, then copy
the values into `defender.tal`:

```sh
make snd          # build + run sndtest.rom under uxn2 (needs audio)
```

| Key | Action |
|-----|--------|
| Up / Down    | select a field |
| Left / Right | change it (auto-plays the sound) |
| A (LeftCtrl) | play the current sound |
| B (LeftAlt)  | print `PITCH= ADSR= VOL= WAVE=` to the terminal |

Fields: **WAVE** (sine / square / saw / tri / noise), **PITCH** (0–107), the four
**ADSR** nibbles (ATK DEC SUS REL — *REL must be > 0* or the envelope never ends),
and **VOL** (0–15). The bottom line and the `B` printout give the exact hex to
drop into `sfx-fire` / `sfx-hit`. Each audio port is one lever — see the
implementation notes above for what each one changes.

## Editing the sprites (PNG round-trip)

`tools/spritesheet.py` round-trips the sprites between `defender.tal` and an
editable `sprites.png`:

```sh
python3 tools/spritesheet.py export   # defender.tal -> sprites.png
# ...edit sprites.png in an image editor (one logical pixel = a 16x16 block)...
python3 tools/spritesheet.py import   # sprites.png  -> patches defender.tal
make                                  # reassemble
```

Sprites are 1bpp: paint a pixel in a bright colour to turn it **on**, leave it
dark to turn it **off** (the faint grid lines stay near the background colour and
read as off). The export/import is lossless. Note `en2a`/`en2b` are currently the
same silhouette (they differed only by colour in the TIC-80 original) — editing
them is a good way to give enemy 2 a real two-frame animation.

## Files

```
defender.tal    source (Uxntal)
defender.rom    assembled ROM
Makefile
```

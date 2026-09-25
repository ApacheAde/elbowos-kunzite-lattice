# Kunzite Lattice

Full-colour Python 3 neon tetromino-well arcade for [ElbowOS](https://x.com/ElbowOS).

Drop kunzite, orchid, gold and mint crystals into an 10×18 lattice.
Rotate, slide, hard-drop. Full rows bloom and vanish.

← → move · ↑ / X rotate · ↓ soft-drop · Space hard-drop · R reset

## Play

```
pip install -r requirements.txt
python3 kunzite_lattice.py --play
```

Needs Python 3.10+ and a desktop window (pygame + SDL).

## Record a 9:16 reel

```
python3 kunzite_lattice.py --record
```

Writes `/home/workdir/artifacts/KUNZITE_LATTICE_ElbowOS.mp4`
(override with `ELBOWOS_MP4`). Headless via `SDL_VIDEODRIVER=dummy`.

- Featured account: https://x.com/ElbowOS
- Drive reel: https://drive.google.com/file/d/1fpgbPPfgtu91Zoi0_UBYo_2-g11iz2vk/view

MIT. Original code. Not a Nintendo ROM or emulator.

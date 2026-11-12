# coolest-art-entry

[![make.fun · coolest-art-01](https://make.fun/badge/coolest-art-01.svg)](https://make.fun/bounty/coolest-art-01?utm_source=github&utm_medium=readme&utm_campaign=coolest-art-01)
[![rank](https://make.fun/badge/coolest-art-01/ahmadcrypto/coolest-art-entry/rank.svg)](https://make.fun/bounty/coolest-art-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=coolest-art-01)
[![reward](https://make.fun/badge/coolest-art-01/ahmadcrypto/coolest-art-entry/reward.svg)](https://make.fun/bounty/coolest-art-01?utm_source=github&utm_medium=readme&utm_campaign=coolest-art-01)

An original generative space artwork: a copper-banded ringed planet drifting
through a teal and violet nebula, with a starfield and a crescent moon. The
art is generated procedurally by `generate.py` (numpy + Pillow, fixed seed,
fully deterministic); the entry itself is `main.py`, which copies the finished
`art.png` to `/output/entry.png` using only the Python standard library.

## Run it

```sh
python3 main.py
```

This writes `/output/entry.png` (896x896 PNG, 946,420 bytes) and verifies
the copy byte for byte. To regenerate the artwork from scratch:

```sh
python3 generate.py
```

---

Entered on [make.fun](https://make.fun/?utm_source=github&utm_medium=readme&utm_campaign=coolest-art-01) · AI agents build software for cash rewards

# Cataclysm: Dark Days Ahead (Asciiverse packaging)

CleverRaven's post-apocalyptic survival roguelike, stable 0.I-1, packaged
for the Asciiverse catalog and as system packages, terminal (curses) build
only. Not our code: keep changes small and list every one in PATCHES.md.

- History: the first commit is upstream's 0.I-1 tree as one import commit
  (tag `0.I-1`), not upstream's ~13 GB history. `upstream` points to
  github.com/CleverRaven/Cataclysm-DDA with `--no-tags`: never fetch it. A
  new release is imported the same way and our commits rebased onto it
  (PATCHES.md, "Import"). `origin` is github.com/theasciiverse/cataclysm-dda.
- Branch `asciiverse` = the import plus our commits.
- Release: tag `v0.I-1-av.<n>` and push it (`.github/workflows/release.yml`;
  upstream's workflows are removed). Package versions are 0.I.1.
- Local static build, gently (it is a big C++ build): `docker run --rm
  --cpus=6 --memory=16g -v "$PWD":/src -w /src alpine:3.22 sh
  asciiverse/build.sh`, then `sh asciiverse/stage.sh`. Files come out
  root-owned; chown them. `JOBS` defaults to 6.
- Data: read-only `data/` and `share/locale/` beside the start script
  `cataclysm-dda`, or under `/usr/share/cataclysm-dda`; player files in
  `$XDG_DATA_HOME/cataclysm-dda` (`src/path_info.cpp`).
- With `LANG=C.UTF-8` the game asks for a language at every start; with a
  real locale it does not.
- Preview: `python3 asciiverse/record-preview.py` after build (needs pyte).

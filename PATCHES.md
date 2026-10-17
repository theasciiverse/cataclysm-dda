# Changes from upstream

This is the Asciiverse packaging of Cataclysm: Dark Days Ahead by
CleverRaven and contributors (from Whales' Cataclysm; CC BY-SA 3.0, see
LICENSE.txt), stable release 0.I-1 "Ito-1" (2026-09-20), terminal
(curses) build.

## Import: one commit, not upstream's history

Upstream's git history is about 13 GB (a full clone on 2026-10-17;
122,604 commits lead to 0.I-1), more than GitHub takes in sensible
pushes (2 GB per push) and more than David wants kept anywhere. So
this repository does not carry it, a deliberate exception to the house
rule of an `upstream` remote with history:

- The first commit, "Cataclysm: Dark Days Ahead 0.I-1, unmodified", is
  upstream's 0.I-1 source tree as one commit, credited to "CleverRaven and
  contributors", with the upstream URL, tag and commit
  (`7b2efa5cea38e4d4d97dd0e63b28b9148623da59`) in its message. It is tagged
  `0.I-1`.
- Everything after it is ours, listed below.
- Remote `upstream` (github.com/CleverRaven/Cataclysm-DDA) is set with
  `--no-tags`. Never fetch from it: that pulls the whole history in.

To move to a later stable release: download that release's source
(`https://github.com/CleverRaven/Cataclysm-DDA/archive/refs/tags/<tag>.tar.gz`),
replace the tree with it in a new commit on top of the current import
(same message form, credited the same way, tagged with the upstream tag),
then rebase our commits onto it and update `VERSION=` in
`asciiverse/build.sh`.

## Code

- `src/third-party/flatbuffers/util.h`: musl has no `strtoll_l` or
  `strtoull_l`, so the static Linux build did not compile; on musl the
  plain `strtoll` and `strtoull` are used, which are locale independent
  there (musl's integer parsing ignores the locale). `strtod_l` and
  `strtof_l` stay.
- `src/path_info.cpp`: with `USE_XDG_DIR=1` all of a player's files go to
  `$XDG_DATA_HOME/cataclysm-dda` (default `~/.local/share/cataclysm-dda`):
  saves, memorials, achievements and templates as upstream already did,
  and now also options, keymap and logs, in its `config/` folder (upstream
  put those in `$XDG_CONFIG_HOME/cataclysm-dda`). macOS follows the same
  setting instead of `~/Library/Application Support/Cataclysm`.

## Packaging (new files)

- `asciiverse/build.sh`: static Linux build in Alpine (musl, ncursesw,
  zlib), macOS per architecture (`CC_ARCH`) against the system ncurses.
  Upstream's Makefile with `TILES=0 SOUND=0 RELEASE=1 LTO=0 PCH=0
  BACKTRACE=0 LOCALIZE=1 LANGUAGES=all USE_XDG_DIR=1`; tests, astyle and
  the JSON lint off; warnings not errors; the version string fixed to
  `0.I-1`. Builds the `cataclysm` program and the translations only (no
  `zzip` save tool).
- `asciiverse/stage.sh`: gathers what ships: the program, the start
  script, the data upstream's `make install` copies for a terminal build,
  the translations in `share/locale` and the licences.
- `asciiverse/cataclysm-dda`: the start script, which av launches and the
  packages put on PATH. It finds the data beside itself (an av install) or
  in `/usr/share/cataclysm-dda` (the packages, which put the program in
  `/usr/lib/cataclysm-dda`) and passes it with `--basepath`. The game reads
  translations from `<basepath>/share/locale`, hence that folder. The
  game also keeps a cache of its parsed data in `data/cache` when it can
  write there (an av install); it is rebuilt when missing, and a
  read-only data folder (the packages) simply goes without it. av keeps
  files a new release does not ship when it updates, so the script stamps
  the cache with a checksum of the game binary
  (`data/cache/.asciiverse-build`) and drops the cache when the binary has
  changed; otherwise the game would warn about "stale game data" after an
  update. The script follows symlinks to itself, so it also works through
  av's link in `~/.local/bin` (added in v0.I-1-av.2).
- `asciiverse/nfpm.yaml`: .deb, .rpm, .apk and Arch packages; no desktop
  file. Package versions write 0.I-1 as 0.I.1 (rpm and Arch versions
  cannot hold a dash).
- `asciiverse/record-preview.py`: records the catalog preview.
- `.github/workflows/release.yml`: builds all of it on a tag. Upstream's
  own workflows (CleverRaven's CI, release and housekeeping jobs, 35
  files) are removed: they are for CleverRaven's repository and would run
  here on every push.

## Not built

- Tiles, sound and the SDL frontend; the Android, Emscripten, MSVC and
  CMake builds (left in the tree, unused).
- Windows: upstream's Windows releases are the SDL tiles build, and its
  non-tiles Windows code (`src/wincurse.cpp`) draws in a window of its
  own, not in the console. A Windows console build would need the ImTui
  ncurses backend built against PDCurses or a Windows ncurses; not tried.

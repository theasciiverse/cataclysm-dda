#!/bin/sh
# Builds Cataclysm: Dark Days Ahead's terminal (curses) game and its
# translations. Linux: run inside alpine:3.22 for a fully static binary;
# macOS: run on the runner, with CC_ARCH set to x86_64 or arm64.
#   docker run --rm -v "$PWD":/src -w /src alpine:3.22 sh asciiverse/build.sh
# Leaves cataclysm in the repository root and the compiled translations in
# lang/mo. Players' files go to $XDG_DATA_HOME/cataclysm-dda (USE_XDG_DIR,
# see PATCHES.md); the read-only data is found through --basepath, which
# asciiverse/cataclysm-dda passes. No tiles, no sound, no SDL.
# JOBS sets the number of parallel compiles (default: 6, so a big build does
# not exhaust memory on the machine running it).
set -eu
jobs=${JOBS:-6}
if [ -f /etc/alpine-release ]; then
  apk add --no-cache build-base linux-headers pkgconf ncurses-dev ncurses-static \
    zlib-dev zlib-static gettext >/dev/null
  export LDFLAGS="-static"
  native=""
else
  export CXXFLAGS="-arch $CC_ARCH" LDFLAGS="-arch $CC_ARCH"
  native="NATIVE=osx"
fi
# The version shown in the game is the upstream release; GIT_DIR keeps the
# Makefile from replacing it with our commit's hash. Warnings are not errors
# here (upstream's -Werror is for its own CI compilers), debug symbols and
# backtraces are off (musl has no execinfo), and tests, astyle and the JSON
# lint are skipped: none of it changes the game.
GIT_DIR=/nonexistent make -j"$jobs" cataclysm localization $native \
  VERSION=0.I-1 TILES=0 SOUND=0 RELEASE=1 LTO=0 PCH=0 BACKTRACE=0 \
  LOCALIZE=1 LANGUAGES=all USE_XDG_DIR=1 \
  TESTS=0 ASTYLE=0 LINTJSON=0 DEBUGSYMS= WARNINGS="-Wall -Wextra"
strip cataclysm

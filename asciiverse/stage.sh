#!/bin/sh
# Gathers what ships into stage/, after asciiverse/build.sh: the game, its
# start script, the read-only data upstream's `make install` installs for a
# terminal build (data/core, font, json, mods, names, raw, motd, credits,
# title, plus changelog.txt and fontdata.json), the compiled translations in
# share/locale (where the game looks for them beside --basepath) and the
# licences. No gfx, sound or desktop files. The av archive is stage/ as it
# is; nfpm.yaml installs the same files under /usr.
set -eu
rm -rf stage
mkdir -p stage/data stage/share
cp cataclysm asciiverse/cataclysm-dda stage/
for d in core font json mods names raw motd credits title; do
  cp -R "data/$d" stage/data/
done
cp data/changelog.txt data/fontdata.json stage/data/
cp -R lang/mo stage/share/locale
cp README.md LICENSE.txt LICENSE-OFL-Terminus-Font.txt LICENSE-Apache-Robot-Font.txt stage/

#!/usr/bin/env python3
"""Records asciiverse/cataclysm-dda.cast, the catalog preview, at 100x30
(hub/RECORDING.md). After asciiverse/build.sh and asciiverse/stage.sh, from
the repo root, with pyte installed:
    python3 asciiverse/record-preview.py

It sets up an install folder the way av does from stage/ (the program, the
start script, data/ and share/locale/), starts a game through "Play Now! (Default
Scenario)" in a throwaway home folder, explores the start area for about
half a minute by walking to the nearest unexplored edge of the map, looks at
the overmap, then saves and quits. The screen is read through pyte, so each
key waits for what it answers to. Scenario, character and map are random, so
takes differ; record again for a better one."""
import fcntl, os, pty, random, select, shutil, struct, sys, tempfile, termios, time
from collections import deque

import pyte

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAST = os.path.join(ROOT, "asciiverse", "cataclysm-dda.cast")
COLS, ROWS = 100, 30
ENTER, ESC, TAB = b"\r", b"\x1b", b"\t"
DOWN = b"\x1bOB"

# ncurses draws runs of one character with REP (CSI n b), which pyte does not
# know; without this a wall drawn as "#" plus REP would read as one "#"
_draw = pyte.Screen.draw
def _draw_remembering(self, data):
    if data:
        self.last_char = data[-1]
    _draw(self, data)
def _repeat_last(self, n=1, *rest, **kw):
    if getattr(self, "last_char", None):
        _draw(self, self.last_char * max(1, n))
pyte.Screen.draw = _draw_remembering
pyte.Screen.repeat_last = _repeat_last
pyte.Stream.csi = dict(pyte.Stream.csi, b="repeat_last")

tmp = tempfile.mkdtemp(prefix="cdda-rec-")
home = os.path.join(tmp, "home")
inst = os.path.join(tmp, "game")
os.makedirs(home)
os.makedirs(inst)
for f in ("cataclysm", "cataclysm-dda"):
    shutil.copy2(os.path.join(ROOT, "stage", f), inst)
for d in ("data", "share"):
    os.symlink(os.path.join(ROOT, "stage", d), os.path.join(inst, d))

env = {"PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": home, "USER": "player",
       "LOGNAME": "player", "TERM": "xterm-256color", "COLORTERM": "truecolor",
       "LANG": "C.UTF-8"}
screen = pyte.Screen(COLS, ROWS)
stream = pyte.ByteStream(screen)

pid, fd = pty.fork()
if pid == 0:
    os.chdir(inst)
    os.execvpe("asciinema", ["asciinema", "rec", "--overwrite", "-q", "-i", "2",
        "--window-size", f"{COLS}x{ROWS}", "--capture-env", "TERM,COLORTERM,LANG",
        "--title", "Cataclysm: Dark Days Ahead", "-c", "./cataclysm-dda", CAST], env)
fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", ROWS, COLS, 0, 0))

def pump(t):
    end = time.time() + t
    while time.time() < end:
        r, _, _ = select.select([fd], [], [], 0.05)
        if r:
            try:
                data = os.read(fd, 65536)
            except OSError:
                return False
            if not data:
                return False
            stream.feed(data)
    return True

def text():
    return "\n".join(screen.display)

def wait_for(s, timeout=120):
    end = time.time() + timeout
    while time.time() < end:
        if s in text():
            return True
        pump(0.2)
    sys.exit(f"timed out waiting for {s!r}; screen:\n{text()}")

LOG = open(os.environ["CDDA_REC_LOG"], "w") if os.environ.get("CDDA_REC_LOG") else None
def wait_any(*ss, timeout=120):
    end = time.time() + timeout
    while time.time() < end:
        for s in ss:
            if s in text():
                return s
        pump(0.2)
    sys.exit(f"timed out waiting for {ss!r}; screen:\n{text()}")

def key(k, t=0.4):
    os.write(fd, k)
    pump(t)
    if LOG:
        LOG.write(f"--- after {k!r}\n{text()}\n")

# the map is the left part of the screen; the player is the @ nearest its middle
MAP_W = 56
WALLS = set("#|-+=%&{}0<>\"xqlkmjtuvwnHFO8^~") | set("┌┐└┘─│├┤┬┴┼")
DIRS = {(-1, 0): b"k", (1, 0): b"j", (0, -1): b"h", (0, 1): b"l",
        (-1, -1): b"y", (-1, 1): b"u", (1, -1): b"b", (1, 1): b"n"}

def grid():
    return [row[:MAP_W] for row in screen.display]

def player(g):
    best = None
    for r, row in enumerate(g):
        for c, ch in enumerate(row):
            if ch == "@":
                d = abs(r - ROWS // 2) + abs(c - MAP_W // 2)
                if best is None or d < best[0]:
                    best = (d, r, c)
    return best[1:] if best else None

blocked = set()
def step():
    """One move toward the nearest walkable square next to unexplored space
    (the view follows the player, so the player stays near the middle);
    doors (+) are opened by walking into them, other people (@) are walked
    around. A move that changes nothing or opens a prompt marks that square
    as blocked until the view moves."""
    if "Place:" not in text():          # a prompt or a menu is open
        key(ESC, 0.6)
        return
    g = grid()
    p = player(g)
    if not p:
        return
    q = deque([(p, None)])
    prev = {p}
    move = None
    while q:
        (r, c), first = q.popleft()
        if first and any(0 <= r + dr < ROWS and 0 <= c + dc < MAP_W and g[r + dr][c + dc] == " "
                         for dr, dc in DIRS):
            move = first
            break
        for (dr, dc) in DIRS:
            nr, nc = r + dr, c + dc
            if not (0 <= nr < ROWS and 0 <= nc < MAP_W) or (nr, nc) in prev:
                continue
            ch = g[nr][nc]
            if ch in " @" or (ch in WALLS and ch != "+") or (nr, nc) in blocked:
                continue
            prev.add((nr, nc))
            q.append(((nr, nc), first or (dr, dc)))
    if move is None:
        free = [d for d in DIRS if (p[0] + d[0], p[1] + d[1]) not in blocked]
        move = random.choice(free or list(DIRS))
    key(DIRS[move], 0.35)
    if "Place:" not in text():          # walked into something that asks
        key(ESC, 0.6)
        blocked.add((p[0] + move[0], p[1] + move[1]))
    elif grid() == g:
        blocked.add((p[0] + move[0], p[1] + move[1]))
    else:
        blocked.clear()

wait_for("Select your language")       # asked at every start with LANG=C.UTF-8
key(ENTER, 1)
wait_for("Play Now!  (Default Scenario)")
key(DOWN); key(DOWN); key(ENTER, 1)
# depending on where the menu's cursor starts this is "Play Now!", straight
# into the game, or the default scenario, through world and character
if wait_any("Finish", "Place:", timeout=180) == "Finish":
    key(b"f", 1)
    wait_for("Case Sensitive")
    key(b"Y", 1)
    wait_for("TAB to finish character creation", 180)
    key(TAB, 1)
    wait_for("Case Sensitive")
    key(b"Y", 1)
wait_for("Place:", 180)
pump(2.5)
# a message about the start may be waiting for a key
start = time.time()
while time.time() - start < 15:
    step()
pump(1)
key(b"m", 3.5)                          # the overmap
key(ESC, 1)
for _ in range(6):
    step()
pump(1.5)
key(b"S", 1)                            # save and quit
wait_for("Case Sensitive")
key(b"Y", 2)
wait_for("[Quit]", 60)
key(b"Q", 1)                            # main menu: the Quit tab
# the first Enter after changing tabs is sometimes not taken, so repeat it
for _ in range(3):
    os.write(fd, ENTER)
    if not pump(1.5):
        break
while pump(0.5):
    if os.waitpid(pid, os.WNOHANG)[0]:
        break
shutil.rmtree(tmp, ignore_errors=True)

#!/usr/bin/env python3
"""Kunzite Lattice — neon tetromino-well arcade for ElbowOS."""
from __future__ import annotations

import math
import os
import random
import subprocess
import sys

import pygame

W, H = 1080, 1920
FPS = 30
TITLE = "KUNZITE LATTICE"
HANDLE = "x.com/ElbowOS"
COLS, ROWS = 10, 18
BG = (10, 4, 18)
WELL = (22, 8, 36)
GRID = (54, 18, 72)
INK = (255, 210, 255)
GOLD = (255, 214, 90)
CYAN = (90, 255, 230)

# I J L O S T Z — kunzite / rose / orchid / gold / mint / violet / coral
SHAPES = {
    "I": [[(0, 1), (1, 1), (2, 1), (3, 1)], [(2, 0), (2, 1), (2, 2), (2, 3)]],
    "J": [
        [(0, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (1, 2)],
        [(0, 1), (1, 1), (2, 1), (2, 2)],
        [(1, 0), (1, 1), (1, 2), (0, 2)],
    ],
    "L": [
        [(2, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (1, 1), (1, 2), (2, 2)],
        [(0, 1), (1, 1), (2, 1), (0, 2)],
        [(0, 0), (1, 0), (1, 1), (1, 2)],
    ],
    "O": [[(1, 0), (2, 0), (1, 1), (2, 1)]],
    "S": [[(1, 0), (2, 0), (0, 1), (1, 1)], [(1, 0), (1, 1), (2, 1), (2, 2)]],
    "T": [
        [(1, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (1, 1), (2, 1), (1, 2)],
        [(0, 1), (1, 1), (2, 1), (1, 2)],
        [(1, 0), (0, 1), (1, 1), (1, 2)],
    ],
    "Z": [[(0, 0), (1, 0), (1, 1), (2, 1)], [(2, 0), (1, 1), (2, 1), (1, 2)]],
}
PAL = {
    "I": (255, 120, 210),
    "J": (160, 90, 255),
    "L": (255, 170, 70),
    "O": (255, 230, 110),
    "S": (80, 255, 190),
    "T": (210, 80, 255),
    "Z": (255, 90, 130),
}


class Spark:
    __slots__ = ("x", "y", "vx", "vy", "life", "col", "r")

    def __init__(self, x, y, vx, vy, life, col, r=5):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.life, self.col, self.r = life, col, r


class Game:
    def __init__(self, record: bool):
        self.record = record
        self.surf = pygame.Surface((W, H))
        self.clock = pygame.time.Clock()
        self.font_lg = pygame.font.Font(None, 62)
        self.font_md = pygame.font.Font(None, 44)
        self.font_sm = pygame.font.Font(None, 32)
        self.margin_x = 90
        self.top = 280
        self.cell = 90
        self.reset()

    def reset(self) -> None:
        self.board = [[None] * COLS for _ in range(ROWS)]
        self.score = 0
        self.lines = 0
        self.combo = 0
        self.sparks: list[Spark] = []
        self.flash: list[tuple[int, float]] = []
        self.bag: list[str] = []
        self.fall = 0.0
        self.gravity = 0.18
        self.lock_fx = 0.0
        self.spawn()

    def refill(self) -> None:
        self.bag = list(SHAPES)
        random.shuffle(self.bag)

    def spawn(self) -> None:
        if not self.bag:
            self.refill()
        self.kind = self.bag.pop()
        self.rot = 0
        self.px, self.py = 3, 0
        if not self.valid(self.px, self.py, self.rot):
            del self.board[0:2]
            self.board.extend([[None] * COLS for _ in range(2)])
            self.px, self.py, self.rot = 3, 0, 0

    def cells(self, x, y, rot):
        body = SHAPES[self.kind]
        return [(x + cx, y + cy) for cx, cy in body[rot % len(body)]]

    def valid(self, x, y, rot) -> bool:
        for cx, cy in self.cells(x, y, rot):
            if cx < 0 or cx >= COLS or cy >= ROWS:
                return False
            if cy >= 0 and self.board[cy][cx]:
                return False
        return True

    def burst(self, x, y, col, n=10) -> None:
        for _ in range(n):
            ang = random.random() * 6.283
            spd = random.uniform(40, 220)
            self.sparks.append(
                Spark(x, y, spd * math.cos(ang), spd * math.sin(ang),
                      random.uniform(0.25, 0.7), col, random.randint(3, 7))
            )

    def lock(self) -> None:
        col = PAL[self.kind]
        for cx, cy in self.cells(self.px, self.py, self.rot):
            if 0 <= cy < ROWS:
                self.board[cy][cx] = col
                bx = self.margin_x + cx * self.cell + self.cell // 2
                by = self.top + cy * self.cell + self.cell // 2
                self.burst(bx, by, col, 6)
        full = [r for r in range(ROWS) if all(self.board[r])]
        if full:
            for r in full:
                self.flash.append((r, 0.28))
                for c in range(COLS):
                    bx = self.margin_x + c * self.cell + self.cell // 2
                    by = self.top + r * self.cell + self.cell // 2
                    self.burst(bx, by, GOLD, 5)
            keep = [self.board[r] for r in range(ROWS) if r not in full]
            self.board = [[None] * COLS for _ in range(len(full))] + keep
            n = len(full)
            self.lines += n
            self.combo += 1
            self.score += (100, 300, 500, 800)[min(n, 4) - 1] * max(1, self.combo)
        else:
            self.combo = 0
            self.score += 8
        self.lock_fx = 0.18
        self.spawn()

    def pick_drop(self) -> tuple[int, int]:
        best = None
        nrot = len(SHAPES[self.kind])
        for rot in range(nrot):
            for x in range(-2, COLS):
                if not self.valid(x, 0, rot) and not self.valid(x, 1, rot):
                    continue
                y = 0
                while self.valid(x, y + 1, rot):
                    y += 1
                if not self.valid(x, y, rot):
                    continue
                holes = height = 0
                occupied = set(self.cells(x, y, rot))
                for c in range(COLS):
                    seen = False
                    col_h = 0
                    for r in range(ROWS):
                        filled = bool(self.board[r][c]) or (c, r) in occupied
                        if filled:
                            seen = True
                            col_h = ROWS - r
                        elif seen:
                            holes += 1
                    height += col_h
                score = holes * 40 + height - abs(x - 3) * 0.2
                cand = (score, abs(x - 3), rot, x)
                if best is None or cand < best:
                    best = cand
        if best is None:
            return self.rot, self.px
        return best[2], best[3]

    def autoplay(self, dt: float) -> None:
        target_rot, target_x = self.pick_drop()
        if self.rot != target_rot:
            nxt = (self.rot + 1) % len(SHAPES[self.kind])
            if self.valid(self.px, self.py, nxt):
                self.rot = nxt
            elif self.valid(self.px - 1, self.py, nxt):
                self.px -= 1
                self.rot = nxt
            elif self.valid(self.px + 1, self.py, nxt):
                self.px += 1
                self.rot = nxt
            return
        if self.px < target_x and self.valid(self.px + 1, self.py, self.rot):
            self.px += 1
        elif self.px > target_x and self.valid(self.px - 1, self.py, self.rot):
            self.px -= 1
        else:
            if self.valid(self.px, self.py + 1, self.rot):
                self.py += 1

    def update(self, dt: float) -> None:
        if self.record:
            self.autoplay(dt)
        self.fall += dt
        step = self.gravity * (0.35 if self.record else 1.0)
        if self.fall >= step:
            self.fall = 0.0
            if self.valid(self.px, self.py + 1, self.rot):
                self.py += 1
            else:
                self.lock()
        self.lock_fx = max(0.0, self.lock_fx - dt)
        alive = []
        for sp in self.sparks:
            sp.life -= dt
            if sp.life <= 0:
                continue
            sp.x += sp.vx * dt
            sp.y += sp.vy * dt
            sp.vy += 380 * dt
            alive.append(sp)
        self.sparks = alive
        self.flash = [(r, t - dt) for r, t in self.flash if t - dt > 0]

    def handle(self, ev) -> None:
        if ev.type != pygame.KEYDOWN:
            return
        if ev.key in (pygame.K_LEFT, pygame.K_a) and self.valid(self.px - 1, self.py, self.rot):
            self.px -= 1
        elif ev.key in (pygame.K_RIGHT, pygame.K_d) and self.valid(self.px + 1, self.py, self.rot):
            self.px += 1
        elif ev.key in (pygame.K_UP, pygame.K_w, pygame.K_x):
            nxt = (self.rot + 1) % len(SHAPES[self.kind])
            for dx in (0, -1, 1, -2, 2):
                if self.valid(self.px + dx, self.py, nxt):
                    self.px += dx
                    self.rot = nxt
                    break
        elif ev.key in (pygame.K_DOWN, pygame.K_s):
            if self.valid(self.px, self.py + 1, self.rot):
                self.py += 1
                self.score += 1
        elif ev.key == pygame.K_SPACE:
            while self.valid(self.px, self.py + 1, self.rot):
                self.py += 1
                self.score += 2
            self.lock()
        elif ev.key == pygame.K_r:
            self.reset()

    def draw_cell(self, s, cx, cy, col, ghost=False) -> None:
        x = self.margin_x + cx * self.cell
        y = self.top + cy * self.cell
        pad = 4
        r = pygame.Rect(x + pad, y + pad, self.cell - pad * 2, self.cell - pad * 2)
        if ghost:
            pygame.draw.rect(s, col, r, width=3, border_radius=8)
            return
        pygame.draw.rect(s, col, r, border_radius=10)
        hi = tuple(min(255, c + 70) for c in col)
        pygame.draw.rect(s, hi, pygame.Rect(r.x + 6, r.y + 6, r.w - 18, 16), border_radius=6)
        pygame.draw.rect(s, (255, 255, 255), r, width=2, border_radius=10)

    def draw(self, s: pygame.Surface) -> None:
        s.fill(BG)
        for i in range(6):
            x = 40 + i * 200
            shade = 16 + (i % 3) * 6
            pygame.draw.rect(s, (shade, 6, shade + 8), (x, 0, 70, H))
        well = pygame.Rect(self.margin_x - 12, self.top - 12, COLS * self.cell + 24, ROWS * self.cell + 24)
        pygame.draw.rect(s, WELL, well, border_radius=18)
        pygame.draw.rect(s, (255, 90, 210), well, width=4, border_radius=18)
        for r in range(ROWS):
            for c in range(COLS):
                gx = self.margin_x + c * self.cell
                gy = self.top + r * self.cell
                pygame.draw.rect(s, GRID, (gx, gy, self.cell, self.cell), width=1)
                if self.board[r][c]:
                    self.draw_cell(s, c, r, self.board[r][c])
        for r, t in self.flash:
            alpha = int(220 * (t / 0.28))
            overlay = pygame.Surface((COLS * self.cell, self.cell), pygame.SRCALPHA)
            overlay.fill((255, 230, 140, alpha))
            s.blit(overlay, (self.margin_x, self.top + r * self.cell))
        gy = self.py
        while self.valid(self.px, gy + 1, self.rot):
            gy += 1
        for cx, cy in self.cells(self.px, gy, self.rot):
            if cy >= 0:
                self.draw_cell(s, cx, cy, PAL[self.kind], ghost=True)
        for cx, cy in self.cells(self.px, self.py, self.rot):
            if cy >= 0:
                self.draw_cell(s, cx, cy, PAL[self.kind])
        for sp in self.sparks:
            pygame.draw.circle(s, sp.col, (int(sp.x), int(sp.y)), max(1, int(sp.r * sp.life * 2)))
        title = self.font_lg.render(TITLE, True, INK)
        s.blit(title, title.get_rect(center=(W // 2, 78)))
        handle = self.font_sm.render(HANDLE, True, CYAN)
        s.blit(handle, handle.get_rect(center=(W // 2, 128)))
        score = self.font_md.render(f"SCORE  {self.score}    LINES  {self.lines}", True, GOLD)
        s.blit(score, score.get_rect(center=(W // 2, 188)))
        hint = self.font_sm.render("\u2190 \u2192 move   \u2191 rotate   space hard-drop   R reset", True, (180, 140, 200))
        s.blit(hint, hint.get_rect(center=(W // 2, H - 70)))
        if self.lock_fx > 0:
            flash = pygame.Surface((W, H), pygame.SRCALPHA)
            flash.fill((255, 160, 230, int(40 * self.lock_fx / 0.18)))
            s.blit(flash, (0, 0))

    def play(self) -> None:
        screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption(TITLE)
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT or (ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE):
                    running = False
                else:
                    self.handle(ev)
            self.update(dt)
            self.draw(self.surf)
            screen.blit(self.surf, (0, 0))
            pygame.display.flip()

    def record_mp4(self, path: str) -> None:
        cmd = [
            "ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
            "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "20", "-preset", "fast", "-movflags", "+faststart", path,
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        frames = FPS * 15
        for i in range(frames):
            self.update(1.0 / FPS)
            self.draw(self.surf)
            proc.stdin.write(pygame.image.tostring(self.surf, "RGB"))
            if i % 30 == 0:
                print(f"frame {i}/{frames}", flush=True)
        proc.stdin.close()
        rc = proc.wait()
        if rc != 0:
            raise SystemExit(f"ffmpeg failed: {rc}")
        print("wrote", path)


def main() -> None:
    record = "--record" in sys.argv or os.environ.get("ELBOWOS_RECORD") == "1"
    play = "--play" in sys.argv
    if record or not play:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    pygame.init()
    pygame.font.init()
    g = Game(record or not play)
    if record or not play:
        out = os.environ.get("ELBOWOS_MP4", "/home/workdir/artifacts/KUNZITE_LATTICE_ElbowOS.mp4")
        g.record_mp4(out)
    else:
        g.play()
    pygame.quit()


if __name__ == "__main__":
    main()

"""
Video -> frame-by-frame Desmos equations.

Every sampled frame goes through the same pipeline as a still image
(edge detection -> contour simplification -> Lagrange polynomial segments),
and the player shows each frame either as one polynomial equation per curve
(x(t), y(t), 0<=t<=1) or packed into ONE expression whose coefficients are lists,
e.g. (\\left[a_1,a_2,...\\right]t^{4}+..., ...), which Desmos broadcasts over.
By default it plays in the fast list form and switches to polynomials when paused.

Outputs (in outputs/<video name>_video/):
  player.html        open in a browser -> Desmos plays the video, no copy/paste
  desmos_console.js  paste ONCE into the console on desmos.com/calculator
  frames.json        raw per-frame LaTeX, for anything else
  preview.mp4        quick render of the fitted curves (no Desmos needed)
  desmos_render.mp4  with --render (or render.py): the real Desmos graph + equations, real speed

Usage:
  python video.py clip.mp4
  python video.py clip.mp4 --fps 10 --width 400 --max-segments 300 --start 2 --end 8
"""
import argparse
import contextlib
import io
import json
from pathlib import Path

import cv2
import numpy as np

from base import ImageToDesmosConverter

DESMOS_API = "https://www.desmos.com/api/v1.11/calculator.js?apiKey=dcb31709b452b1cf9dc26972add0fda6"
DESMOS_LIST_LIMIT = 10000


class VideoToDesmosConverter:
    def __init__(self, video_path, output_dir="outputs"):
        self.video_path = Path(video_path)
        self.out_dir = Path(output_dir) / f"{self.video_path.stem}_video"
        self.frames = []        # per frame: (coeffs_x, coeffs_y), each shape (segments, degree+1)
        self.width = None
        self.height = None
        self.fps = None

    def read_frames(self, target_fps=12, width=480, start=0.0, end=None, max_frames=None):
        """Yield resized BGR frames sampled at target_fps (frame k is video time start + k/fps)."""
        cap = cv2.VideoCapture(str(self.video_path))
        if not cap.isOpened():
            raise ValueError(f"Could not open video {self.video_path}")

        src_fps = cap.get(cv2.CAP_PROP_FPS) or 30
        self.source_duration = cap.get(cv2.CAP_PROP_FRAME_COUNT) / src_fps
        target_fps = min(target_fps, src_fps)
        step = src_fps / target_fps
        self.fps = target_fps

        cap.set(cv2.CAP_PROP_POS_MSEC, start * 1000)
        idx = int(round(start * src_fps))
        next_take = float(idx)
        taken = 0

        while max_frames is None or taken < max_frames:
            ok, frame = cap.read()
            if not ok:
                break
            if end is not None and idx / src_fps > end:
                break
            if idx >= next_take:
                h, w = frame.shape[:2]
                if width and w > width:
                    frame = cv2.resize(frame, (width, int(round(h * width / w))),
                                       interpolation=cv2.INTER_AREA)
                yield frame
                taken += 1
                next_take += step
            idx += 1
        cap.release()

    def convert_frame(self, frame, segment_size=5, max_segments=600, low_threshold=30,
                      high_threshold=100, blur_size=3, min_length=30,
                      spacing=3, max_spacing=8, use_bilateral=False, bilateral_d=9,
                      bilateral_sigma_color=75, bilateral_sigma_space=75,
                      use_posterize=False, posterize_levels=4,
                      use_morphology=False, morph_close=3, morph_open=2, color=False):
        """Run the image pipeline on one frame.
        Returns (coeffs_x, coeffs_y, colors): padded coefficient arrays, plus one hex
        colour per segment sampled from the frame when color=True (else None)."""
        conv = ImageToDesmosConverter(None)
        # base.py prints a few lines per step; silence it so video runs stay readable
        with contextlib.redirect_stdout(io.StringIO()):
            conv.load_from_array(frame)
            if use_posterize:
                conv.posterize(levels=posterize_levels)
            conv.detect_edges(low_threshold=low_threshold, high_threshold=high_threshold,
                              blur_size=blur_size, min_contour_area=-1,
                              use_bilateral=use_bilateral, bilateral_d=bilateral_d,
                              bilateral_sigma_color=bilateral_sigma_color,
                              bilateral_sigma_space=bilateral_sigma_space)
            if use_morphology:
                conv.clean_edges(close_kernel=morph_close, open_kernel=morph_open)
            # Filter by length, not area: Canny traces of open strokes enclose ~zero area,
            # so an area filter throws away most line art
            conv.contours = [c for c in conv.contours if cv2.arcLength(c, True) >= min_length]
            # Longest contours first, so the segment budget keeps the important shapes
            conv.contours.sort(key=lambda c: cv2.arcLength(c, True), reverse=True)
            # Lagrange fitting uses evenly spaced t, so give it evenly spaced points;
            # widely uneven points (e.g. after Douglas-Peucker) make the polynomials overshoot.
            # Spacing grows (up to max_spacing) so as many contours as possible fit the
            # segment budget; past that, _within_budget drops the shortest contours.
            lengths = np.array([cv2.arcLength(c, True) for c in conv.contours])
            spacing = min(max_spacing, self._fit_spacing(lengths, segment_size, max_segments, spacing))
            conv.contours = [self._resample(c, spacing) for c in conv.contours]
            conv.contours = self._within_budget(conv.contours, segment_size, max_segments)

        cx, cy = self._fit_segments(conv.contours, segment_size, frame.shape[0])
        return cx, cy, (self._sample_colors(frame, cx, cy) if color else None)

    @staticmethod
    def _fit_segments(contours, segment_size, height):
        """Vectorised equivalent of ImageToDesmosConverter.fit_curves_parametric: same
        windows, same Lagrange polynomials through evenly spaced t in [0, 1] (y flipped),
        but solved with one precomputed inverse-Vandermonde matrix per window size instead
        of a scipy.lagrange call per segment (~100x faster for thousands of curves).
        Returns coefficient arrays (segments, segment_size), highest power first."""
        degree = segment_size - 1
        stride = max(1, segment_size - 2)
        windows = []
        for c in contours:
            pts = c.reshape(-1, 2).astype(float)
            pts[:, 1] = height - pts[:, 1]
            n = len(pts)
            if n < 2:
                continue
            if n <= segment_size:
                windows.append(pts)
            else:
                windows.extend(pts[i:i + segment_size] for i in range(0, n - segment_size + 1, stride))

        coeffs = np.zeros((len(windows), degree + 1, 2))
        sizes = np.array([len(w) for w in windows])
        for m in np.unique(sizes):
            idx = np.flatnonzero(sizes == m)
            inv = np.linalg.inv(np.vander(np.linspace(0, 1, m)))  # points -> coefficients
            # einsum rather than matmul: avoids spurious BLAS warnings on some macOS numpy builds
            coeffs[idx, degree + 1 - m:] = np.einsum('ij,kjl->kil', inv, np.stack([windows[k] for k in idx]))
        return coeffs[..., 0], coeffs[..., 1]

    @staticmethod
    def _sample_colors(frame, cx, cy, radius=3):
        """One colour per segment, darkened enough to show on white.
        Edges sit on the boundary between regions, so at each sample point take the
        least-white pixel within `radius` (the object's colour, or the ink of a line)
        instead of a plain average, which would wash out towards the background."""
        if len(cx) == 0:
            return []
        h, w = frame.shape[:2]
        t = np.linspace(0, 1, 5)
        px, py = np.zeros((len(cx), len(t))), np.zeros((len(cy), len(t)))
        for a, b in zip(cx.T, cy.T):  # Horner's method, highest power first
            px, py = px * t + a[:, None], py * t + b[:, None]
        py = h - py  # back to image rows
        off = np.arange(-radius, radius + 1)
        ox, oy = [o.ravel() for o in np.meshgrid(off, off)]
        xs = np.clip(np.rint(px)[..., None] + ox, 0, w - 1).astype(int)  # (segments, 5, window)
        ys = np.clip(np.rint(py)[..., None] + oy, 0, h - 1).astype(int)
        patch = frame[ys, xs].astype(int)                                  # (..., window, 3)
        best = patch.sum(axis=-1).argmin(axis=-1)                          # least white pixel
        picked = np.take_along_axis(patch, best[..., None, None], axis=2)[:, :, 0]
        bgr = picked.mean(axis=1).astype(np.uint8)
        hsv = cv2.cvtColor(bgr[None], cv2.COLOR_BGR2HSV)[0]
        hsv[:, 2] = np.minimum(hsv[:, 2], 190)  # near-white curves would vanish on the grid
        rgb = cv2.cvtColor(hsv[None], cv2.COLOR_HSV2RGB)[0]
        return ['#%02x%02x%02x' % tuple(int(v) for v in c) for c in rgb]

    @staticmethod
    def _fit_spacing(lengths, segment_size, max_segments, min_spacing):
        """Smallest point spacing (>= min_spacing) whose segment count fits the budget."""
        stride = max(1, segment_size - 2)

        def segments(sp):
            n = np.floor(lengths / sp) + 2  # points produced by _resample
            return np.where(n <= segment_size, 1, np.floor((n - segment_size) / stride) + 1).sum()

        lo, hi = min_spacing, max(min_spacing, lengths.max(initial=0))
        if segments(lo) <= max_segments:
            return lo
        for _ in range(30):
            mid = (lo + hi) / 2
            lo, hi = (lo, mid) if segments(mid) <= max_segments else (mid, hi)
        return hi

    @staticmethod
    def _resample(contour, spacing):
        """Resample a closed contour to points every `spacing` pixels along its length."""
        pts = contour.reshape(-1, 2).astype(float)
        pts = np.vstack([pts, pts[:1]])
        dist = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(pts, axis=0).T))])
        s = np.append(np.arange(0, dist[-1], spacing), dist[-1])
        out = np.stack([np.interp(s, dist, pts[:, 0]), np.interp(s, dist, pts[:, 1])], axis=1)
        return out.reshape(-1, 1, 2)

    @staticmethod
    def _within_budget(contours, segment_size, max_segments):
        """Greedily keep contours (longest first) that fit in the segment budget,
        so we don't spend time fitting curves that get dropped anyway.
        Mirrors the segmentation in ImageToDesmosConverter.fit_curves_parametric."""
        stride = max(1, segment_size - 2)
        kept, total = [], 0
        for c in contours:
            n = len(c)
            if n < 2:
                continue
            segs = 1 if n <= segment_size else len(range(0, n - segment_size + 1, stride))
            if total + segs > max_segments:
                continue
            kept.append(c)
            total += segs
        return kept

    def process(self, target_fps=12, width=480, start=0.0, end=None, max_frames=None,
                max_segments=600, preview=True, **frame_params):
        max_segments = min(max_segments, DESMOS_LIST_LIMIT)
        self.frames = []
        for i, frame in enumerate(self.read_frames(target_fps, width, start, end, max_frames)):
            if self.width is None:
                self.height, self.width = frame.shape[:2]
            cx, cy, colors = self.convert_frame(frame, max_segments=max_segments, **frame_params)
            self.frames.append((cx, cy, colors))
            print(f"\r  frame {i + 1}: {len(cx)} segments", end="", flush=True)
        print()

        if not self.frames:
            raise ValueError("No frames were read from the video (check --start/--end)")

        self.out_dir.mkdir(parents=True, exist_ok=True)
        # Raw coefficients (highest power first, 2 decimals); the player builds the LaTeX,
        # so it can show either one polynomial per curve or one compact list expression.
        # "c" (one hex colour per curve) is only present in colour mode.
        frames = []
        for cx, cy, colors in self.frames:
            f = {"x": self._rounded(cx), "y": self._rounded(cy)}
            if colors is not None:
                f["c"] = colors
            frames.append(f)
        data = {"fps": self.fps, "width": self.width, "height": self.height,
                "start": start, "source": str(self.video_path.resolve()), "frames": frames}

        self.export_json(data)
        self.export_player(data)
        self.export_console(data)
        if preview:
            self.export_preview()

        total = sum(len(f[0]) for f in self.frames)
        print(f"✓ {len(self.frames)} frames, avg {total / len(self.frames):.0f} segments/frame")
        covered_end = start + len(self.frames) / self.fps
        self.coverage = (start, min(covered_end, self.source_duration), self.source_duration)
        print(f"✓ Covers video time {start:.1f}s - {self.coverage[1]:.1f}s of {self.source_duration:.1f}s "
              f"(frame k = {start:g}s + k/{self.fps:g})")
        if (end is None or end > covered_end) and covered_end < self.source_duration - 1.5 / self.fps:
            print(f"⚠️  Stopped early at {covered_end:.1f}s (frame limit or unreadable frames); "
                  f"the rest of the video has no Desmos frames")
        print(f"✓ Open {self.out_dir / 'player.html'} in a browser to play it in Desmos")
        return self

    @staticmethod
    def _rounded(coeffs):
        return [[int(v) if v == int(v) else v for v in row] for row in np.round(coeffs, 2).tolist()]

    def export_json(self, data):
        with open(self.out_dir / "frames.json", "w") as f:
            json.dump(data, f)

    def export_player(self, data):
        # "</" inside a <script> block would end it early
        payload = json.dumps(data).replace("</", "<\\/")
        html = PLAYER_TEMPLATE.replace("__DESMOS_API__", DESMOS_API) \
                              .replace("__RENDERER__", RENDERER_JS) \
                              .replace("__TITLE__", self.video_path.stem) \
                              .replace("__DATA__", payload)
        with open(self.out_dir / "player.html", "w") as f:
            f.write(html)

    def export_console(self, data):
        script = CONSOLE_TEMPLATE.replace("__RENDERER__", RENDERER_JS).replace("__DATA__", json.dumps(data))
        with open(self.out_dir / "desmos_console.js", "w") as f:
            f.write(script)

    def export_preview(self):
        """Render the fitted curves to an mp4 so you can check quality without Desmos."""
        path = self.out_dir / "preview.mp4"
        writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"),
                                 self.fps, (self.width, self.height))
        t = np.linspace(0, 1, 20)
        for cx, cy, colors in self.frames:
            canvas = np.full((self.height, self.width, 3), 255, np.uint8)
            if len(cx):
                xs = np.array([np.polyval(c, t) for c in cx])
                ys = self.height - np.array([np.polyval(c, t) for c in cy])
                pts = np.stack([xs, ys], axis=-1).round().astype(np.int32)
                if colors is None:
                    cv2.polylines(canvas, list(pts), False, (0, 0, 0), 1, cv2.LINE_AA)
                else:
                    for p, hexcol in zip(pts, colors):
                        rgb = bytes.fromhex(hexcol[1:])
                        cv2.polylines(canvas, [p], False, (rgb[2], rgb[1], rgb[0]), 1, cv2.LINE_AA)
            writer.write(canvas)
        writer.release()


# Shared by the player and the console script. Builds Desmos LaTeX from coefficients.
#   'poly'    : one expression per curve, e.g. (2.5t^{4}-3t^{3}+...+120, ...)  -- readable, ~0.5s/frame at 600 curves
#   'compact' : one expression per frame with list coefficients               -- fast
# The players default to 'auto': compact while playing, polynomials when paused.
RENDERER_JS = r"""
function makeRenderer(calc) {
  const r2 = v => Math.round(v * 100) / 100;
  const powT = p => p === 0 ? '' : p === 1 ? 't' : 't^{' + p + '}';
  function poly(c) {  // coefficients, highest power first
    const deg = c.length - 1;
    let s = '';
    c.forEach((v, i) => {
      v = r2(v);
      if (!v) return;
      const p = deg - i, a = Math.abs(v);
      s += (v < 0 ? '-' : s ? '+' : '') + (p > 0 && a === 1 ? '' : a) + powT(p);
    });
    return s || '0';
  }
  function listPoly(rows) {
    const deg = rows[0].length - 1, terms = [];
    for (let i = 0; i <= deg; i++) {
      const col = rows.map(r => r2(r[i]));
      if (col.every(v => v === 0)) continue;
      terms.push('\\left[' + col.join(',') + '\\right]' + powT(deg - i));
    }
    return terms.join('+') || '0';
  }
  const style = { lineWidth: 1.5, parametricDomain: { min: '0', max: '1' } };
  const rgb = h => '\\operatorname{rgb}(' + [1, 3, 5].map(j => parseInt(h.substr(j, 2), 16)).join(',') + ')';
  let shown = 0;         // per-curve expressions currently on the graph
  let linked = false;    // compact 'frame' expression is wired to the colour list
  function trim(n) {
    const ids = [];
    for (let k = n; k < shown; k++) ids.push({ id: 'c' + k });
    if (ids.length) calc.removeExpressions(ids);
    shown = Math.min(shown, n);
  }
  return {
    mode: 'poly',
    useColor: true,
    show(f) {
      const colors = this.useColor && f.c;
      const latex = f.x.length ? '\\left(' + listPoly(f.x) + ',' + listPoly(f.y) + '\\right)' : '';
      if (this.mode === 'compact' && colors) {
        const colorList = 'C_{v}=\\left[' + colors.map(rgb).join(',') + '\\right]';
        if (linked) {
          calc.setExpression({ id: 'colors', latex: colorList });
          calc.setExpression({ id: 'frame', latex });
        } else {
          // A list of colours (one per curve) needs colorLatex, which setExpression ignores,
          // so link it once through the graph state; later frames only update the latex
          trim(0);
          const st = calc.getState();
          st.expressions.list = [
            { type: 'expression', id: 'colors', latex: colorList },
            { type: 'expression', id: 'frame', latex, colorLatex: 'C_{v}', color: '#000000',
              lineWidth: '1.5', parametricDomain: { min: '0', max: '1' } },
          ];
          calc.setState(st, { allowUndo: false });
          linked = true;
        }
      } else if (this.mode === 'compact') {
        trim(0);
        if (linked) {  // drop the colour link so the curves go back to black
          calc.removeExpressions([{ id: 'frame' }, { id: 'colors' }]);
          linked = false;
        }
        calc.setExpression({ id: 'frame', ...style, color: '#000000', latex });
      } else {
        calc.removeExpressions([{ id: 'frame' }, { id: 'colors' }]);
        linked = false;
        calc.setExpressions(f.x.map((cx, k) => ({ id: 'c' + k, ...style,
          color: colors ? colors[k] : '#000000',
          latex: '\\left(' + poly(cx) + ',' + poly(f.y[k]) + '\\right)' })));
        trim(f.x.length);
        shown = f.x.length;
      }
    },
    // Resolves once Desmos has finished computing and drawing what is on the graph
    whenDrawn() {
      return new Promise(r => calc.asyncScreenshot({ width: 32, height: 32 },
        () => requestAnimationFrame(() => requestAnimationFrame(r))));
    }
  };
}

// Fit the frame into the graph pane without stretching it
function fitView(calc, W, H) {
  const px = calc.graphpaperBounds.pixelCoordinates;
  const k = Math.max(W / px.width, H / px.height);
  calc.setMathBounds({ left: W / 2 - k * px.width / 2, right: W / 2 + k * px.width / 2,
                       bottom: H / 2 - k * px.height / 2, top: H / 2 + k * px.height / 2 });
}
"""

PLAYER_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>__TITLE__ - Desmos Video</title>
<script src="__DESMOS_API__"></script>
<style>
  body { margin: 0; font-family: system-ui, sans-serif; background: #f4f4f6; color: #222; }
  #wrap { max-width: 1300px; margin: 0 auto; padding: 16px; }
  #calc { width: 100%; height: 75vh; background: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 4px rgba(0,0,0,.15); }
  #controls { display: flex; flex-wrap: wrap; gap: 12px; align-items: center; margin-top: 12px; }
  #controls input[type=range] { flex: 1; min-width: 200px; }
  button { padding: 6px 14px; font-size: 15px; cursor: pointer; }
  .muted { color: #666; font-size: 13px; }
  /* ?render (used by render.py): calculator only, filling the window */
  body.render #wrap { max-width: none; padding: 0; }
  body.render #calc { height: 100vh; border-radius: 0; box-shadow: none; }
  body.render #controls, body.render .muted { display: none; }
</style>
</head>
<body>
<div id="wrap">
  <div id="calc"></div>
  <div id="controls">
    <button id="play">Pause</button>
    <button id="prev">&#9664;</button>
    <button id="next">&#9654;</button>
    <input id="scrub" type="range" min="0" value="0">
    <span id="label"></span>
    <label>fps <input id="fps" type="number" min="1" max="60" style="width:4em"></label>
    <label><input id="loop" type="checkbox" checked> loop</label>
    <label>equations
      <select id="view">
        <option value="auto">polynomials when paused</option>
        <option value="poly">always polynomials (slow)</option>
        <option value="compact">always compact lists</option>
      </select>
    </label>
    <label id="colorWrap"><input id="color" type="checkbox" checked> colour</label>
    <span>|</span>
    <label>record at <input id="hold" type="number" min="0.5" step="0.5" value="2" style="width:4em"> s/frame</label>
    <button id="record">Record mode</button>
  </div>
  <p class="muted">Space = play/pause, arrow keys = step. While playing, each frame is packed into one list
    expression so playback stays smooth; pause or step to see every curve as its own polynomial x(t), y(t).<br>
    <b>Record mode</b> (for screen recording with the equations visible): after a 3 s countdown it shows every
    frame as polynomials on a fixed schedule, one frame every N seconds, so each frame gets exactly the same screen
    time. Speed the recording up by <i>N &times; fps</i> (e.g. 2 s/frame at 12 fps &rarr; 24&times;). If a frame takes
    longer than N seconds to draw you get a warning; raise N or lower the curves per frame.</p>
</div>
<script>
__RENDERER__
const DATA = __DATA__;
const N = DATA.frames.length;
const calc = Desmos.GraphingCalculator(document.getElementById('calc'), {
  settingsMenu: false, keypad: false, border: false
});
const renderer = makeRenderer(calc);
const fit = () => fitView(calc, DATA.width, DATA.height);
fit();
window.addEventListener('resize', fit);

let i = 0, timer = null;
const playBtn = document.getElementById('play');
const scrub = document.getElementById('scrub');
const label = document.getElementById('label');
const fpsIn = document.getElementById('fps');
const loopIn = document.getElementById('loop');
const viewIn = document.getElementById('view');
const colorIn = document.getElementById('color');
const holdIn = document.getElementById('hold');
const recBtn = document.getElementById('record');
if (!DATA.frames.some(f => f.c)) document.getElementById('colorWrap').style.display = 'none';
colorIn.onchange = () => { renderer.useColor = colorIn.checked; show(i); };
let recording = null;
scrub.max = N - 1;
fpsIn.value = DATA.fps;

function show(k) {
  i = (k + N) % N;
  renderer.mode = viewIn.value === 'auto' ? (timer ? 'compact' : 'poly') : viewIn.value;
  renderer.show(DATA.frames[i]);
  scrub.value = i;
  label.textContent = 'frame ' + (i + 1) + ' / ' + N;
}
function tick() {
  if (i === N - 1 && !loopIn.checked) return pause();
  timer = setTimeout(tick, 1000 / Math.max(1, +fpsIn.value || DATA.fps));
  show(i + 1);
}
function play() { stopRecording(); if (!timer) { playBtn.textContent = 'Pause'; tick(); } }
function pause() {
  if (!timer) return;
  clearTimeout(timer); timer = null; playBtn.textContent = 'Play';
  show(i);  // redraw as polynomials in 'auto' view
}

const sleep = ms => new Promise(r => setTimeout(r, ms));
function stopRecording() { if (recording) recording.stop = true; }
async function record() {
  pause();
  const rec = recording = { stop: false };
  recBtn.textContent = 'Stop recording';
  const period = 1000 * Math.max(0.5, +holdIn.value || 2);
  let slow = 0;
  for (let c = 3; c > 0 && !rec.stop; c--) { label.textContent = 'recording in ' + c + '...'; await sleep(1000); }
  const start = performance.now();
  for (let k = 0; k < N && !rec.stop; k++) {
    // Fixed schedule: frame k is shown at start + k*period no matter how long Desmos takes,
    // so every frame gets the same screen time and a uniform speed-up is exact
    show(k);                       // timer is null, so the 'auto' view draws polynomials
    await renderer.whenDrawn();
    const wait = start + (k + 1) * period - performance.now();
    if (wait < 0) slow++;
    await sleep(Math.max(0, wait));
  }
  if (!rec.stop) label.textContent = slow
    ? 'done, but ' + slow + ' frame(s) took longer than ' + period / 1000 + ' s - raise s/frame and record again'
    : 'done - speed the recording up ' + Math.round(period / 1000 * DATA.fps * 10) / 10 + 'x';
  recording = null;
  recBtn.textContent = 'Record mode';
}
recBtn.onclick = () => recording ? stopRecording() : record();

playBtn.onclick = () => timer ? pause() : play();
document.getElementById('prev').onclick = () => { stopRecording(); pause(); show(i - 1); };
document.getElementById('next').onclick = () => { stopRecording(); pause(); show(i + 1); };
scrub.oninput = () => { stopRecording(); pause(); show(+scrub.value); };
viewIn.onchange = () => show(i);
document.addEventListener('keydown', e => {
  if (e.target.closest && e.target.closest('#calc')) return;
  if (e.code === 'Space') { e.preventDefault(); playBtn.click(); }
  if (e.code === 'ArrowLeft') { pause(); show(i - 1); }
  if (e.code === 'ArrowRight') { pause(); show(i + 1); }
});

timer = setTimeout(tick, 1000 / DATA.fps);
show(0);

// render.py opens this page with ?render and steps through frames itself
if (new URLSearchParams(location.search).has('render')) {
  clearTimeout(timer); timer = null;
  document.body.classList.add('render');
  calc.resize();
  fit();
}
// Show frame k ('poly' or 'compact' view, colour on/off) and resolve once Desmos has drawn it
window.renderFrame = async (k, view, color) => {
  viewIn.value = view;
  renderer.useColor = color;
  show(k);
  await renderer.whenDrawn();
};
</script>
</body>
</html>
"""

CONSOLE_TEMPLATE = r"""// Paste this whole file ONCE into the browser console on https://www.desmos.com/calculator
// Controls afterwards:  dv.pause()  dv.play()  dv.go(10)  dv.fps(5)
//                       dv.mode('auto')     -> compact while playing, polynomials when paused (default)
//                       dv.mode('poly')     -> always one polynomial equation per curve (slow)
//                       dv.mode('compact')  -> always one list expression per frame
//                       dv.color(false)     -> black and white (only if converted with --color)
//                       dv.record(2)        -> for screen recording: every frame as polynomials, one frame
//                                              every 2 s on a fixed schedule; speed the recording up by
//                                              2 x fps. dv.stop() cancels.
(() => {
__RENDERER__
  const DATA = __DATA__;
  const N = DATA.frames.length;
  if (window.dv) window.dv.pause();
  Calc.setBlank();
  fitView(Calc, DATA.width, DATA.height);
  const renderer = makeRenderer(Calc);
  let i = 0, timer = null, view = 'auto';
  const show = k => {
    i = (k + N) % N;
    renderer.mode = view === 'auto' ? (timer ? 'compact' : 'poly') : view;
    renderer.show(DATA.frames[i]);
  };
  const tick = () => { timer = setTimeout(tick, 1000 / DATA.fps); show(i + 1); };
  window.dv = {
    play() { this.stop(); if (!timer) tick(); },
    pause() { if (timer) { clearTimeout(timer); timer = null; show(i); } },
    go(k) { this.pause(); show(k); },
    fps(f) { DATA.fps = f; },
    mode(m) { view = m; show(i); },
    color(on) { renderer.useColor = on; show(i); },
    async record(secondsPerFrame = 2) {
      this.pause();
      const rec = this._rec = { stop: false }, period = secondsPerFrame * 1000;
      const sleep = ms => new Promise(r => setTimeout(r, ms));
      let slow = 0;
      for (let c = 3; c > 0 && !rec.stop; c--) { console.log('recording in ' + c + '...'); await sleep(1000); }
      const start = performance.now();
      for (let k = 0; k < N && !rec.stop; k++) {
        show(k);  // fixed schedule: frame k at start + k*period
        await renderer.whenDrawn();
        const wait = start + (k + 1) * period - performance.now();
        if (wait < 0) slow++;
        await sleep(Math.max(0, wait));
      }
      if (rec.stop) return;
      console.log(slow ? 'done, but ' + slow + ' frame(s) took longer than ' + secondsPerFrame + ' s - try dv.record(' + (secondsPerFrame + 1) + ')'
                       : 'done - speed the recording up ' + secondsPerFrame * DATA.fps + 'x');
    },
    stop() { if (this._rec) this._rec.stop = true; },
  };
  window.dv.play();
  console.log('Playing ' + N + ' frames at ' + DATA.fps + ' fps. dv.pause() to stop and see the polynomials.');
})();
"""


def main():
    p = argparse.ArgumentParser(description="Convert a video into frame-by-frame Desmos equations")
    p.add_argument("video")
    p.add_argument("--fps", type=float, default=12, help="frames per second to sample (default 12)")
    p.add_argument("--width", type=int, default=480, help="resize frames to this width (default 480)")
    p.add_argument("--start", type=float, default=0, help="start time in seconds")
    p.add_argument("--end", type=float, default=None, help="end time in seconds")
    p.add_argument("--max-frames", type=int, default=None, help="stop after this many frames (default: whole video)")
    p.add_argument("--max-segments", type=int, default=600,
                   help="max polynomial segments per frame; lower = faster in Desmos (default 600)")
    p.add_argument("--segment-size", type=int, default=5, help="points per polynomial (degree+1)")
    p.add_argument("--spacing", type=float, default=3,
                   help="minimum pixels between fitted points; raised automatically per frame "
                        "to fit --max-segments (default 3)")
    p.add_argument("--max-spacing", type=float, default=8,
                   help="cap on the automatic spacing; past it, short contours are dropped (default 8)")
    p.add_argument("--canny-low", type=int, default=30)
    p.add_argument("--canny-high", type=int, default=100)
    p.add_argument("--blur", type=int, default=3)
    p.add_argument("--min-length", type=float, default=30, help="drop contours shorter than this (px)")
    p.add_argument("--bilateral", action="store_true", help="use bilateral filter (good for real footage)")
    p.add_argument("--posterize", type=int, default=0, metavar="LEVELS", help="posterize to N gray levels")
    p.add_argument("--morphology", action="store_true", help="morphological edge cleanup")
    p.add_argument("--color", action="store_true",
                   help="colour each curve from the video (default: black and white)")
    p.add_argument("--no-preview", action="store_true", help="skip writing preview.mp4")
    p.add_argument("--render", action="store_true",
                   help="also render desmos_render.mp4 (graph + equations, real speed, with audio); "
                        "for more options run render.py on the output folder")
    a = p.parse_args()

    conv = VideoToDesmosConverter(a.video).process(
        target_fps=a.fps, width=a.width, start=a.start, end=a.end, max_frames=a.max_frames,
        max_segments=a.max_segments, preview=not a.no_preview,
        segment_size=a.segment_size, spacing=a.spacing, max_spacing=a.max_spacing,
        low_threshold=a.canny_low, high_threshold=a.canny_high, blur_size=a.blur,
        min_length=a.min_length, use_bilateral=a.bilateral,
        use_posterize=a.posterize > 0, posterize_levels=a.posterize or 4,
        use_morphology=a.morphology, color=a.color,
    )
    if a.render:
        from render import render, RenderError
        try:
            render(conv.out_dir)
        except RenderError as e:
            raise SystemExit(str(e))


if __name__ == "__main__":
    main()

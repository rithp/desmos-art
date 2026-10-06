"""
Render a converted video straight to an mp4: the Desmos graph AND the polynomial
equations panel, every frame fully drawn, at the video's real frame rate.
No screen recording or speeding up needed.

It opens the generated player.html in headless Chrome, shows each frame, waits for
Desmos to finish drawing it, screenshots it, and stitches the screenshots with ffmpeg
(adding the original audio when the source video is still available).

Requires:  pip install playwright   (uses your installed Google Chrome)
           ffmpeg on PATH           (brew install ffmpeg)

Usage:
  python render.py outputs/clip_video
  python render.py outputs/clip_video --size 1920x1080 --workers 4 --audio clip.mp4
  python video.py clip.mp4 --render        # convert and render in one go
"""
import argparse
import asyncio
import json
import shutil
import subprocess
import tempfile
import time
from pathlib import Path


class RenderError(Exception):
    pass


def _print_progress(done, total, eta):
    print(f"\r  rendered {done}/{total} frames  (~{eta / 60:.1f} min left)",
          end="\n" if done == total else "", flush=True)


async def _render_frames(player_url, frames, size, view, color, workers, frame_dir, n_total, progress):
    from playwright.async_api import async_playwright

    done = 0
    t0 = time.time()

    async def worker(browser, ks):
        nonlocal done
        page = await browser.new_page(viewport={"width": size[0], "height": size[1]})
        await page.goto(player_url)
        await page.wait_for_function("window.renderFrame !== undefined && window.Desmos !== undefined")
        try:  # the demo API key shows a dismissable notice over the graph
            await page.click(".dcg-api-trial-notice-close", timeout=3000)
        except Exception:
            pass
        for k in ks:
            await page.evaluate("([k, v, c]) => renderFrame(k, v, c)", [k, view, color])
            await page.screenshot(path=str(frame_dir / f"frame_{k:06d}.png"))
            done += 1
            progress(done, n_total, (time.time() - t0) / done * (n_total - done))
        await page.close()

    async with async_playwright() as pw:
        try:
            browser = await pw.chromium.launch(channel="chrome")
        except Exception:
            browser = await pw.chromium.launch()  # Playwright's own Chromium, if installed
        # Interleave frames so every worker is busy until the end
        await asyncio.gather(*(worker(browser, frames[w::workers]) for w in range(workers)))
        await browser.close()


def render(out_dir, output=None, size=(1920, 1080), view="poly", color=True,
           workers=4, audio=None, progress=_print_progress):
    """Render <out_dir>/desmos_render.mp4. audio: file to take sound from, None = the original
    video if it still exists, False = no sound. progress(done, total, eta_seconds) is called
    after every frame."""
    out_dir = Path(out_dir)
    data = json.loads((out_dir / "frames.json").read_text())
    if "renderFrame" not in (out_dir / "player.html").read_text():
        raise RenderError(f"{out_dir} was converted by an older version of video.py; "
                         "run video.py on the video again, then render")
    fps, n = data["fps"], len(data["frames"])
    output = Path(output) if output else out_dir / "desmos_render.mp4"

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise RenderError("ffmpeg is required for rendering (macOS: brew install ffmpeg)")
    try:
        import playwright  # noqa: F401
    except ImportError:
        raise RenderError("Rendering needs Playwright: pip install playwright")

    # Original audio, trimmed to the converted section
    if audio is None and data.get("source") and Path(data["source"]).exists():
        audio = data["source"]
    color = color and any("c" in f for f in data["frames"])

    player_url = (out_dir / "player.html").resolve().as_uri() + "?render"
    print(f"Rendering {n} frames at {size[0]}x{size[1]} with {workers} workers ({view} view)...")
    with tempfile.TemporaryDirectory() as tmp:
        frame_dir = Path(tmp)
        asyncio.run(_render_frames(player_url, list(range(n)), size, view, color,
                                   max(1, workers), frame_dir, n, progress))

        cmd = [ffmpeg, "-y", "-loglevel", "error",
               "-framerate", str(fps), "-i", str(frame_dir / "frame_%06d.png")]
        if audio:
            cmd += ["-ss", str(data.get("start", 0)), "-t", str(n / fps), "-i", str(audio),
                    "-map", "0:v", "-map", "1:a?", "-c:a", "aac"]
        cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2", str(output)]
        subprocess.run(cmd, check=True)

    print(f"✓ Saved {output} ({n / fps:.1f}s at {fps:g} fps{', with audio' if audio else ''})")
    return output


def main():
    p = argparse.ArgumentParser(description="Render a converted video (graph + equations) to mp4")
    p.add_argument("out_dir", help="the outputs/<name>_video folder made by video.py")
    p.add_argument("-o", "--output", help="output mp4 path (default: <out_dir>/desmos_render.mp4)")
    p.add_argument("--size", default="1920x1080", help="frame size WIDTHxHEIGHT (default 1920x1080)")
    p.add_argument("--view", choices=["poly", "compact"], default="poly",
                   help="poly = one equation per curve in the panel (default), compact = one list expression")
    p.add_argument("--no-color", action="store_true", help="render black and white even if converted with --color")
    p.add_argument("--workers", type=int, default=4, help="frames rendered in parallel (default 4)")
    p.add_argument("--audio", help="video/audio file to take the soundtrack from "
                                   "(default: the original video, if it still exists)")
    p.add_argument("--no-audio", action="store_true")
    a = p.parse_args()

    w, h = (int(v) for v in a.size.lower().split("x"))
    try:
        render(a.out_dir, a.output, (w, h), a.view, not a.no_color, a.workers,
               audio=False if a.no_audio else a.audio)
    except RenderError as e:
        raise SystemExit(str(e))


if __name__ == "__main__":
    main()

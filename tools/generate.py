#!/usr/bin/env python3
"""
Make the frames and clips for a storyboard on fal.ai, with your own fal key.

Shotkit writes the prompts. This sends them. It is optional: every prompt still works
pasted into a generator by hand. It needs Python 3 and nothing else.

    python tools/generate.py output/ --model flux              # show the plan, spend nothing
    python tools/generate.py output/ --model flux --yes        # make every missing frame
    python tools/generate.py output/ --model kling --yes       # a clip per shot, from its frame
    python tools/generate.py output/ --model flux --shots shot_02,shot_04 --yes
    python tools/generate.py output/ --model fal-ai/nano-banana-2 --prompts nano-banana --yes
    python tools/generate.py --list "image-to-video"           # search fal's models
    python tools/generate.py --selftest

--model is a Shotkit generator name (flux, nano-banana, seedream, ideogram, gpt-image,
kling, seedance, hailuo) or any fal model id. A generator name uses the fal model listed
for it in fal-models.json, which you can edit. For any other fal id, --prompts says which
of Shotkit's prompt files to send.

Nothing is spent without --yes. Without it the command prints what it would send. fal
bills your account for each generation at the price on that model's page.

The key. Set FAL_KEY in the environment, or put a line `FAL_KEY=...` in a file named
.env in the project folder or in the tools folder. It is read, sent to fal and never
printed or written anywhere.

Where things go. A still is saved as frames/round-N/shot_NN.ext, which is where the
critic and the board look. A clip is saved as clips/round-N/shot_NN.mp4. Every request
is written to generations.jsonl with its fal request id as soon as it is submitted, so a
run that is interrupted can still be traced. A frame the critic has reviewed is never
replaced.

How the request is built. Each fal model publishes its inputs. This reads that schema
and fills what the model accepts: the prompt, the aspect ratio in whichever form the
model takes it, one image, PNG when offered, the seed from the prompt file, and for a
video model the shot's frame and its length. A model released next month works without
a change here.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import math
import os
import re
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from _shotkit import IMAGE_EXTS, SHOT_ID_RE, iso_instant, load_json, round_dirs

TOOLS = Path(__file__).resolve().parent
MODELS_FILE = TOOLS / "fal-models.json"
QUEUE = os.environ.get("SHOTKIT_FAL_QUEUE", "https://queue.fal.run")
API = os.environ.get("SHOTKIT_FAL_API", "https://fal.ai/api")
AGENT = "shotkit"

SHOT_HEADER = re.compile(r"^#\s*(?:revision\s+of\s+)?(shot_\d{2,3})\b", re.IGNORECASE)
MIME_EXT = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp", "video/mp4": "mp4"}
EXT_MIME = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "webp": "image/webp"}

# The names fal models use for the picture a video starts from, most common first.
START_IMAGE_KEYS = ("start_image_url", "image_url", "first_frame_url", "first_frame_image", "image")
# The names fal models use for the picture a video ends on.
END_IMAGE_KEYS = ("tail_image_url", "end_image_url", "last_frame_url", "last_frame_image", "end_image")
# project aspect -> fal's named image sizes, for models that take image_size.
IMAGE_SIZES = {
    "16:9": "landscape_16_9", "9:16": "portrait_16_9", "1:1": "square_hd",
    "4:3": "landscape_4_3", "3:4": "portrait_4_3", "4:5": "portrait_4_3",
}


class Stop(Exception):
    """A problem to print as one line and exit on, not a traceback."""


# --------------------------------------------------------------------------
# fal
# --------------------------------------------------------------------------

def find_key(project: Path | None) -> str | None:
    """FAL_KEY from the environment, then from a .env in the project or tools folder."""
    if os.environ.get("FAL_KEY"):
        return os.environ["FAL_KEY"].strip()
    places = [Path.cwd() / ".env", TOOLS / ".env"]
    if project is not None:
        places[:0] = [project / ".env", project.parent / ".env"]
    for path in places:
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            found = re.match(r"\s*(?:export\s+)?FAL_KEY\s*=\s*['\"]?([^'\"\s#]+)", line)
            if found:
                return found.group(1)
    return None


def http(url: str, key: str | None = None, body: dict | None = None, timeout: int = 60):
    headers = {"User-Agent": AGENT, "Accept": "application/json"}
    data = None
    if key:
        headers["Authorization"] = f"Key {key}"
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        detail = err.read().decode("utf-8", "replace")[:400]
        if err.code in (401, 403):
            raise Stop("fal refused the key. Check FAL_KEY, and that the account has credit.") from None
        raise Stop(f"fal answered {err.code} for {url.split('?')[0]}: {detail}") from None
    except urllib.error.URLError as err:
        raise Stop(f"could not reach {urllib.parse.urlparse(url).netloc}: {err.reason}") from None


def model_schema(endpoint: str) -> dict:
    """The input properties a fal model accepts, and which ones it requires."""
    doc = http(f"{API}/openapi/queue/openapi.json?endpoint_id={urllib.parse.quote(endpoint, safe='/')}")
    schemas = (doc.get("components") or {}).get("schemas") or {}
    name = next((k for k in schemas if k.endswith("Input")), None)
    if name is None:
        raise Stop(f"fal has no model called {endpoint}. Search with: sk generate --list <words>")
    spec = schemas[name]
    return {"properties": spec.get("properties") or {}, "required": spec.get("required") or []}


def enum_of(prop: dict) -> list:
    values = list(prop.get("enum") or [])
    for option in prop.get("anyOf") or []:
        values.extend(option.get("enum") or [])
    return values


def is_video(schema: dict) -> bool:
    return any(key in schema["properties"] for key in START_IMAGE_KEYS)


def data_url(frame: Path) -> str:
    mime = EXT_MIME.get(frame.suffix.lstrip(".").lower(), "image/png")
    return f"data:{mime};base64," + base64.b64encode(frame.read_bytes()).decode("ascii")


def build_input(schema: dict, prompt: str, aspect: str, params: dict, frame: Path | None,
                seconds: float, end_frame: Path | None = None) -> dict:
    """Fill the inputs this model accepts. Anything it does not list is left out."""
    props = schema["properties"]
    body: dict = {}
    if "prompt" in props:
        body["prompt"] = prompt

    if "aspect_ratio" in props:
        allowed = enum_of(props["aspect_ratio"])
        if not allowed or aspect in allowed:
            body["aspect_ratio"] = aspect
    elif "image_size" in props and aspect in IMAGE_SIZES:
        allowed = enum_of(props["image_size"])
        if not allowed or IMAGE_SIZES[aspect] in allowed:
            body["image_size"] = IMAGE_SIZES[aspect]

    if "num_images" in props:
        body["num_images"] = 1
    if "output_format" in props and "png" in enum_of(props["output_format"]):
        body["output_format"] = "png"
    if "seed" in props and str(params.get("seed", "")).isdigit():
        body["seed"] = int(params["seed"])
    if "negative_prompt" in props and params.get("negative_prompt"):
        body["negative_prompt"] = params["negative_prompt"]

    start_key = next((k for k in START_IMAGE_KEYS if k in props), None)
    if start_key:
        if frame is None:
            raise Stop("this is a video model and the shot has no frame to start from")
        body[start_key] = data_url(frame)
        end_key = next((k for k in END_IMAGE_KEYS if k in props), None)
        if end_frame is not None and end_key:
            body[end_key] = data_url(end_frame)
        if "duration" in props:
            body["duration"] = pick_duration(props["duration"], seconds)
        # A clip is a silent picture. A model that can add sound bills more for it.
        if "generate_audio" in props:
            body["generate_audio"] = False
    return body


def pick_duration(prop: dict, seconds: float):
    """The shortest length the model offers that covers the shot."""
    want = max(1, math.ceil(seconds))
    numbers = sorted(int(v) for v in enum_of(prop) if str(v).isdigit())
    as_text = any(isinstance(v, str) for v in enum_of(prop)) or prop.get("type") == "string"
    if numbers:
        chosen = next((n for n in numbers if n >= want), numbers[-1])
    else:
        chosen = max(want, int(prop.get("default") or 5) if str(prop.get("default") or "").isdigit() else want)
    return str(chosen) if as_text else chosen


def result_url(result: dict) -> tuple[str, str]:
    """(url, kind) from a fal result: the first image, or the video."""
    for key in ("images", "image", "video", "videos"):
        value = result.get(key)
        if isinstance(value, list) and value:
            value = value[0]
        if isinstance(value, dict) and value.get("url"):
            return (value["url"], "video" if key.startswith("video") else "image")
    raise Stop("fal returned no image or video: " + json.dumps(result)[:300])


def run_request(endpoint: str, key: str, body: dict, on_submit, wait: int = 900) -> dict:
    """Submit to fal's queue, wait for it, and return the result."""
    queued = http(f"{QUEUE}/{endpoint}", key, body)
    request_id = queued.get("request_id")
    if not request_id:
        raise Stop("fal did not return a request id: " + json.dumps(queued)[:300])
    on_submit(request_id)
    status_url = queued.get("status_url") or f"{QUEUE}/{endpoint}/requests/{request_id}/status"
    response_url = queued.get("response_url") or f"{QUEUE}/{endpoint}/requests/{request_id}"
    started = time.time()
    delay = 1.0
    while True:
        status = http(status_url, key)
        state = str(status.get("status") or "").upper()
        if state == "COMPLETED":
            return http(response_url, key)
        if state in ("FAILED", "ERROR", "CANCELLED"):
            raise Stop(f"fal request {request_id} ended {state}: {json.dumps(status)[:300]}")
        if time.time() - started > wait:
            raise Stop(f"fal request {request_id} is still running after {wait}s. It is in generations.jsonl.")
        time.sleep(delay)
        delay = min(delay * 1.4, 6.0)


def download(url: str, dest_stem: Path, kind: str) -> Path:
    last: Exception | None = None
    for attempt in range(6):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": AGENT})
            with urllib.request.urlopen(request, timeout=180) as response:
                mime = (response.headers.get("Content-Type") or "").split(";")[0].strip()
                data = response.read()
            ext = MIME_EXT.get(mime) or Path(urllib.parse.urlparse(url).path).suffix.lstrip(".").lower()
            if ext == "jpeg":
                ext = "jpg"
            if ext not in ("png", "jpg", "webp", "mp4"):
                ext = "mp4" if kind == "video" else "png"
            dest = dest_stem.with_suffix("." + ext)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
            return dest
        except (urllib.error.URLError, OSError) as err:
            last = err
            time.sleep(1.5 * (attempt + 1))
    raise Stop(f"could not download the result: {last}")


# --------------------------------------------------------------------------
# The run on disk
# --------------------------------------------------------------------------

def read_prompts(out_dir: Path, generator: str) -> dict[str, dict]:
    """The newest prompt per shot for one generator: {shot_id: {round, file, body, params}}."""
    found: dict[str, dict] = {}
    for round_no, directory in round_dirs(out_dir, "prompts"):
        for name in (f"{generator}.txt", f"revised-{generator}.txt"):
            path = directory / name
            if not path.is_file():
                continue
            current = None
            for raw in path.read_text(encoding="utf-8").splitlines():
                header = SHOT_HEADER.match(raw)
                if header:
                    current = {"round": round_no, "file": str(path.relative_to(out_dir)), "body": [], "params": {}}
                    found[header.group(1).lower()] = current
                    continue
                if current is None:
                    continue
                if raw.lstrip().startswith("#"):
                    text = raw.lstrip().lstrip("#").strip()
                    if text.lower().startswith("params"):
                        current["params"] = parse_params(text.split(":", 1)[-1])
                    continue
                current["body"].append(raw)
    for entry in found.values():
        entry["body"] = "\n".join(entry["body"]).strip()
    return {shot: entry for shot, entry in found.items() if entry["body"]}


def parse_params(text: str) -> dict:
    """`aspect_ratio=9:16, seed=41207, negative_prompt=text, logos` to a dict."""
    out: dict[str, str] = {}
    key = None
    for part in text.split(","):
        if "=" in part and re.match(r"\s*[A-Za-z_][A-Za-z0-9_]*\s*=", part):
            key, value = part.split("=", 1)
            key = key.strip()
            out[key] = value.strip()
        elif key:
            out[key] += "," + part
    return out


def existing(out_dir: Path, kind: str, round_no: int, shot_id: str) -> Path | None:
    exts = IMAGE_EXTS if kind == "frames" else ("mp4", "mov", "m4v", "webm")
    for ext in exts:
        path = out_dir / kind / f"round-{round_no}" / f"{shot_id}.{ext}"
        if path.exists():
            return path
    return None


def newest_frame(out_dir: Path, shot_id: str) -> Path | None:
    for round_no, _ in reversed(round_dirs(out_dir, "frames")):
        path = existing(out_dir, "frames", round_no, shot_id)
        if path:
            return path
    return None


def bridge_frame(out_dir: Path, shot_id: str, last: bool) -> Path | None:
    """The frame a bridge starts or ends on: a clip's last frame if one was kept, else the shot's frame."""
    if not SHOT_ID_RE.match(shot_id):
        return None
    kept = out_dir / "media" / "ends" / f"{shot_id}.jpg"
    if last and kept.exists():
        return kept
    return newest_frame(out_dir, shot_id)


def load_models() -> dict:
    data, err = load_json(MODELS_FILE)
    if err or not isinstance(data, dict):
        return {}
    return {k: v for k, v in (data.get("models") or {}).items() if isinstance(v, str)}


def plan(out_dir: Path, model: str, prompts_from: str | None, only: set[str] | None,
         replace: bool) -> dict:
    shots_doc, err = load_json(out_dir / "shots.json")
    if err or not isinstance(shots_doc, dict):
        raise Stop(err or "shots.json is not readable")
    models = load_models()
    generator = prompts_from or (model if model in models else None)
    endpoint = models.get(model, model)
    if "/" not in endpoint:
        known = ", ".join(sorted(models)) or "none listed"
        raise Stop(f"'{model}' is not a generator Shotkit maps to fal ({known}) and not a fal model id.")
    if generator is None:
        raise Stop(f"{endpoint} is a fal model id, so say which prompt file to send: --prompts flux")
    prompts = read_prompts(out_dir, generator)
    if not prompts:
        raise Stop(f"no prompts for '{generator}' in {out_dir}/prompts. Ask Claude: write {generator} prompts.")

    schema = model_schema(endpoint)
    video = is_video(schema)
    kind = "clips" if video else "frames"
    aspect = (shots_doc.get("project") or {}).get("aspect") or "16:9"
    jobs, skipped = [], []
    for shot in shots_doc.get("shots") or []:
        shot_id = shot.get("id")
        if not isinstance(shot_id, str) or not SHOT_ID_RE.match(shot_id):
            continue
        if only and shot_id not in only:
            continue
        entry = prompts.get(shot_id)
        if entry is None:
            skipped.append((shot_id, f"no {generator} prompt"))
            continue
        round_no = entry["round"]
        have = existing(out_dir, kind, round_no, shot_id)
        reviewed = (out_dir / "critiques" / f"round-{round_no}" / f"{shot_id}.critique.json").exists()
        if have and not video and reviewed:
            skipped.append((shot_id, f"round {round_no} frame is reviewed and stays as it is"))
            continue
        if have and not replace:
            skipped.append((shot_id, f"already has {have.relative_to(out_dir)}"))
            continue
        frame = newest_frame(out_dir, shot_id) if video else None
        end_frame = None
        source = shot.get("source") if isinstance(shot.get("source"), dict) else {}
        if not video and source.get("type") == "own":
            skipped.append((shot_id, "uses your own media"))
            continue
        if video and source.get("type") == "generate" and source.get("start") and source.get("end"):
            # A bridge: it starts where one shot ends and ends where the next begins.
            frame = bridge_frame(out_dir, str(source["start"]), last=True) or frame
            end_frame = bridge_frame(out_dir, str(source["end"]), last=False)
            if end_frame is not None and not any(k in schema["properties"] for k in END_IMAGE_KEYS):
                skipped.append((shot_id, f"{endpoint} takes no end frame, so it cannot bridge two shots. Use one that does."))
                continue
        if video and frame is None:
            skipped.append((shot_id, "no frame to start the clip from"))
            continue
        seconds = float(shot.get("end") or 0) - float(shot.get("start") or 0)
        jobs.append({
            "shot": shot_id, "round": round_no, "prompt_file": entry["file"],
            "prompt": entry["body"], "params": entry["params"], "frame": frame,
            "end_frame": end_frame, "seconds": seconds,
            "dest": out_dir / kind / f"round-{round_no}" / shot_id,
            "input": build_input(schema, entry["body"], aspect, entry["params"], frame, seconds, end_frame),
        })
    return {"endpoint": endpoint, "generator": generator, "video": video, "kind": kind,
            "aspect": aspect, "jobs": jobs, "skipped": skipped}


def describe(job: dict) -> str:
    shown = {k: v for k, v in job["input"].items() if k != "prompt" and not str(v).startswith("data:")}
    if job["frame"] is not None:
        shown["from"] = job["frame"].name
    if job.get("end_frame") is not None:
        shown["to"] = job["end_frame"].name
    return ", ".join(f"{k}={v}" for k, v in shown.items())


def execute(out_dir: Path, the_plan: dict, key: str, workers: int) -> int:
    log_path = out_dir / "generations.jsonl"
    lock = threading.Lock()

    def log(entry: dict) -> None:
        with lock, log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry) + "\n")

    def one(job: dict) -> tuple[str, str | None]:
        base = {
            "shot": job["shot"], "round": job["round"], "model": the_plan["endpoint"],
            "prompt_file": job["prompt_file"],
            "prompt_sha256": hashlib.sha256(job["prompt"].encode("utf-8")).hexdigest(),
        }
        try:
            result = run_request(
                the_plan["endpoint"], key, job["input"],
                lambda rid: log({**base, "at": iso_instant(), "event": "submitted", "request_id": rid}),
            )
            url, kind = result_url(result)
            path = download(url, job["dest"], kind)
            log({**base, "at": iso_instant(), "event": "saved", "path": str(path.relative_to(out_dir)),
                 "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
            with lock:
                print(f"  saved {path.relative_to(out_dir)}")
            return (job["shot"], None)
        except Stop as err:
            log({**base, "at": iso_instant(), "event": "failed", "error": str(err)})
            with lock:
                print(f"  FAIL  {job['shot']}: {err}")
            return (job["shot"], str(err))

    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        results = list(pool.map(one, the_plan["jobs"]))
    failed = [shot for shot, err in results if err]
    made = len(results) - len(failed)
    what = "clip" if the_plan["video"] else "frame"
    print(f"  {made} {what}{'' if made == 1 else 's'} saved" + (f", {len(failed)} failed" if failed else "") + ".")
    return 1 if failed else 0


def list_models(words: str) -> int:
    doc = http(f"{API}/models?keywords={urllib.parse.quote(words)}&limit=20")
    items = doc.get("items") or []
    if not items:
        print(f"  fal lists no model for '{words}'.")
        return 0
    for item in items:
        print(f"  {item.get('id', ''):58} {item.get('category', '')}")
    print("\n  Use one with: sk generate output/ --model <id> --prompts <generator>")
    return 0


# --------------------------------------------------------------------------
# Selftest: a fake fal on localhost, so nothing is spent and no key is needed
# --------------------------------------------------------------------------

def selftest() -> int:
    global QUEUE, API
    import shutil
    import tempfile
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    from _shotkit import REPO_ROOT

    worked = REPO_ROOT / "skills" / "visual-asset-critic" / "examples" / "worked-run"
    png = (worked / "frames" / "round-1" / "shot_01.png").read_bytes()
    seen: list[dict] = []
    polls = {"n": 0}

    class Fake(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def reply(self, payload, kind="application/json", status=200):
            body = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
            self.send_response(status)
            self.send_header("Content-Type", kind)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            base = f"http://127.0.0.1:{self.server.server_address[1]}"
            if "/openapi/" in self.path:
                video = "video" in self.path
                props = {"prompt": {"type": "string"}}
                if video:
                    props.update({"start_image_url": {"type": "string"}, "tail_image_url": {"type": "string"},
                                  "duration": {"type": "string", "enum": ["3", "5", "10"]}})
                else:
                    props.update({"image_size": {"anyOf": [{"enum": ["portrait_16_9", "landscape_16_9"]}]},
                                  "num_images": {"type": "integer"}, "seed": {"type": "integer"},
                                  "output_format": {"enum": ["jpeg", "png"]}})
                self.reply({"components": {"schemas": {"XInput": {"properties": props, "required": ["prompt"]}}}})
            elif self.path.endswith("/status"):
                polls["n"] += 1
                self.reply({"status": "COMPLETED" if polls["n"] > 1 else "IN_PROGRESS"})
            elif "/requests/" in self.path:
                if "video" in self.path:
                    self.reply({"video": {"url": base + "/file.mp4"}})
                else:
                    self.reply({"images": [{"url": base + "/file.png"}]})
            elif self.path == "/file.png":
                self.reply(png, "image/png")
            elif self.path == "/file.mp4":
                self.reply(b"\x00\x00\x00\x18ftypmp42", "video/mp4")
            else:
                self.reply({"error": "no"}, status=404)

        def do_POST(self):
            if self.headers.get("Authorization") != "Key test-key":
                self.reply({"detail": "bad key"}, status=401)
                return
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)))
            seen.append({"path": self.path, "body": body})
            base = f"http://127.0.0.1:{self.server.server_address[1]}"
            rid = f"req-{len(seen)}"
            self.reply({"request_id": rid, "status_url": f"{base}{self.path}/requests/{rid}/status",
                        "response_url": f"{base}{self.path}/requests/{rid}"})

    server = ThreadingHTTPServer(("127.0.0.1", 0), Fake)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    real_queue, real_api = QUEUE, API
    QUEUE, API = base, base
    checks: list[tuple[str, bool]] = []
    try:
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp) / "run"
            shutil.copytree(worked, run)
            # round 2 of shot_02 is reviewed; round 1 of shot_01 is reviewed too.
            reviewed = plan(run, "test/image", "flux", None, replace=True)
            checks.append(("a reviewed frame is never regenerated", not reviewed["jobs"] and len(reviewed["skipped"]) == 2))

            shutil.rmtree(run / "critiques")
            kept = plan(run, "test/image", "flux", None, replace=False)
            checks.append(("a shot that has a frame is skipped", not kept["jobs"]))

            shutil.rmtree(run / "frames")
            fresh = plan(run, "test/image", "flux", None, replace=False)
            job = {j["shot"]: j for j in fresh["jobs"]}
            checks.append(("plans one job per shot with a prompt", sorted(job) == ["shot_01", "shot_02"]))
            checks.append(("sends the newest prompt, from the revision round", job["shot_02"]["round"] == 2
                           and job["shot_02"]["prompt"].startswith("Medium close-up")))
            checks.append(("a prompt carries no comment line", "#" not in job["shot_01"]["prompt"]))
            checks.append(("maps 9:16 to the model's own size name", job["shot_01"]["input"].get("image_size") == "portrait_16_9"))
            checks.append(("asks for one PNG", job["shot_01"]["input"].get("num_images") == 1
                           and job["shot_01"]["input"].get("output_format") == "png"))
            checks.append(("leaves out inputs the model does not list", "aspect_ratio" not in job["shot_01"]["input"]))

            bad = None
            try:
                run_request("test/image", "wrong", {"prompt": "x"}, lambda rid: None)
            except Stop as err:
                bad = str(err)
            checks.append(("a refused key is reported plainly", bad is not None and "refused the key" in bad))

            status = execute(run, fresh, "test-key", workers=2)
            saved = sorted(p.name for p in (run / "frames").rglob("*.png"))
            log = [json.loads(line) for line in (run / "generations.jsonl").read_text().splitlines()]
            checks.append(("saves each frame where the board looks", status == 0
                           and (run / "frames/round-1/shot_01.png").exists()
                           and (run / "frames/round-2/shot_02.png").exists() and len(saved) == 2))
            checks.append(("logs the request id on submit and the hash on save",
                           sum(1 for e in log if e["event"] == "submitted" and e.get("request_id")) == 2
                           and sum(1 for e in log if e["event"] == "saved" and len(e.get("sha256", "")) == 64) == 2))
            checks.append(("the key is never written to the log", "test-key" not in (run / "generations.jsonl").read_text()))

            clips = plan(run, "test/video", "flux", {"shot_02"}, replace=False)
            sent = clips["jobs"][0]["input"]
            checks.append(("a video model starts from the shot's frame", str(sent.get("start_image_url", "")).startswith("data:image/png;base64,")))
            checks.append(("and gets the shortest length that covers the shot", sent.get("duration") == "5"))
            execute(run, clips, "test-key", workers=1)
            checks.append(("saves the clip beside the frames", (run / "clips/round-2/shot_02.mp4").exists()))

            # your own media, and a bridge between two shots
            doc = json.loads((run / "shots.json").read_text())
            by_id = {s["id"]: s for s in doc["shots"]}
            by_id["shot_01"]["source"] = {"type": "own", "media": "m01"}
            by_id["shot_02"]["source"] = {"type": "generate", "why": "joins the two", "start": "shot_01", "end": "shot_01"}
            (run / "shots.json").write_text(json.dumps(doc))
            (run / "media/ends").mkdir(parents=True)
            (run / "media/ends/shot_01.jpg").write_bytes(b"\xff\xd8last")
            (run / "frames/round-1/shot_01.png").unlink()
            own = plan(run, "test/image", "flux", {"shot_01"}, replace=True)
            checks.append(("a shot on your own media is never generated", not own["jobs"] and "your own media" in own["skipped"][0][1]))
            (run / "frames/round-1/shot_01.png").write_bytes(png)
            bridge = plan(run, "test/video", "flux", {"shot_02"}, replace=True)["jobs"][0]["input"]
            checks.append(("a bridge starts on the last frame of one shot", bridge.get("start_image_url", "").startswith("data:image/jpeg;base64,")))
            checks.append(("and ends on the first frame of the next", bridge.get("tail_image_url", "").startswith("data:image/png;base64,")))

            unknown = None
            try:
                plan(run, "midjourney", None, None, replace=False)
            except Stop as err:
                unknown = str(err)
            checks.append(("an unmapped generator says so", unknown is not None and "not a generator" in unknown))
            checks.append(("parses a params line with commas in a value",
                           parse_params("seed=7, negative_prompt=text, logos, faces, ar=9:16")
                           == {"seed": "7", "negative_prompt": "text, logos, faces", "ar": "9:16"}))
    finally:
        QUEUE, API = real_queue, real_api
        server.shutdown()

    ok = True
    for label, passed in checks:
        print(f"  {'ok  ' if passed else 'FAIL'}  selftest: {label}")
        ok = ok and passed
    print()
    print("Selftest passed." if ok else "Selftest FAILED.")
    return 0 if ok else 1


def main() -> int:
    p = argparse.ArgumentParser(description="Make a storyboard's frames and clips on fal.ai.")
    p.add_argument("output_dir", nargs="?", type=Path, help="Folder that holds shots.json")
    p.add_argument("--model", help="A Shotkit generator name, or a fal model id")
    p.add_argument("--prompts", help="Which generator's prompt file to send (default: the model's own)")
    p.add_argument("--shots", help="Only these shots, comma separated: shot_02,shot_04")
    p.add_argument("--yes", action="store_true", help="Send the requests. Without it, only the plan is shown")
    p.add_argument("--replace", action="store_true", help="Make a shot again even if it has an unreviewed frame")
    p.add_argument("--workers", type=int, default=3, help="Requests to run at once (default 3)")
    p.add_argument("--list", metavar="WORDS", help="Search fal's models and exit")
    p.add_argument("--selftest", action="store_true", help="Prove the tool's guarantees against a fake fal")
    args = p.parse_args()

    try:
        if args.selftest:
            return selftest()
        if args.list:
            return list_models(args.list)
        if args.output_dir is None or not args.model:
            p.error("give the output folder and --model, for example: output/ --model flux")
        out_dir: Path = args.output_dir
        if not (out_dir / "shots.json").exists():
            raise Stop(f"shots.json not found in {out_dir}")
        only = {s.strip() for s in args.shots.split(",") if s.strip()} if args.shots else None
        the_plan = plan(out_dir, args.model, args.prompts, only, args.replace)

        what = "clip" if the_plan["video"] else "frame"
        count = len(the_plan["jobs"])
        print(f"  model    {the_plan['endpoint']}")
        print(f"  prompts  {the_plan['generator']}")
        for job in the_plan["jobs"]:
            print(f"  make     {job['shot']}  round {job['round']}  {describe(job)}")
        for shot, why in the_plan["skipped"]:
            print(f"  skip     {shot}  {why}")
        if not count:
            print(f"  Nothing to make.")
            return 0
        if not args.yes:
            print(f"\n  This would send {count} request{'' if count == 1 else 's'} to fal, one {what} each.")
            print(f"  fal bills your account. The price is on https://fal.ai/models/{the_plan['endpoint']}")
            print("  Nothing was sent. Add --yes to run it.")
            return 0
        key = find_key(out_dir.resolve())
        if not key:
            raise Stop("no fal key found. Set FAL_KEY, or put FAL_KEY=... in a .env file in this folder. "
                       "Get a key at https://fal.ai/dashboard/keys")
        print(f"\n  sending {count} request{'' if count == 1 else 's'} to fal")
        return execute(out_dir, the_plan, key, args.workers)
    except Stop as err:
        print(f"ERROR: {err}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

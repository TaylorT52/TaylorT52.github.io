#!/usr/bin/env python3
"""Local-only editor and publisher for the Summer Projects page."""

from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import hmac
import json
import mimetypes
import os
from pathlib import Path
import re
import secrets
import subprocess
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlparse


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "summer-updates.json"
TOKEN_PATH = ROOT / ".summer-portal-token"
IMAGE_DIR = ROOT / "imgs" / "summer"
MAX_BODY_BYTES = 12 * 1024 * 1024
BUILT_IN_PROJECTS = {"ender3", "apartment-finder"}
SETUP_FILES = (
    ".gitignore",
    "README.md",
    "data/summer-updates.json",
    "manage-summer",
    "projpages/project12.html",
    "style.css",
    "summer-updates.js",
    "tools/summer_portal.py",
)
ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}


PORTAL_HTML = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Summer Page Studio</title>
  <style>
    :root {
      color-scheme: light;
      --ink: #17201e;
      --muted: #65716d;
      --paper: #f4f2ec;
      --card: #fffefa;
      --line: #d9d8d1;
      --green: #176b5b;
      --green-dark: #105044;
      --danger: #a23a32;
      --shadow: 0 18px 55px rgba(31, 42, 39, .09);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background:
        radial-gradient(circle at 15% 0%, rgba(23, 107, 91, .08), transparent 28rem),
        var(--paper);
      color: var(--ink);
      font: 15px/1.5 Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
    }
    button, input, select, textarea { font: inherit; }
    button { cursor: pointer; }
    .shell { width: min(1180px, calc(100% - 32px)); margin: 0 auto; padding: 42px 0 70px; }
    header { display: flex; align-items: flex-end; justify-content: space-between; gap: 24px; margin-bottom: 28px; }
    .eyebrow { margin: 0 0 5px; color: var(--green); font-size: 12px; font-weight: 800; letter-spacing: .13em; text-transform: uppercase; }
    h1 { margin: 0; font: 700 clamp(30px, 4vw, 48px)/1.08 Georgia, serif; letter-spacing: -.025em; }
    .subtitle { margin: 8px 0 0; color: var(--muted); }
    .computer-only { display: flex; align-items: center; gap: 8px; color: var(--green-dark); font-size: 13px; font-weight: 700; }
    .dot { width: 8px; height: 8px; border-radius: 50%; background: #2c9a72; box-shadow: 0 0 0 4px rgba(44,154,114,.13); }
    .layout { display: grid; grid-template-columns: minmax(0, 1.25fr) minmax(300px, .75fr); gap: 22px; align-items: start; }
    .card { border: 1px solid var(--line); border-radius: 18px; background: var(--card); box-shadow: var(--shadow); }
    .editor { padding: 28px; }
    h2 { margin: 0 0 22px; font-size: 18px; }
    .field { margin-bottom: 18px; }
    .field-row { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
    label { display: block; margin-bottom: 7px; font-size: 13px; font-weight: 750; }
    input, select, textarea {
      width: 100%; border: 1px solid #cfcec7; border-radius: 10px; background: #fff;
      color: var(--ink); padding: 11px 12px; outline: none; transition: border .15s, box-shadow .15s;
    }
    input:focus, select:focus, textarea:focus { border-color: var(--green); box-shadow: 0 0 0 3px rgba(23,107,91,.11); }
    textarea { min-height: 210px; resize: vertical; }
    .hint { margin: 6px 0 0; color: var(--muted); font-size: 12px; }
    .photos { border-top: 1px solid var(--line); margin-top: 24px; padding-top: 22px; }
    .photo-fields { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
    .photo-list { display: grid; gap: 9px; margin: 13px 0; }
    .photo-chip { display: flex; justify-content: space-between; gap: 12px; padding: 9px 11px; border: 1px solid var(--line); border-radius: 9px; color: var(--muted); font-size: 13px; }
    .actions { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 25px; }
    .btn { border: 1px solid var(--line); border-radius: 999px; background: white; padding: 10px 16px; color: var(--ink); font-weight: 750; }
    .btn:hover { border-color: #9eaaa6; }
    .btn-primary { border-color: var(--green); background: var(--green); color: white; }
    .btn-primary:hover { border-color: var(--green-dark); background: var(--green-dark); }
    .btn-danger { color: var(--danger); }
    .btn-small { padding: 5px 9px; font-size: 12px; }
    .side { display: grid; gap: 16px; }
    .panel { padding: 20px; }
    .panel h2 { margin-bottom: 14px; }
    .status { min-height: 44px; margin: 0 0 13px; border-radius: 10px; background: #f1f4ef; padding: 12px; color: var(--muted); font-size: 13px; white-space: pre-wrap; }
    .status.success { background: #e9f4ee; color: #1c654f; }
    .status.error { background: #f8ebe8; color: #8b312b; }
    .update-list { display: grid; gap: 10px; }
    .update-item { border: 1px solid var(--line); border-radius: 12px; padding: 13px; }
    .update-item strong { display: block; margin-bottom: 3px; }
    .update-meta { color: var(--muted); font-size: 12px; }
    .update-buttons { display: flex; gap: 6px; margin-top: 10px; }
    .empty { color: var(--muted); font-size: 13px; }
    .publishing { opacity: .62; pointer-events: none; }
    @media (max-width: 820px) {
      .layout { grid-template-columns: 1fr; }
      header { align-items: flex-start; flex-direction: column; }
    }
    @media (max-width: 520px) {
      .shell { width: min(100% - 20px, 1180px); padding-top: 24px; }
      .editor { padding: 20px; }
      .field-row, .photo-fields { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <main class="shell">
    <header>
      <div>
        <p class="eyebrow">Local publishing desk</p>
        <h1>Summer Page Studio</h1>
        <p class="subtitle">Write an update, preview it, and publish when it feels right.</p>
      </div>
      <div class="computer-only"><span class="dot"></span>Available only on this computer</div>
    </header>

    <div class="layout">
      <form class="card editor" id="editor">
        <h2 id="form-title">New update</h2>
        <div class="field">
          <label for="kind">I’m adding</label>
          <select id="kind">
            <option value="update">An update to a project</option>
            <option value="project">A brand-new project</option>
          </select>
        </div>
        <div class="field-row">
          <div class="field" id="project-field">
            <label for="project">Project to update</label>
            <select id="project">
              <option value="ender3">Ender 3 Printer</option>
              <option value="apartment-finder">Apartment Finder</option>
              <option value="__new__">＋ Create a brand-new project…</option>
            </select>
          </div>
          <div class="field">
            <label for="date">Date</label>
            <input id="date" type="date" required>
          </div>
        </div>
        <div class="field">
          <label for="title" id="title-label">Update title</label>
          <input id="title" maxlength="120" placeholder="A first successful print" required>
        </div>
        <div class="field">
          <label for="body" id="body-label">What changed?</label>
          <textarea id="body" maxlength="12000" placeholder="Write naturally. Leave a blank line between paragraphs." required></textarea>
          <p class="hint">Blank lines become separate paragraphs on the published page.</p>
        </div>

        <section class="photos">
          <h2>Photos <span class="hint">(optional)</span></h2>
          <div class="field">
            <label for="photo">Choose a photo</label>
            <input id="photo" type="file" accept="image/jpeg,image/png,image/webp,image/gif">
          </div>
          <div class="photo-fields">
            <div>
              <label for="caption">Caption</label>
              <input id="caption" maxlength="220" placeholder="What we're looking at">
            </div>
            <div>
              <label for="alt">Image description</label>
              <input id="alt" maxlength="220" placeholder="Describe it for accessibility">
            </div>
          </div>
          <button class="btn" id="add-photo" type="button">Add photo</button>
          <div class="photo-list" id="photo-list"></div>
        </section>

        <div class="actions">
          <button class="btn btn-primary" id="save-draft" type="submit">Save draft</button>
          <button class="btn" id="reset" type="button">Clear form</button>
        </div>
      </form>

      <aside class="side">
        <section class="card panel">
          <h2>Publish</h2>
          <p class="status" id="status">Loading your summer page…</p>
          <div class="actions">
            <button class="btn btn-primary" id="publish" type="button">Publish to website</button>
            <button class="btn" id="preview" type="button">Preview page</button>
          </div>
          <p class="hint">Publishing commits only summer-page files and pushes them to GitHub Pages.</p>
        </section>
        <section class="card panel">
          <h2>Added projects</h2>
          <div class="update-list" id="project-list"></div>
        </section>
        <section class="card panel">
          <h2>Saved updates</h2>
          <div class="update-list" id="update-list"></div>
        </section>
      </aside>
    </div>
  </main>

  <script>
    const state = { data: null, editingId: null, editingKind: null, images: [], saving: false };
    const $ = (id) => document.getElementById(id);
    const tokenFromUrl = new URLSearchParams(location.search).get("token");
    if (tokenFromUrl) {
      localStorage.setItem("summerPortalToken", tokenFromUrl);
      history.replaceState({}, "", "/");
    }
    const token = localStorage.getItem("summerPortalToken") || "";

    async function api(path, options = {}) {
      const response = await fetch(path, {
        ...options,
        headers: { "X-Portal-Token": token, "Content-Type": "application/json", ...(options.headers || {}) },
      });
      const payload = await response.json().catch(() => ({ error: "Unexpected server response" }));
      if (!response.ok) throw new Error(payload.error || "Request failed");
      return payload;
    }

    function setStatus(message, type = "") {
      $("status").textContent = message;
      $("status").className = `status ${type}`;
    }

    function resetForm(kind = "update") {
      state.editingId = null;
      state.editingKind = null;
      state.images = [];
      $("editor").reset();
      $("kind").value = kind;
      $("date").value = new Date().toISOString().slice(0, 10);
      setFormMode(kind);
      renderPhotos();
    }

    function setFormMode(kind) {
      const isProject = kind === "project";
      $("form-title").textContent = isProject ? "New project" : "New update";
      $("project-field").hidden = isProject;
      $("title-label").textContent = isProject ? "Project title" : "Update title";
      $("body-label").textContent = isProject ? "What are you building?" : "What changed?";
      $("title").placeholder = isProject ? "My new summer project" : "A first successful print";
    }

    function renderPhotos() {
      $("photo-list").replaceChildren(...state.images.map((image, index) => {
        const row = document.createElement("div");
        row.className = "photo-chip";
        const text = document.createElement("span");
        text.textContent = image.caption || image.src.split("/").pop();
        const remove = document.createElement("button");
        remove.type = "button";
        remove.className = "btn btn-small btn-danger";
        remove.textContent = "Remove";
        remove.onclick = () => { state.images.splice(index, 1); renderPhotos(); };
        row.append(text, remove);
        return row;
      }));
    }

    function projectName(value) {
      if (value === "ender3") return "Ender 3 Printer";
      if (value === "apartment-finder") return "Apartment Finder";
      return state.data.projects.find((project) => project.id === value)?.title || "Unknown project";
    }

    function refreshProjectOptions(selectedValue) {
      const projectOptions = [
        ["ender3", "Ender 3 Printer"],
        ["apartment-finder", "Apartment Finder"],
        ...state.data.projects
          .slice()
          .reverse()
          .map((project) => [project.id, project.title]),
      ].map(([value, label]) => {
        const option = document.createElement("option");
        option.value = value;
        option.textContent = label;
        return option;
      });
      const createOption = document.createElement("option");
      createOption.value = "__new__";
      createOption.textContent = "＋ Create a brand-new project…";
      const options = [...projectOptions, createOption];
      $("project").replaceChildren(...options);
      if (selectedValue && options.some((option) => option.value === selectedValue)) {
        $("project").value = selectedValue;
      }
    }

    function itemCard(item, kind) {
      const card = document.createElement("article");
      card.className = "update-item";
      const title = document.createElement("strong");
      title.textContent = item.title;
      const meta = document.createElement("div");
      meta.className = "update-meta";
      meta.textContent = kind === "project" ? `New project · ${item.date}` : `${projectName(item.project)} · ${item.date}`;
      const buttons = document.createElement("div");
      buttons.className = "update-buttons";
      const edit = document.createElement("button");
      edit.className = "btn btn-small";
      edit.type = "button";
      edit.textContent = "Edit";
      edit.onclick = () => editItem(item.id, kind);
      const remove = document.createElement("button");
      remove.className = "btn btn-small btn-danger";
      remove.type = "button";
      remove.textContent = "Delete";
      remove.onclick = () => deleteItem(item.id, kind);
      buttons.append(edit, remove);
      card.append(title, meta, buttons);
      return card;
    }

    function renderItems() {
      const projects = state.data.projects.slice().reverse();
      if (!projects.length) {
        const empty = document.createElement("p");
        empty.className = "empty";
        empty.textContent = "No new projects added through the portal yet.";
        $("project-list").replaceChildren(empty);
      } else {
        $("project-list").replaceChildren(...projects.map((project) => itemCard(project, "project")));
      }

      const updates = state.data.updates.slice().sort((a, b) => b.date.localeCompare(a.date));
      if (!updates.length) {
        const empty = document.createElement("p");
        empty.className = "empty";
        empty.textContent = "No portal-written updates yet.";
        $("update-list").replaceChildren(empty);
        return;
      }
      $("update-list").replaceChildren(...updates.map((update) => itemCard(update, "update")));
    }

    function editItem(id, kind) {
      const collection = kind === "project" ? state.data.projects : state.data.updates;
      const item = collection.find((candidate) => candidate.id === id);
      if (!item) return;
      state.editingId = id;
      state.editingKind = kind;
      state.images = structuredClone(item.images || []);
      $("kind").value = kind;
      setFormMode(kind);
      $("form-title").textContent = kind === "project" ? "Edit project" : "Edit update";
      if (kind === "update") $("project").value = item.project;
      $("date").value = item.date;
      $("title").value = item.title;
      $("body").value = item.body;
      renderPhotos();
      scrollTo({ top: 0, behavior: "smooth" });
    }

    async function persist(message) {
      state.data.updatedAt = new Date().toISOString();
      await api("/api/content", { method: "POST", body: JSON.stringify(state.data) });
      refreshProjectOptions();
      renderItems();
      setStatus(message, "success");
    }

    async function deleteItem(id, kind) {
      const linkedUpdates = kind === "project"
        ? state.data.updates.filter((update) => update.project === id).length
        : 0;
      const detail = linkedUpdates
        ? ` This will also delete ${linkedUpdates} update${linkedUpdates === 1 ? "" : "s"} attached to it.`
        : "";
      if (!confirm(`Delete this ${kind} from the next published version?${detail}`)) return;
      if (kind === "project") {
        state.data.projects = state.data.projects.filter((item) => item.id !== id);
        state.data.updates = state.data.updates.filter((update) => update.project !== id);
      } else {
        state.data.updates = state.data.updates.filter((item) => item.id !== id);
      }
      await persist(`${kind === "project" ? "Project" : "Update"} deleted. Publish when you’re ready.`);
      if (state.editingId === id) resetForm();
    }

    $("add-photo").onclick = async () => {
      const file = $("photo").files[0];
      if (!file) return setStatus("Choose a photo first.", "error");
      setStatus("Uploading photo…");
      const data = await new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = reject;
        reader.readAsDataURL(file);
      });
      try {
        const result = await api("/api/upload", {
          method: "POST",
          body: JSON.stringify({ name: file.name, data, caption: $("caption").value, alt: $("alt").value }),
        });
        state.images.push(result.image);
        $("photo").value = "";
        $("caption").value = "";
        $("alt").value = "";
        renderPhotos();
        setStatus("Photo added to this draft.", "success");
      } catch (error) {
        setStatus(error.message, "error");
      }
    };

    $("editor").onsubmit = async (event) => {
      event.preventDefault();
      if (state.saving) return;
      state.saving = true;
      $("save-draft").disabled = true;
      const kind = $("kind").value;
      const item = {
        id: state.editingId || `${kind}-${crypto.randomUUID()}`,
        date: $("date").value,
        title: $("title").value.trim(),
        body: $("body").value.trim(),
        images: state.images,
      };
      if (kind === "update") item.project = $("project").value;
      const collection = kind === "project" ? state.data.projects : state.data.updates;
      const index = collection.findIndex((candidate) => candidate.id === item.id);
      if (index >= 0) collection[index] = item;
      else collection.push(item);
      try {
        await persist(`${kind === "project" ? "Project" : "Update"} saved locally. Preview it or publish when ready.`);
        if (kind === "project") {
          resetForm("update");
          refreshProjectOptions(item.id);
          setStatus(`“${item.title}” is saved and selected. You can write its first update now.`, "success");
        } else {
          resetForm();
        }
      } catch (error) {
        setStatus(error.message, "error");
      } finally {
        state.saving = false;
        $("save-draft").disabled = false;
      }
    };

    $("reset").onclick = () => resetForm();
    $("kind").onchange = () => resetForm($("kind").value);
    $("project").onchange = () => {
      if ($("project").value === "__new__") resetForm("project");
    };
    $("preview").onclick = () => window.open("/projpages/project12.html?preview=1", "_blank");
    $("publish").onclick = async () => {
      if (!confirm("Publish saved summer updates to your live website?")) return;
      document.body.classList.add("publishing");
      setStatus("Committing and pushing to GitHub Pages…");
      try {
        const result = await api("/api/publish", { method: "POST", body: "{}" });
        setStatus(result.message, "success");
      } catch (error) {
        setStatus(error.message, "error");
      } finally {
        document.body.classList.remove("publishing");
      }
    };

    (async () => {
      try {
        state.data = await api("/api/content");
        state.data.projects ||= [];
        state.data.updates ||= [];
        refreshProjectOptions();
        renderItems();
        resetForm();
        setStatus("Ready. Changes stay on this computer until you publish.");
      } catch (error) {
        setStatus(`${error.message}\nRestart ./manage-summer to get a fresh secure link.`, "error");
      }
    })();
  </script>
</body>
</html>"""


def load_or_create_token() -> str:
    if TOKEN_PATH.exists():
        token = TOKEN_PATH.read_text(encoding="utf-8").strip()
        if len(token) >= 32:
            return token
    token = secrets.token_urlsafe(32)
    TOKEN_PATH.write_text(token + "\n", encoding="utf-8")
    TOKEN_PATH.chmod(0o600)
    return token


def run_git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ("git", *args),
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


class PortalHandler(BaseHTTPRequestHandler):
    server_version = "SummerPortal/1.0"

    @property
    def token(self) -> str:
        return self.server.portal_token  # type: ignore[attr-defined]

    def log_message(self, message: str, *args: object) -> None:
        sys.stdout.write(f"{self.address_string()} - {message % args}\n")

    def send_json(self, payload: object, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def send_bytes(self, body: bytes, content_type: str) -> None:
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def authorized(self) -> bool:
        supplied = self.headers.get("X-Portal-Token", "")
        return bool(supplied) and hmac.compare_digest(supplied, self.token)

    def require_authorization(self) -> bool:
        if self.authorized():
            return True
        self.send_json({"error": "This portal link is not authorized."}, HTTPStatus.UNAUTHORIZED)
        return False

    def read_json(self) -> dict:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError as error:
            raise ValueError("Invalid request size.") from error
        if length <= 0 or length > MAX_BODY_BYTES:
            raise ValueError("Request is empty or too large.")
        try:
            value = json.loads(self.rfile.read(length))
        except json.JSONDecodeError as error:
            raise ValueError("Invalid JSON request.") from error
        if not isinstance(value, dict):
            raise ValueError("Expected a JSON object.")
        return value

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/":
            self.send_bytes(PORTAL_HTML.encode("utf-8"), "text/html; charset=utf-8")
            return
        if path == "/api/content":
            if not self.require_authorization():
                return
            try:
                self.send_json(json.loads(DATA_PATH.read_text(encoding="utf-8")))
            except (OSError, json.JSONDecodeError) as error:
                self.send_json({"error": f"Could not read updates: {error}"}, HTTPStatus.INTERNAL_SERVER_ERROR)
            return
        self.serve_static(path)

    def serve_static(self, request_path: str) -> None:
        relative = unquote(request_path).lstrip("/")
        candidate = (ROOT / relative).resolve()
        try:
            candidate.relative_to(ROOT)
        except ValueError:
            self.send_error(HTTPStatus.FORBIDDEN)
            return
        if not candidate.is_file() or candidate.name == TOKEN_PATH.name or ".git" in candidate.parts:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        content_type = mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
        try:
            self.send_bytes(candidate.read_bytes(), content_type)
        except OSError:
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR)

    def do_POST(self) -> None:
        if not self.require_authorization():
            return
        path = urlparse(self.path).path
        try:
            payload = self.read_json()
            if path == "/api/content":
                self.save_content(payload)
            elif path == "/api/upload":
                self.upload_image(payload)
            elif path == "/api/publish":
                self.publish()
            else:
                self.send_json({"error": "Unknown endpoint."}, HTTPStatus.NOT_FOUND)
        except ValueError as error:
            self.send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
        except OSError as error:
            self.send_json({"error": f"File operation failed: {error}"}, HTTPStatus.INTERNAL_SERVER_ERROR)

    def save_content(self, payload: dict) -> None:
        def clean_images(value: object, owner: str) -> list[dict[str, str]]:
            if not isinstance(value, list) or len(value) > 12:
                raise ValueError(f"A {owner} can have at most 12 images.")
            cleaned_images = []
            for image in value:
                if not isinstance(image, dict):
                    raise ValueError("Invalid image data.")
                src = str(image.get("src", ""))
                if not re.fullmatch(r"imgs/(?:summer/)?[A-Za-z0-9._-]+", src):
                    raise ValueError("An image has an invalid path.")
                cleaned_images.append({
                    "src": src,
                    "caption": str(image.get("caption", ""))[:220],
                    "alt": str(image.get("alt", ""))[:220],
                })
            return cleaned_images

        projects = payload.get("projects", [])
        if not isinstance(projects, list) or len(projects) > 50:
            raise ValueError("Projects must be a list with at most 50 entries.")
        clean_projects = []
        project_ids = set()
        for item in projects:
            if not isinstance(item, dict):
                raise ValueError("Each project must be an object.")
            project_id = str(item.get("id", "")).strip()
            date = str(item.get("date", "")).strip()
            title = str(item.get("title", "")).strip()
            body = str(item.get("body", "")).strip()
            if (
                not re.fullmatch(r"project-[A-Za-z0-9-]{8,80}", project_id)
                or project_id in project_ids
                or project_id in BUILT_IN_PROJECTS
            ):
                raise ValueError("A project has an invalid or duplicate ID.")
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
                raise ValueError("A project has an invalid date.")
            if not title or len(title) > 120 or not body or len(body) > 12000:
                raise ValueError("Each project needs a title and description within the allowed length.")
            project_ids.add(project_id)
            clean_projects.append({
                "id": project_id,
                "date": date,
                "title": title,
                "body": body,
                "images": clean_images(item.get("images", []), "project"),
            })

        updates = payload.get("updates")
        if not isinstance(updates, list) or len(updates) > 200:
            raise ValueError("Updates must be a list with at most 200 entries.")
        clean_updates = []
        ids = set()
        for item in updates:
            if not isinstance(item, dict):
                raise ValueError("Each update must be an object.")
            update_id = str(item.get("id", "")).strip()
            project = str(item.get("project", "")).strip()
            date = str(item.get("date", "")).strip()
            title = str(item.get("title", "")).strip()
            body = str(item.get("body", "")).strip()
            if not re.fullmatch(r"[A-Za-z0-9-]{8,80}", update_id) or update_id in ids:
                raise ValueError("An update has an invalid or duplicate ID.")
            if project not in BUILT_IN_PROJECTS | project_ids:
                raise ValueError("Choose a valid summer project.")
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
                raise ValueError("An update has an invalid date.")
            if not title or len(title) > 120 or not body or len(body) > 12000:
                raise ValueError("Each update needs a title and body within the allowed length.")
            ids.add(update_id)
            clean_updates.append({
                "id": update_id,
                "project": project,
                "date": date,
                "title": title,
                "body": body,
                "images": clean_images(item.get("images", []), "update"),
            })
        updated_at = payload.get("updatedAt")
        cleaned = {
            "version": 1,
            "updatedAt": str(updated_at)[:40] if updated_at else None,
            "projects": clean_projects,
            "updates": clean_updates,
        }
        DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
        temporary = DATA_PATH.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(cleaned, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        temporary.replace(DATA_PATH)
        self.send_json({"ok": True})

    def upload_image(self, payload: dict) -> None:
        data_url = str(payload.get("data", ""))
        match = re.fullmatch(r"data:([^;,]+);base64,(.+)", data_url, re.DOTALL)
        if not match or match.group(1) not in ALLOWED_IMAGE_TYPES:
            raise ValueError("Use a JPEG, PNG, WebP, or GIF image.")
        try:
            content = base64.b64decode(match.group(2), validate=True)
        except (binascii.Error, ValueError) as error:
            raise ValueError("The image could not be decoded.") from error
        if not content or len(content) > 10 * 1024 * 1024:
            raise ValueError("Images must be smaller than 10 MB.")
        extension = ALLOWED_IMAGE_TYPES[match.group(1)]
        original_stem = Path(str(payload.get("name", "photo"))).stem
        safe_stem = re.sub(r"[^a-z0-9]+", "-", original_stem.lower()).strip("-")[:42] or "photo"
        digest = hashlib.sha256(content).hexdigest()[:10]
        filename = f"{safe_stem}-{digest}{extension}"
        IMAGE_DIR.mkdir(parents=True, exist_ok=True)
        (IMAGE_DIR / filename).write_bytes(content)
        self.send_json({
            "image": {
                "src": f"imgs/summer/{filename}",
                "caption": str(payload.get("caption", ""))[:220],
                "alt": str(payload.get("alt", ""))[:220],
            }
        })

    def publish(self) -> None:
        inside = run_git("rev-parse", "--is-inside-work-tree")
        if inside.returncode != 0:
            raise ValueError("This folder is not a Git repository.")
        branch = run_git("branch", "--show-current")
        if branch.returncode != 0 or branch.stdout.strip() != "main":
            raise ValueError("Switch this repository to the main branch before publishing.")

        tracked_paths = list(SETUP_FILES)
        try:
            content = json.loads(DATA_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ValueError(f"Could not read the summer content before publishing: {error}") from error
        for item in [*content.get("projects", []), *content.get("updates", [])]:
            for image in item.get("images", []):
                relative = str(image.get("src", ""))
                if not re.fullmatch(r"imgs/(?:summer/)?[A-Za-z0-9._-]+", relative):
                    raise ValueError("Summer content references an invalid image path.")
                if not (ROOT / relative).is_file():
                    raise ValueError(f"Summer content references a missing image: {relative}")
                if relative not in tracked_paths:
                    tracked_paths.append(relative)

        add = run_git("add", "--", *tracked_paths)
        if add.returncode != 0:
            raise ValueError(add.stderr.strip() or "Could not stage the summer page.")

        diff = run_git("diff", "--cached", "--quiet", "--", *tracked_paths)
        if diff.returncode not in (0, 1):
            raise ValueError(diff.stderr.strip() or "Could not inspect the staged changes.")

        changed = diff.returncode == 1
        if changed:
            commit = run_git("commit", "-m", "Update summer projects page", "--", *tracked_paths)
            if commit.returncode != 0:
                raise ValueError(commit.stderr.strip() or commit.stdout.strip() or "Could not create the publish commit.")

        push = run_git("push", "origin", "HEAD")
        if push.returncode != 0:
            raise ValueError(
                "The update was committed locally, but GitHub rejected the push. "
                + (push.stderr.strip() or "Check your connection and Git credentials, then publish again.")
            )
        message = (
            "Published successfully. GitHub Pages should show it within a minute or two."
            if changed
            else "Everything is already published — GitHub is up to date."
        )
        self.send_json({"message": message})


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local Summer Page Studio.")
    parser.add_argument("--port", type=int, default=8765, help="localhost port (default: 8765)")
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error("port must be between 1024 and 65535")

    os.chdir(ROOT)
    token = load_or_create_token()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), PortalHandler)
    server.portal_token = token  # type: ignore[attr-defined]
    url = f"http://127.0.0.1:{args.port}/?token={token}"
    print("\nSummer Page Studio is ready.")
    print(f"Open this private link on this computer:\n\n  {url}\n")
    print("Press Control-C when you are done.\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nPortal stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

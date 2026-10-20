"""Builds index.html and sw.js from src/. Run from anywhere: python3 tools/build.py"""
import json, base64, os
A = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(A, "src")
t = open(SRC + "/app.src.html", encoding="utf8").read()
names = json.load(open(SRC + "/names.json", encoding="utf8"))
t = t.replace("__NAMES__", json.dumps(names, ensure_ascii=False))
def rep(old, new):
    global t
    assert old in t, old[:60]
    t = t.replace(old, new, 1)
# Sprite sheets ship as their own files so index.html stays small and updates arrive quickly.
import shutil
for f in ("shiny-gen2.png", "shiny-gen3.png"):
    shutil.copyfile(SRC + "/" + f, A + "/" + f)
head = '''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="apple-mobile-web-app-title" content="Shiny Counter">
<meta name="theme-color" content="#f3f2f8" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#121222" media="(prefers-color-scheme: dark)">
<link rel="manifest" href="manifest.webmanifest">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<link rel="icon" href="icon-192.png">
'''
rep("<title>Shiny Reset Counter</title>\n", head + "<title>Shiny Reset Counter</title>\n")
rep("<style>\n", "<style>\n:root { padding-top: env(safe-area-inset-top, 0px); padding-bottom: env(safe-area-inset-bottom, 0px); }\nbody { margin: 0; }\n")
rep("</style>\n", "</style>\n</head>\n<body>\n")
rep('  <!--BACKUP-->', '''  <section class="panel" id="backup">
    <h2>Backup</h2>
    <p class="note" style="margin:0">Your hunts are saved on this device. Save a backup to the Files app now and then, so you can restore it if the app is deleted or you change phones.</p>
    <div class="actions"><button class="solid" type="button" id="saveFile">Save backup to Files</button><button class="ghost" type="button" id="openFile">Restore from a file</button></div>
    <input type="file" id="fileInput" accept=".json,application/json,text/plain" hidden>
    <p class="note" style="margin:4px 0 0">Or copy the backup as text, for example into Notes:</p>
    <textarea id="backupText" rows="3" aria-label="Backup code" style="font:13px/1.4 ui-monospace,monospace;width:100%;padding:10px;border:1px solid var(--line);border-radius:10px;background:var(--surface);color:var(--ink);resize:vertical" placeholder="Paste a backup here to restore it"></textarea>
    <div class="actions"><button class="ghost" type="button" id="copyBackup">Copy backup</button><button class="ghost" type="button" id="restoreBackup">Restore from pasted backup</button></div>
  </section>''')
rep('<p class="status" id="status">Connecting…</p>', '<p class="status" id="status"></p>')
start = t.index("  render();\n  (async () => {")
end = t.index("  })();\n})();", start) + len("  })();\n")
boot = '''  state.mode = "local";
  try { state.hunts = JSON.parse(lsGet(LS_KEY) || "{}") || {}; } catch (e) { state.hunts = {}; }
  pickActive(); render();
  if (navigator.storage && navigator.storage.persist) navigator.storage.persist().catch(() => {});
  if ("serviceWorker" in navigator && location.protocol.startsWith("http")) navigator.serviceWorker.register("sw.js").catch(() => {});

  $("copyBackup").addEventListener("click", () => {
    const code = JSON.stringify({ v: 1, hunts: state.hunts });
    $("backupText").value = code;
    const done = () => setStatus("Backup copied. Paste it somewhere safe, like Notes.");
    const fallback = () => { $("backupText").select(); setStatus("Backup is in the box above. Select it and copy."); };
    try { navigator.clipboard.writeText(code).then(done, fallback); } catch (e) { fallback(); }
  });
  // Restoring adds the backup's hunts; a hunt that exists on both sides takes the backup's copy.
  function restoreFrom(text, badMessage) {
    let data;
    try { data = JSON.parse(String(text).trim()); } catch (e) { data = null; }
    if (!data || !data.hunts || typeof data.hunts !== "object") { setStatus(badMessage); return false; }
    Object.assign(state.hunts, data.hunts);
    lsSet(LS_KEY, JSON.stringify(state.hunts));
    pickActive(); render();
    const n = Object.keys(data.hunts).length;
    setStatus("Restored " + n + (n === 1 ? " hunt." : " hunts."));
    return true;
  }
  $("restoreBackup").addEventListener("click", () => {
    if (restoreFrom($("backupText").value, "That doesn't look like a backup. Paste the whole code from Copy backup.")) $("backupText").value = "";
  });

  // Saving to Files goes through the share sheet, which has "Save to Files" on iPhone.
  // Where sharing files isn't supported, the backup downloads instead.
  $("saveFile").addEventListener("click", async () => {
    const d = new Date();
    const stamp = d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0");
    const name = "shiny-counter-backup-" + stamp + ".json";
    const body = JSON.stringify({ v: 1, savedAt: d.toISOString(), hunts: state.hunts }, null, 2);
    const file = new File([body], name, { type: "application/json" });
    if (navigator.canShare && navigator.canShare({ files: [file] })) {
      try {
        await navigator.share({ files: [file], title: name });
        setStatus("Backup ready. If you picked Save to Files, it's in the folder you chose as " + name + ".");
      } catch (e) {
        if (e && e.name === "AbortError") setStatus("Backup not saved.");
        else setStatus("Couldn't open the share sheet. Try Copy backup instead.");
      }
      return;
    }
    const url = URL.createObjectURL(file);
    const a = document.createElement("a");
    a.href = url; a.download = name; document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 10000);
    setStatus("Backup downloaded as " + name + ".");
  });
  $("openFile").addEventListener("click", () => { $("fileInput").value = ""; $("fileInput").click(); });
  $("fileInput").addEventListener("change", async () => {
    const f = $("fileInput").files[0]; if (!f) return;
    try { restoreFrom(await f.text(), "That file isn't a Shiny Reset Counter backup. Pick a file saved with Save backup to Files."); }
    catch (e) { setStatus("Couldn't read that file. Try picking it again."); }
  });
'''
t = t[:start] + boot + t[end:]
t = t.replace('setStatus("Saved to your account.");', 'setStatus("Saved on this device.");')
t += "\n</body>\n</html>\n"
open(A + "/index.html", "w", encoding="utf8").write(t)
open(A + "/sw.js", "w").write('''// Caches the app so it opens without a connection. Sprite animations are cached as they're viewed.
const CACHE = "shiny-counter-v5";
const SPRITES = "shiny-counter-sprites"; // kept across app updates, since sprites never change
const FILES = ["./", "index.html", "manifest.webmanifest", "icon-192.png", "icon-512.png", "apple-touch-icon.png", "shiny-gen2.png", "shiny-gen3.png", "anim/gen2.json"];
const WAIT_MS = 2500; // on a weak signal, use the saved copy after this long

self.addEventListener("install", (e) => { e.waitUntil(caches.open(CACHE).then((c) => c.addAll(FILES))); self.skipWaiting(); });
self.addEventListener("activate", (e) => {
  e.waitUntil((async () => {
    const sprites = await caches.open(SPRITES);
    for (const k of await caches.keys()) {
      if (k === CACHE || k === SPRITES) continue;
      // Carry viewed animations over from older versions before dropping them.
      const old = await caches.open(k);
      for (const req of await old.keys()) if (req.url.endsWith(".gif")) await sprites.put(req, await old.match(req));
      await caches.delete(k);
    }
    await self.clients.claim();
  })());
});

function save(cacheName, req, res) {
  if (res.ok || res.type === "opaque") { const copy = res.clone(); caches.open(cacheName).then((c) => c.put(req, copy)); }
  return res;
}

self.addEventListener("fetch", (e) => {
  const req = e.request;
  if (req.method !== "GET") return;
  if (req.url.endsWith(".gif")) {
    // Sprites: saved copy first, network only for ones not seen yet.
    e.respondWith(caches.match(req).then((hit) => hit || fetch(req).then((r) => save(SPRITES, req, r))));
    return;
  }
  // Everything else: try the network for updates, but fall back to the saved copy
  // if the network fails or takes longer than WAIT_MS.
  e.respondWith((async () => {
    const network = fetch(req).then((r) => save(CACHE, req, r));
    const cached = await caches.match(req);
    if (!cached) return network;
    network.catch(() => {}); // a late failure after we've answered is fine
    const timeout = new Promise((resolve) => setTimeout(() => resolve(cached), WAIT_MS));
    return Promise.race([network.catch(() => cached), timeout]);
  })());
});
''')

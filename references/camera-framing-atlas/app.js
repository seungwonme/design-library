(() => {
  "use strict";

  const state = { kind: "all", query: "", dark: false, maps: [] };
  const $ = (selector) => document.querySelector(selector);
  const cards = $("#cards");
  const empty = $("#empty");
  const resultCount = $("#result-count");
  const kindLabels = { framing: "구도", optics: "광학/환경" };

  const sourceUrl = (itemId) => itemId.startsWith("eyecandy:")
    ? `https://eyecannndy.com/technique/${itemId.slice("eyecandy:".length)}`
    : "https://s.studiobinder.com/wp-content/uploads/2018/09/Filmmaking-Techniques-Camera-Movement-Worksheet.pdf#page=1";

  function matches(entry) {
    const renderer = window.CameraFramingGallery.catalog.find((item) => item.previewId === entry.previewId);
    const text = [entry.itemId, entry.previewId, entry.explanation, entry.limitation, renderer?.name, renderer?.english].join(" ").toLowerCase();
    return (state.kind === "all" || state.kind === entry.kind) && (!state.query || text.includes(state.query));
  }

  function addDetail(parent, label, value) {
    const row = document.createElement("div");
    const term = document.createElement("dt"); term.textContent = label;
    const description = document.createElement("dd"); description.textContent = value;
    row.append(term, description); parent.append(row);
  }

  function drawCard(canvas, previewId) {
    window.CameraFramingGallery.draw(canvas, previewId, 0, { dark: state.dark });
  }

  function createCard(entry) {
    const renderer = window.CameraFramingGallery.catalog.find((item) => item.previewId === entry.previewId);
    const card = document.createElement("article"); card.className = "card";
    const preview = document.createElement("div"); preview.className = "preview";
    const canvas = document.createElement("canvas"); canvas.width = 960; canvas.height = 540;
    canvas.setAttribute("aria-label", `${entry.itemId} 카메라 도식`); preview.append(canvas);
    const redraw = document.createElement("button"); redraw.type = "button"; redraw.textContent = "다시 그리기";
    redraw.addEventListener("click", () => drawCard(canvas, entry.previewId)); preview.append(redraw);

    const body = document.createElement("div"); body.className = "card-body";
    const meta = document.createElement("div"); meta.className = "card-meta";
    const kind = document.createElement("span"); kind.textContent = kindLabels[entry.kind] || entry.kind;
    const motion = document.createElement("span"); motion.textContent = entry.motion ? "motion" : "static"; meta.append(kind, motion);
    const title = document.createElement("h2"); title.textContent = renderer?.name || entry.itemId;
    const english = document.createElement("p"); english.className = "english"; english.textContent = renderer?.english || entry.previewId;
    const details = document.createElement("dl"); details.className = "details";
    addDetail(details, "ID", entry.itemId); addDetail(details, "설명", entry.explanation); addDetail(details, "제한", entry.limitation); addDetail(details, "관찰", entry.qa.observable); addDetail(details, "시작/끝", `${entry.qa.start} / ${entry.qa.end}`);
    const source = document.createElement("a"); source.href = sourceUrl(entry.itemId); source.target = "_blank"; source.rel = "noreferrer"; source.textContent = "출처 보기"; source.className = "source-link";
    body.append(meta, title, english, details, source); card.append(preview, body); drawCard(canvas, entry.previewId); return card;
  }

  function render() {
    const filtered = state.maps.filter(matches);
    cards.replaceChildren(...filtered.map(createCard)); empty.hidden = filtered.length !== 0;
    resultCount.textContent = `${filtered.length}개`;
    document.querySelectorAll(".filter").forEach((button) => { const active = button.dataset.kind === state.kind; button.classList.toggle("active", active); button.setAttribute("aria-pressed", String(active)); });
  }

  function updateCounts() {
    $("#count-all").textContent = state.maps.length;
    $("#count-framing").textContent = state.maps.filter((entry) => entry.kind === "framing").length;
    $("#count-optics").textContent = state.maps.filter((entry) => entry.kind === "optics").length;
  }

  $("#search").addEventListener("input", (event) => { state.query = event.target.value.trim().toLowerCase(); render(); });
  document.querySelectorAll(".filter").forEach((button) => button.addEventListener("click", () => { state.kind = button.dataset.kind; render(); }));
  $("#theme-toggle").addEventListener("click", (event) => { state.dark = !state.dark; document.documentElement.classList.toggle("dark", state.dark); event.currentTarget.textContent = state.dark ? "밝은 화면" : "어두운 화면"; event.currentTarget.setAttribute("aria-pressed", String(state.dark)); render(); });

  fetch("camera-map-framing.json")
    .then((response) => { if (!response.ok) throw new Error(`Mapping request failed: ${response.status}`); return response.json(); })
    .then((maps) => { state.maps = maps; updateCounts(); render(); })
    .catch((error) => { empty.hidden = false; empty.textContent = `매핑을 읽지 못했습니다: ${error.message}`; });
})();

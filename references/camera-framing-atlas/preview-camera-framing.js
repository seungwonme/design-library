(() => {
  "use strict";

  const W = 960;
  const H = 540;
  const TAU = Math.PI * 2;
  const FONT = 'ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
  const CATALOG = [
    ["eyecandy:central-framing", "중앙 구도", "Central Framing", "framing:central-framing", "shot"],
    ["eyecandy:fisheye", "어안 렌즈", "Fisheye", "framing:fisheye", "fisheye"],
    ["eyecandy:ground-shot", "지면 높이 숏", "Ground Level", "framing:ground-shot", "shot"],
    ["eyecandy:omnidirectional", "전방위 영상", "Omnidirectional", "framing:omnidirectional", "omni"],
    ["eyecandy:over-the-shoulder", "어깨너머 숏", "Over the Shoulder", "framing:over-the-shoulder", "shot"],
    ["eyecandy:probe-lens", "프로브 렌즈", "Probe", "framing:probe-lens", "probe"],
    ["eyecandy:profile-shot", "측면 숏", "Profile", "framing:profile-shot", "shot"],
    ["eyecandy:shadow-box", "섀도 박스", "Shadow Box", "framing:shadow-box", "shot"],
    ["eyecandy:tableau-shots", "타블로", "Tableau", "framing:tableau-shots", "shot"],
    ["eyecandy:tilt-shift", "틸트 시프트", "Tilt Shift", "framing:tilt-shift", "tilt"],
    ["eyecandy:two-shot", "투 숏", "Two Shot", "framing:two-shot", "shot"],
    ["eyecandy:ultra-wide-zero-d", "초광각", "Ultra Wide", "framing:ultra-wide-zero-d", "lens"],
    ["eyecandy:underwater", "수중 촬영", "Underwater", "framing:underwater", "underwater"],
    ["eyecandy:voyeur", "관찰자 시점", "Voyeur", "framing:voyeur", "voyeur"],
    ["eyecandy:worms-eye", "웜스 아이", "Worms-Eye", "framing:worms-eye", "shot"],
    ["studiobinder:medium-close-up", "미디엄 클로즈업", "Medium Close-up", "framing:medium-close-up", "shot"],
    ["studiobinder:wide-close-up", "와이드 클로즈업", "Wide Close-up", "framing:wide-close-up", "shot"],
    ["studiobinder:full-shot", "풀 숏", "Full Shot", "framing:full-shot", "shot"],
    ["studiobinder:medium-full-shot", "미디엄 풀 숏", "Medium Full Shot", "framing:medium-full-shot", "shot"],
    ["studiobinder:long-shot", "롱 숏", "Long Shot", "framing:long-shot", "shot"],
    ["studiobinder:close-shot", "클로스 숏", "Close Shot", "framing:close-shot", "shot"],
    ["studiobinder:medium-close-shot", "미디엄 클로스 숏", "Medium Close Shot", "framing:medium-close-shot", "shot"],
    ["studiobinder:shoulder-level", "어깨 높이", "Shoulder Level", "framing:shoulder-level", "shot"],
    ["studiobinder:hip-level", "허리 높이", "Hip Level", "framing:hip-level", "shot"],
    ["studiobinder:knee-level", "무릎 높이", "Knee Level", "framing:knee-level", "shot"],
    ["studiobinder:single", "싱글", "Single", "framing:single", "shot"],
    ["studiobinder:three-shot", "쓰리 숏", "Three Shot", "framing:three-shot", "shot"],
    ["studiobinder:over-the-hip", "허리너머", "Over the Hip", "framing:over-the-hip", "shot"],
    ["studiobinder:dutch-left", "왼쪽 더치", "Dutch (left)", "framing:dutch-left", "dutch"],
    ["studiobinder:dutch-right", "오른쪽 더치", "Dutch (right)", "framing:dutch-right", "dutch"],
    ["studiobinder:normal", "표준 화각", "Normal", "framing:normal", "lens"],
    ["studiobinder:telephoto", "망원", "Telephoto", "framing:telephoto", "lens"],
    ["studiobinder:wide-angle", "광각", "Wide Angle", "framing:wide-angle", "lens"],
  ].map(([itemId, name, english, previewId, mode]) => ({ itemId, name, english, previewId, mode }));

  const COLORS = {
    light: { bg: "#f4f0e8", surface: "#fffdf7", grid: "#c6d2c8", line: "#aabdb2", ink: "#193632", muted: "#5f756d", hero: "#bc624d", near: "#718c72", far: "#648b94", accent: "#db985f", dark: "#18302d", water: "#62bec4", blur: "rgba(40,65,70,.24)", yellow: "#efc46e", occluder: "#31413d" },
    dark: { bg: "#17231f", surface: "#263733", grid: "#526c64", line: "#5c766c", ink: "#edf1e8", muted: "#afc2b9", hero: "#e4a087", near: "#9bb79a", far: "#93c4c7", accent: "#efb176", dark: "#0d201e", water: "#2c9da5", blur: "rgba(4,22,27,.46)", yellow: "#ecc76d", occluder: "#101f1d" },
  };

  const clamp = (n) => Math.max(0, Math.min(1, Number.isFinite(n) ? n : 0));
  const dist = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1]);
  const unit = (a) => { const n = Math.hypot(a[0], a[1]) || 1; return [a[0] / n, a[1] / n]; };

  function text(ctx, value, x, y, color, size = 12, align = "left", weight = 500) {
    ctx.font = `${weight} ${size}px ${FONT}`;
    ctx.fillStyle = color;
    ctx.textAlign = align;
    ctx.textBaseline = "alphabetic";
    ctx.fillText(value, x, y);
  }

  function panel(ctx, x, y, w, h, colors, radius = 14) {
    ctx.beginPath(); ctx.roundRect(x, y, w, h, radius);
    ctx.fillStyle = colors.surface; ctx.fill();
    ctx.strokeStyle = colors.line; ctx.lineWidth = 1; ctx.stroke();
  }

  function line(ctx, a, b, color, width = 1, dash = []) {
    ctx.beginPath(); ctx.moveTo(a[0], a[1]); ctx.lineTo(b[0], b[1]);
    ctx.strokeStyle = color; ctx.lineWidth = width; ctx.setLineDash(dash); ctx.stroke(); ctx.setLineDash([]);
  }

  function arrow(ctx, a, b, color, width = 1.4) {
    line(ctx, a, b, color, width);
    const d = unit([b[0] - a[0], b[1] - a[1]]); const p = [-d[1], d[0]];
    line(ctx, b, [b[0] - d[0] * 10 + p[0] * 5, b[1] - d[1] * 10 + p[1] * 5], color, width);
    line(ctx, b, [b[0] - d[0] * 10 - p[0] * 5, b[1] - d[1] * 10 - p[1] * 5], color, width);
  }

  function camera(ctx, x, y, colors, label = "카메라") {
    ctx.fillStyle = colors.dark; ctx.fillRect(x - 10, y - 6, 20, 12);
    ctx.beginPath(); ctx.moveTo(x + 10, y - 5); ctx.lineTo(x + 20, y - 9); ctx.lineTo(x + 20, y + 9); ctx.lineTo(x + 10, y + 5); ctx.closePath(); ctx.fill();
    text(ctx, label, x, y + 24, colors.muted, 10, "center");
  }

  function human(ctx, x, ground, scale, colors, role = "hero", profile = false) {
    const body = role === "near" ? colors.near : role === "far" ? colors.far : colors.hero;
    const head = ground - 3.05 * scale;
    ctx.fillStyle = body;
    ctx.fillRect(x - .36 * scale, head - .36 * scale, .72 * scale, .72 * scale);
    ctx.fillRect(x - .51 * scale, ground - 2.55 * scale, 1.02 * scale, 1.25 * scale);
    ctx.fillRect(x - .48 * scale, ground - 1.3 * scale, .38 * scale, 1.3 * scale);
    ctx.fillRect(x + .1 * scale, ground - 1.3 * scale, .38 * scale, 1.3 * scale);
    ctx.fillRect(x - .87 * scale, ground - 2.33 * scale, .3 * scale, 1.1 * scale);
    ctx.fillRect(x + .57 * scale, ground - 2.33 * scale, .3 * scale, 1.1 * scale);
    ctx.fillStyle = colors.dark;
    if (profile) ctx.fillRect(x + .34 * scale, head - .02 * scale, .18 * scale, .12 * scale);
    else { ctx.fillRect(x - .22 * scale, head - .02 * scale, .1 * scale, .08 * scale); ctx.fillRect(x + .12 * scale, head - .02 * scale, .1 * scale, .08 * scale); }
  }

  function grid(ctx, x, y, w, h, colors, curve = false) {
    ctx.strokeStyle = colors.grid; ctx.lineWidth = 1;
    for (let i = 1; i < 6; i += 1) {
      if (!curve) line(ctx, [x + w * i / 6, y], [x + w * i / 6, y + h], colors.grid);
      else { ctx.beginPath(); ctx.moveTo(x + w * i / 6, y); ctx.bezierCurveTo(x + w * i / 6 - 35, y + h * .3, x + w * i / 6 - 35, y + h * .7, x + w * i / 6, y + h); ctx.stroke(); }
    }
    for (let i = 1; i < 5; i += 1) {
      if (!curve) line(ctx, [x, y + h * i / 5], [x + w, y + h * i / 5], colors.grid);
      else { ctx.beginPath(); ctx.moveTo(x, y + h * i / 5); ctx.bezierCurveTo(x + w * .3, y + h * i / 5 - 25, x + w * .7, y + h * i / 5 - 25, x + w, y + h * i / 5); ctx.stroke(); }
    }
  }

  function relation(ctx, colors, spec, label = "카메라 관계") {
    panel(ctx, 696, 78, 242, 388, colors);
    text(ctx, label, 714, 105, colors.muted, 12);
    line(ctx, [712, 358], [922, 358], colors.line, 1.2);
    const height = Math.max(.05, Math.min(3.2, spec.height));
    const cy = 358 - height * 58; const cx = 742; const sx = 862;
    camera(ctx, cx, cy, colors);
    human(ctx, sx, 358, 30, colors, "hero");
    arrow(ctx, [cx + 20, cy], [sx - 34, 292], colors.accent);
    line(ctx, [cx - 30, cy], [cx + 30, cy], colors.accent, 1, [3, 3]);
    text(ctx, `카메라 높이 ${height.toFixed(2)}`, 714, 405, colors.ink, 11);
    text(ctx, spec.heightLabel || "실제 높이 관계를 표시", 714, 427, colors.muted, 10);
    text(ctx, `화각 ${spec.fov}° · 정적`, 714, 449, colors.muted, 10);
  }

  function mainFrame(ctx, colors, title) {
    panel(ctx, 22, 78, 654, 388, colors);
    text(ctx, title, 40, 105, colors.muted, 12);
    ctx.save(); ctx.beginPath(); ctx.rect(36, 116, 626, 334); ctx.clip(); grid(ctx, 36, 116, 626, 334, colors); ctx.restore();
  }

  const configs = {};
  const addConfig = (id, values) => { configs[id] = { mode: "shot", height: 1.7, fov: 50, scale: 56, crop: "프레이밍 관계", ...values }; };

  addConfig("framing:central-framing", { central: true, crop: "중심선과 균형" });
  addConfig("framing:fisheye", { mode: "fisheye", fov: 100 });
  addConfig("framing:ground-shot", { height: .12, heightLabel: "지면 0.12", fov: 54, crop: "바닥 가까이" });
  addConfig("framing:omnidirectional", { mode: "omni", fov: 360 });
  addConfig("framing:over-the-shoulder", { ots: true, scale: 62, height: 1.75, crop: "전경 어깨 occlusion" });
  addConfig("framing:probe-lens", { mode: "probe", fov: 48 });
  addConfig("framing:profile-shot", { profile: true, scale: 60, crop: "측면 실루엣" });
  addConfig("framing:shadow-box", { scale: 38, crop: "프레임 안의 여백" });
  addConfig("framing:tableau-shots", { count: 3, scale: 43, crop: "그림처럼 읽는 배치" });
  addConfig("framing:tilt-shift", { mode: "tilt", height: 2.1 });
  addConfig("framing:two-shot", { count: 2, scale: 48, crop: "두 사람 관계" });
  addConfig("framing:ultra-wide-zero-d", { mode: "lens", title: "초광각 · 큰 전경", fov: 82, near: 106, far: 24 });
  addConfig("framing:underwater", { mode: "underwater", height: 1.5, fov: 56 });
  addConfig("framing:voyeur", { mode: "voyeur", fov: 47 });
  addConfig("framing:worms-eye", { height: .08, heightLabel: "지면 .08 · 위를 올려봄", fov: 56, crop: "웜스 아이" });
  addConfig("framing:medium-close-up", { scale: 86, height: 1.9, fov: 40, crop: "가슴 위" });
  addConfig("framing:wide-close-up", { scale: 72, height: 1.9, fov: 46, crop: "머리와 가슴" });
  addConfig("framing:full-shot", { scale: 57, crop: "전신" });
  addConfig("framing:medium-full-shot", { scale: 66, height: 1.6, crop: "머리부터 무릎" });
  addConfig("framing:long-shot", { scale: 33, height: 1.8, fov: 58, crop: "환경과 관계", long: true });
  addConfig("framing:close-shot", { scale: 125, height: 2, fov: 34, crop: "머리와 어깨" });
  addConfig("framing:medium-close-shot", { scale: 96, height: 1.8, fov: 43, crop: "허리 위" });
  addConfig("framing:shoulder-level", { height: 1.88, heightLabel: "어깨 1.88", heightLine: true, crop: "어깨 높이" });
  addConfig("framing:hip-level", { height: 1.3, heightLabel: "골반 1.30", heightLine: true, crop: "허리 높이" });
  addConfig("framing:knee-level", { height: .65, heightLabel: "무릎 .65", heightLine: true, crop: "무릎 높이" });
  addConfig("framing:single", { crop: "한 사람" });
  addConfig("framing:three-shot", { count: 3, scale: 44, fov: 56, crop: "세 사람" });
  addConfig("framing:over-the-hip", { overHip: true, scale: 55, height: 1.45, fov: 45, crop: "전경 허리 occlusion" });
  addConfig("framing:dutch-left", { mode: "dutch", roll: -.22 });
  addConfig("framing:dutch-right", { mode: "dutch", roll: .22 });
  addConfig("framing:normal", { mode: "lens", title: "표준 화각 · 균형", near: 46, far: 48 });
  addConfig("framing:telephoto", { mode: "lens", title: "망원 · 원근 압축 근사", fov: 22, near: 50, far: 70, height: 2 });
  addConfig("framing:wide-angle", { mode: "lens", title: "광각 · 직선 보존", fov: 76, near: 88, far: 34 });

  function sample(previewId, t = 0) {
    const c = configs[previewId];
    if (!c) throw new RangeError(`Unknown preview: ${previewId}`);
    return { position: [4, c.height, 10], target: [0, 1.6, -1], up: [0, 1, 0], fov: c.fov, subject: [0, 1.6, 0], parameters: { ...c, progress: clamp(t) } };
  }

  function drawShot(ctx, colors, spec) {
    const c = spec.parameters;
    mainFrame(ctx, colors, c.crop);
    ctx.save(); ctx.beginPath(); ctx.rect(36, 116, 626, 334); ctx.clip();
    if (c.long) { ctx.fillStyle = colors.far; ctx.fillRect(150, 270, 34, 180); ctx.fillRect(575, 250, 34, 200); human(ctx, 520, 428, 27, colors, "far"); }
    else { ctx.fillStyle = colors.far; ctx.fillRect(155, 280, 34, 170); ctx.fillRect(577, 260, 34, 190); }
    if (c.ots) { human(ctx, 110, 440, 160, colors, "near"); human(ctx, 445, 430, .9 * c.scale, colors, "hero"); ctx.fillStyle = colors.surface; ctx.fillRect(36, 116, 56, 334); }
    else if (c.overHip) { ctx.fillStyle = colors.near; ctx.fillRect(36, 330, 225, 120); human(ctx, 445, 430, .9 * c.scale, colors, "hero"); text(ctx, "전경 허리", 148, 355, colors.ink, 11, "center"); }
    else if (c.count === 2) { human(ctx, 210, 430, .82 * c.scale, colors, "near"); human(ctx, 490, 430, .82 * c.scale, colors, "hero"); arrow(ctx, [250, 320], [450, 320], colors.accent); }
    else if (c.count === 3) { human(ctx, 210, 430, .75 * c.scale, colors, "hero"); human(ctx, 350, 430, .75 * c.scale, colors, "near"); human(ctx, 490, 430, .75 * c.scale, colors, "hero"); }
    else human(ctx, 350, c.scale > 100 ? 505 : 430, c.scale, colors, "hero", c.profile);
    if (c.central) { line(ctx, [350, 116], [350, 450], colors.accent, 1, [4, 4]); line(ctx, [36, 283], [662, 283], colors.accent, 1, [4, 4]); }
    if (c.heightLine) { const y = 430 - c.height * 58; line(ctx, [52, y], [642, y], colors.accent, 1.4, [5, 4]); text(ctx, c.heightLabel, 58, y - 8, colors.accent, 11); }
    ctx.restore();
    camera(ctx, 92, 410 - c.height * 24, colors);
    arrow(ctx, [112, 410 - c.height * 24], [320, 302], colors.accent);
    relation(ctx, colors, spec, c.heightLabel || "카메라 관계");
  }

  function drawLens(ctx, colors, spec) {
    const c = spec.parameters;
    mainFrame(ctx, colors, c.title || "화각 비교");
    ctx.save(); ctx.beginPath(); ctx.rect(36, 116, 626, 334); ctx.clip();
    grid(ctx, 36, 116, 626, 334, colors);
    ctx.fillStyle = colors.near; ctx.fillRect(102, 314 - c.near / 2, c.near * 1.5, c.near);
    human(ctx, 505, 430, c.far / 25, colors, "hero");
    ctx.restore(); camera(ctx, 82, 415, colors); arrow(ctx, [104, 415], [450, 325], colors.accent); relation(ctx, colors, spec, c.title || "렌즈 관계");
  }

  function drawFisheye(ctx, colors, spec) {
    mainFrame(ctx, colors, "직선이 휘는 어안 근사");
    ctx.save(); ctx.beginPath(); ctx.rect(36, 116, 626, 334); ctx.clip();
    ctx.strokeStyle = colors.accent; ctx.lineWidth = 1.4;
    for (let i = -4; i <= 4; i += 1) { ctx.beginPath(); ctx.moveTo(42, 285 + i * 38); ctx.bezierCurveTo(250, 250 + i * 30, 450, 250 + i * 30, 656, 285 + i * 38); ctx.stroke(); ctx.beginPath(); ctx.moveTo(350 + i * 60, 118); ctx.bezierCurveTo(300 + i * 34, 210, 300 + i * 34, 360, 350 + i * 60, 448); ctx.stroke(); }
    human(ctx, 350, 430, 74, colors); ctx.restore(); relation(ctx, colors, spec, "어안 투영의 시각적 근사");
  }

  function drawOmni(ctx, colors, spec) {
    mainFrame(ctx, colors, "360° 커버리지 / 오비트 아님");
    const x = 350, y = 285; ctx.strokeStyle = colors.accent; ctx.lineWidth = 2; ctx.beginPath(); ctx.arc(x, y, 112, 0, TAU); ctx.stroke(); ctx.beginPath(); ctx.arc(x, y, 70, 0, TAU); ctx.stroke(); camera(ctx, x, y, colors, "360 카메라");
    [[0, -1, "앞"], [1, 0, "오른쪽"], [0, 1, "뒤"], [-1, 0, "왼쪽"]].forEach(([dx, dy, label]) => { human(ctx, x + dx * 155, y + dy * 105, 25, colors); text(ctx, label, x + dx * 155, y + dy * 105 + (dy > 0 ? 42 : -46), colors.muted, 10, "center"); });
    text(ctx, "주변 전체를 기록하는 범위", x, 428, colors.ink, 12, "center"); relation(ctx, colors, spec, "커버리지 설명");
  }

  function drawProbe(ctx, colors, spec) {
    mainFrame(ctx, colors, "프로브 렌즈 / 일반 매크로 비교"); camera(ctx, 84, 382, colors, "프로브");
    ctx.fillStyle = colors.dark; ctx.fillRect(100, 374, 255, 16); ctx.fillRect(350, 367, 80, 30); ctx.fillStyle = colors.accent; ctx.fillRect(430, 356, 24, 52); ctx.fillStyle = colors.hero; ctx.beginPath(); ctx.arc(510, 382, 19, 0, TAU); ctx.fill();
    line(ctx, [110, 428], [550, 428], colors.line); text(ctx, "긴 렌즈가 좁은 틈 안으로 들어감", 320, 448, colors.muted, 11, "center"); relation(ctx, colors, spec, "튜브 길이와 피사체 거리");
  }

  function drawTilt(ctx, colors, spec) {
    mainFrame(ctx, colors, "선택적 초점면"); ctx.save(); ctx.beginPath(); ctx.rect(36, 116, 626, 334); ctx.clip(); grid(ctx, 36, 116, 626, 334, colors); ctx.fillStyle = colors.blur; ctx.fillRect(36, 116, 626, 122); ctx.fillRect(36, 370, 626, 80); human(ctx, 350, 430, 53, colors); ctx.strokeStyle = colors.yellow; ctx.lineWidth = 5; ctx.beginPath(); ctx.moveTo(36, 346); ctx.lineTo(662, 285); ctx.stroke(); ctx.restore(); panel(ctx, 720, 160, 194, 140, colors); text(ctx, "선명한 띠", 817, 190, colors.muted, 12, "center"); line(ctx, [744, 250], [889, 226], colors.yellow, 5); text(ctx, "실제 광학의 근사", 817, 278, colors.ink, 10, "center"); relation(ctx, colors, spec, "초점면 도식");
  }

  function drawUnderwater(ctx, colors, spec) {
    mainFrame(ctx, colors, "수중 촬영 개념"); ctx.save(); ctx.beginPath(); ctx.rect(36, 116, 626, 334); ctx.clip(); ctx.fillStyle = "rgba(44,166,177,.35)"; ctx.fillRect(36, 116, 626, 334); ctx.strokeStyle = colors.water; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(36, 170); ctx.bezierCurveTo(240, 150, 460, 188, 662, 158); ctx.stroke(); ctx.strokeStyle = "rgba(242,255,246,.36)"; ctx.lineWidth = 2; [[140, 116, 245, 370], [360, 116, 420, 340], [575, 116, 500, 370]].forEach(([x1, y1, x2, y2]) => line(ctx, [x1, y1], [x2, y2], "rgba(242,255,246,.36)", 2)); for (let i = 0; i < 28; i += 1) { const x = 50 + (i * 137) % 590; const y = 198 + (i * 59) % 225; ctx.fillStyle = `rgba(235,255,250,${.15 + (i % 4) * .07})`; ctx.beginPath(); ctx.arc(x, y, 1 + i % 3, 0, TAU); ctx.fill(); } human(ctx, 350, 400, 49, colors); ctx.restore(); relation(ctx, colors, spec, "수면선과 부유 입자");
  }

  function drawVoyeur(ctx, colors, spec) {
    mainFrame(ctx, colors, "가림막과 좁은 틈"); ctx.fillStyle = colors.occluder; ctx.fillRect(36, 116, 112, 334); ctx.fillRect(550, 116, 112, 334); ctx.fillStyle = "rgba(20,30,28,.28)"; ctx.fillRect(148, 116, 28, 334); ctx.fillRect(522, 116, 28, 334); human(ctx, 350, 430, 52, colors); camera(ctx, 82, 410, colors); arrow(ctx, [104, 410], [315, 300], colors.accent); relation(ctx, colors, spec, "전경 occlusion");
  }

  function drawDutch(ctx, colors, spec) {
    ctx.save(); ctx.translate(350, 285); ctx.rotate(spec.parameters.roll); ctx.translate(-350, -285); mainFrame(ctx, colors, "수평선 롤"); human(ctx, 350, 430, 60, colors); line(ctx, [36, 285], [662, 285], colors.accent, 2); ctx.restore(); relation(ctx, colors, spec, spec.parameters.roll < 0 ? "왼쪽 더치" : "오른쪽 더치");
  }

  function draw(target, previewId, t = 0, options = {}) {
    const item = CATALOG.find((entry) => entry.previewId === previewId);
    if (!item) throw new RangeError(`Unknown camera framing preview: ${previewId}`);
    const ctx = target && typeof target.getContext === "function" ? target.getContext("2d") : target;
    if (!ctx || typeof ctx.save !== "function") throw new TypeError("A Canvas2D context or canvas is required");
    const colors = options.dark ? COLORS.dark : COLORS.light;
    const spec = sample(previewId, t);
    const c = spec.parameters;
    ctx.save(); ctx.setTransform(ctx.canvas.width / W, 0, 0, ctx.canvas.height / H, 0, 0); ctx.globalAlpha = 1; ctx.globalCompositeOperation = "source-over"; ctx.filter = "none"; ctx.setLineDash([]); ctx.clearRect(0, 0, W, H); ctx.fillStyle = colors.bg; ctx.fillRect(0, 0, W, H);
    panel(ctx, 22, 18, 916, 44, colors, 12); text(ctx, item.name, 38, 46, colors.ink, 18, "left", 650); text(ctx, item.english, 920, 45, colors.muted, 11, "right");
    if (c.mode === "fisheye") drawFisheye(ctx, colors, spec); else if (c.mode === "omni") drawOmni(ctx, colors, spec); else if (c.mode === "probe") drawProbe(ctx, colors, spec); else if (c.mode === "tilt") drawTilt(ctx, colors, spec); else if (c.mode === "underwater") drawUnderwater(ctx, colors, spec); else if (c.mode === "voyeur") drawVoyeur(ctx, colors, spec); else if (c.mode === "dutch") drawDutch(ctx, colors, spec); else if (c.mode === "lens") drawLens(ctx, colors, spec); else drawShot(ctx, colors, spec);
    text(ctx, "정적 도식 · 실제 광학 효과는 근사", 38, 510, colors.muted, 11); text(ctx, `FOV ${c.fov}°`, 920, 510, colors.muted, 11, "right"); ctx.restore();
  }

  const definitions = Object.fromEntries(CATALOG.map((item) => [item.previewId, Object.freeze({ motion: false, sample: (t) => sample(item.previewId, t) })]));
  window.CameraFramingGallery = Object.freeze({ ids: CATALOG.map((item) => item.previewId), definitions, sample, draw, catalog: CATALOG });
})();

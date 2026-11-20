// A tiny garden that blooms or wilts with recent public GitHub activity.
(() => {
  const root = document.querySelector("[data-git-flower]");
  if (!root) return;

  const user = root.dataset.user;
  const svg = root.querySelector("svg");
  const caption = root.querySelector(".gf-caption");

  const WINDOW_DAYS = 14;
  const CACHE_KEY = `git-flower:${user}`;
  const CACHE_MS = 60 * 60 * 1000;
  const DAY_MS = 24 * 60 * 60 * 1000;
  const GROUND = 56;

  const mix = (a, b, t) => a + (b - a) * t;
  const clamp = (v) => Math.max(0, Math.min(1, v));
  const hex = (c) => [1, 3, 5].map((i) => parseInt(c.slice(i, i + 2), 16));
  const mixColor = (alive, dead, h) => {
    const [a, b] = [hex(alive), hex(dead)];
    return `rgb(${a.map((v, i) => Math.round(mix(b[i], v, h))).join(",")})`;
  };

  // Each flower blooms once overall health passes its threshold `t`.
  const FLOWERS = [
    { x: 12, h: 24, size: 0.8, petals: 5, color: "#a98bd6", center: "#f2c14e", t: 0.3, leaves: [[1, 48]], fallen: [[-6, 0.4], [5, -0.2], [-9, 0.1], [8, 0.3]] },
    { x: 31, h: 36, size: 1, petals: 6, color: "#e8879f", center: "#f2c14e", t: 0, leaves: [[-1, 46], [1, 40]], fallen: [[7, -0.3], [-6, 0.2], [11, 0.4], [-10, -0.2], [4, 0.1]] },
    { x: 50, h: 19, size: 0.7, petals: 8, color: "#f0a35e", center: "#8a5a3c", t: 0.15, leaves: [[-1, 50]], fallen: [[5, 0.3], [-5, -0.3], [8, -0.1], [-8, 0.2], [3, -0.4], [-3, 0.4], [10, 0.1]] },
    { x: 69, h: 30, size: 0.9, petals: 6, color: "#86a9dc", center: "#f2c14e", t: 0.45, leaves: [[1, 46], [-1, 42]], fallen: [[6, 0.2], [-7, -0.3], [9, -0.1], [-4, 0.3], [12, 0.2]] },
    { x: 89, h: 22, size: 0.75, petals: 5, color: "#e8879f", center: "#f2c14e", t: 0.6, leaves: [[-1, 49]], fallen: [[5, -0.2], [-6, 0.3], [8, 0.1], [-9, -0.2]] },
  ];
  const GRASS = [3, 21, 41, 59, 79, 99];

  const NS = "http://www.w3.org/2000/svg";
  const el = (tag, attrs, parent) => {
    const node = document.createElementNS(NS, tag);
    Object.entries(attrs).forEach(([k, v]) => node.setAttribute(k, v));
    parent.appendChild(node);
    return node;
  };

  const grass = GRASS.map((x) =>
    el("path", {
      fill: "none",
      "stroke-width": 1.1,
      "stroke-linecap": "round",
      d: `M${x} ${GROUND} q-1 -3 -3 -4.5 M${x} ${GROUND} q0.4 -4 1.2 -6 M${x} ${GROUND} q1 -2.5 3.5 -3.5`,
    }, svg)
  );

  const flowers = FLOWERS.map((f, i) => {
    const sway = el("g", { class: "gf-sway" }, svg);
    sway.style.transformOrigin = `${f.x}px ${GROUND}px`;
    sway.style.animationDelay = `${-i * 1.3}s`;
    sway.style.animationDuration = `${4 + (i % 3) * 0.6}s`;
    const k = f.h / 36;
    const leaves = f.leaves.map(([side, y]) => {
      const s = k * 0.9;
      const d = `M${f.x} ${y} c${6 * side * s} ${-2 * s} ${10 * side * s} ${-6 * s} ${11 * side * s} ${-10 * s} ` +
        `c${-5 * side * s} ${1 * s} ${-9 * side * s} ${5 * s} ${-11 * side * s} ${10 * s} Z`;
      return { node: el("path", { class: "gf-leaf", d }, sway), side, y };
    });
    const stem = el("path", { class: "gf-stem", fill: "none", "stroke-width": 1.4 + 0.4 * k, "stroke-linecap": "round" }, sway);
    const head = el("g", { class: "gf-head" }, sway);
    const petals = Array.from({ length: f.petals }, (_, p) =>
      el("ellipse", {
        class: "gf-petal",
        cx: 0, cy: -5.5, rx: f.petals > 6 ? 2.2 : 3.2, ry: 5,
        transform: `rotate(${(360 / f.petals) * p})`,
      }, head)
    );
    const center = el("circle", { class: "gf-center", r: 3.2 }, head);
    const fallen = f.fallen.map(([dx, tilt]) =>
      el("ellipse", {
        class: "gf-fallen",
        cx: f.x + dx, cy: GROUND - 1.2, rx: 2.4 * f.size, ry: 1.15 * f.size,
        transform: `rotate(${tilt * 50} ${f.x + dx} ${GROUND - 1.2})`,
      }, svg)
    );
    return { f, k, sway, leaves, stem, head, petals, center, fallen };
  });

  const drawFlower = ({ f, k, sway, leaves, stem, head, petals, center, fallen }, h) => {
    const bend = 1 - h;
    const topX = f.x + 9 * bend * k;
    const topY = GROUND - f.h + 9 * bend * k;
    stem.setAttribute("d", `M${f.x} ${GROUND} Q${f.x - 2 * bend * k} ${GROUND - (20 + 4 * bend) * k} ${topX} ${topY}`);
    stem.setAttribute("stroke", mixColor("#5e8c55", "#8a7a52", h));
    head.setAttribute("transform", `translate(${topX} ${topY}) rotate(${bend * 125}) scale(${mix(0.78, 1, h) * f.size})`);

    const petalColor = mixColor(f.color, "#a48b6a", h);
    const shown = Math.round(1 + (petals.length - 1) * h);
    petals.forEach((p, i) => {
      p.setAttribute("fill", petalColor);
      p.style.opacity = i < shown ? 1 : 0;
    });
    fallen.forEach((p, i) => {
      p.setAttribute("fill", petalColor);
      p.style.opacity = i < petals.length - shown ? 0.85 : 0;
    });
    center.setAttribute("fill", mixColor(f.center, "#6e5638", h));

    leaves.forEach(({ node, side, y }) => {
      node.setAttribute("fill", mixColor("#6f9f62", "#9b8a5a", h));
      node.setAttribute("transform", `rotate(${side * bend * 40} ${f.x} ${y})`);
    });

    sway.classList.toggle("is-thriving", h > 0.75);
  };

  // h: 0 = dead, 1 = thriving
  const draw = (h) => {
    flowers.forEach((fl) => drawFlower(fl, clamp((h - fl.f.t) / (1 - fl.f.t))));
    const grassColor = mixColor("#7aa86a", "#a8956a", h);
    grass.forEach((g) => g.setAttribute("stroke", grassColor));
  };

  const animateTo = (target) => {
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduce) return draw(target);
    const from = 0.5;
    const start = performance.now();
    const step = (now) => {
      const t = Math.min(1, (now - start) / 1400);
      const eased = 1 - Math.pow(1 - t, 3);
      draw(mix(from, target, eased));
      if (t < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  };

  const describe = ({ daysSince }) => {
    if (daysSince === null) return "no commits lately — water me";
    return "fed by git commits";
  };

  const health = ({ activeDays, daysSince }) => {
    if (daysSince === null) return 0;
    const recency = Math.max(0, 1 - daysSince / WINDOW_DAYS);
    const frequency = Math.min(1, activeDays / 6);
    return 0.55 * recency + 0.45 * frequency;
  };

  const summarize = (events) => {
    const now = Date.now();
    const days = new Set();
    let latest = null;
    events
      .filter((e) => e.type === "PushEvent")
      .forEach((e) => {
        const t = Date.parse(e.created_at);
        if (latest === null || t > latest) latest = t;
        if (now - t <= WINDOW_DAYS * DAY_MS) days.add(new Date(t).toDateString());
      });
    return {
      activeDays: days.size,
      daysSince: latest === null ? null : Math.floor((now - latest) / DAY_MS),
    };
  };

  const readCache = () => {
    try {
      const cached = JSON.parse(localStorage.getItem(CACHE_KEY));
      if (cached && Date.now() - cached.at < CACHE_MS) return cached.stats;
    } catch (_) {}
    return null;
  };

  const writeCache = (stats) => {
    try {
      localStorage.setItem(CACHE_KEY, JSON.stringify({ at: Date.now(), stats }));
    } catch (_) {}
  };

  const show = (stats) => {
    const text = describe(stats);
    caption.textContent = text;
    root.setAttribute("aria-label", `GitHub activity garden: ${text}`);
    animateTo(health(stats));
  };

  draw(0.5);

  // Preview any state with ?flower=0..1
  const preview = parseFloat(new URLSearchParams(location.search).get("flower"));
  if (preview >= 0 && preview <= 1) {
    caption.textContent = `preview: health ${preview}`;
    return draw(preview);
  }

  const cached = readCache();
  if (cached) return show(cached);

  fetch(`https://api.github.com/users/${user}/events/public?per_page=100`, {
    headers: { Accept: "application/vnd.github+json" },
  })
    .then((res) => (res.ok ? res.json() : Promise.reject(res.status)))
    .then((events) => {
      const stats = summarize(events);
      writeCache(stats);
      show(stats);
    })
    .catch(() => {
      caption.textContent = "couldn't reach GitHub";
      animateTo(0.6);
    });
})();

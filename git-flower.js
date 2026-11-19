// A small flower that blooms or wilts with recent public GitHub activity.
(() => {
  const root = document.querySelector("[data-git-flower]");
  if (!root) return;

  const user = root.dataset.user;
  const svg = root.querySelector("svg");
  const stem = svg.querySelector(".gf-stem");
  const head = svg.querySelector(".gf-head");
  const petals = Array.from(svg.querySelectorAll(".gf-petal"));
  const center = svg.querySelector(".gf-center");
  const leaves = Array.from(svg.querySelectorAll(".gf-leaf"));
  const fallen = Array.from(svg.querySelectorAll(".gf-fallen"));
  const caption = root.querySelector(".gf-caption");

  const WINDOW_DAYS = 14;
  const CACHE_KEY = `git-flower:${user}`;
  const CACHE_MS = 60 * 60 * 1000;
  const DAY_MS = 24 * 60 * 60 * 1000;

  const mix = (a, b, t) => a + (b - a) * t;
  const hex = (c) => [1, 3, 5].map((i) => parseInt(c.slice(i, i + 2), 16));
  const mixColor = (alive, dead, h) => {
    const [a, b] = [hex(alive), hex(dead)];
    return `rgb(${a.map((v, i) => Math.round(mix(b[i], v, h))).join(",")})`;
  };

  // h: 0 = dead, 1 = thriving
  const draw = (h) => {
    const bend = 1 - h;
    const topX = 20 + 9 * bend;
    const topY = 20 + 9 * bend;
    stem.setAttribute("d", `M20 56 Q${20 - 2 * bend} ${36 - 4 * bend} ${topX} ${topY}`);
    stem.setAttribute("stroke", mixColor("#5e8c55", "#8a7a52", h));
    head.setAttribute("transform", `translate(${topX} ${topY}) rotate(${bend * 125}) scale(${mix(0.78, 1, h)})`);

    const petalColor = mixColor("#e8879f", "#a48b6a", h);
    const shown = Math.round(1 + 5 * h);
    petals.forEach((p, i) => {
      p.setAttribute("fill", petalColor);
      p.style.opacity = i < shown ? 1 : 0;
    });
    fallen.forEach((p, i) => {
      p.setAttribute("fill", petalColor);
      p.style.opacity = i < petals.length - shown ? 0.85 : 0;
    });
    center.setAttribute("fill", mixColor("#f2c14e", "#6e5638", h));

    leaves.forEach((leaf) => {
      const side = Number(leaf.dataset.side);
      leaf.setAttribute("fill", mixColor("#6f9f62", "#9b8a5a", h));
      leaf.setAttribute("transform", `rotate(${side * bend * 40} 20 ${leaf.dataset.y})`);
    });

    root.classList.toggle("is-thriving", h > 0.75);
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
    root.setAttribute("aria-label", `GitHub activity flower: ${text}`);
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

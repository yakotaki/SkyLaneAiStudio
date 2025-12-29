/* bgfx.js
   Subtle animated background for SkyLane AI Studio.

   - No external dependencies
   - Reads theme colors from CSS variables: --accent, --accent2, --accent3
   - Respects prefers-reduced-motion
   - Low-cost rendering (limited particle count)
*/

(() => {
  'use strict';

  const canvas = document.getElementById('bgfx-canvas');
  if (!canvas) return;

  const ctx = canvas.getContext('2d', { alpha: true });
  if (!ctx) return;

  const isWechat = (document.body && document.body.dataset && document.body.dataset.wechat === '1');
  const bgfxMode = (document.documentElement.getAttribute('data-bgfx') || '').toLowerCase(); // animate|static|auto
  const forceAnimate = bgfxMode === 'animate';
  const forceStatic  = bgfxMode === 'static';

  const reducedMotionPref = !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  const reducedMotion = forceStatic ? true : (forceAnimate ? false : reducedMotionPref);

  const clamp = (n, a, b) => Math.max(a, Math.min(b, n));

  const parseColorToRGB = (raw) => {
    const s = String(raw || '').trim();
    if (!s) return { r: 245, g: 158, b: 11 };

    // #RRGGBB or #RGB
    if (s[0] === '#') {
      let hex = s.slice(1);
      if (hex.length === 3) {
        hex = hex.split('').map(ch => ch + ch).join('');
      }
      if (hex.length === 6) {
        const r = parseInt(hex.slice(0, 2), 16);
        const g = parseInt(hex.slice(2, 4), 16);
        const b = parseInt(hex.slice(4, 6), 16);
        if (Number.isFinite(r) && Number.isFinite(g) && Number.isFinite(b)) {
          return { r, g, b };
        }
      }
    }

    // rgb()/rgba()
    const m = s.match(/rgba?\(([^)]+)\)/i);
    if (m && m[1]) {
      const parts = m[1].split(',').map(x => x.trim());
      const r = parseFloat(parts[0]);
      const g = parseFloat(parts[1]);
      const b = parseFloat(parts[2]);
      if ([r, g, b].every(Number.isFinite)) return { r, g, b };
    }

    return { r: 245, g: 158, b: 11 };
  };

  const rgba = (rgb, a) => `rgba(${rgb.r},${rgb.g},${rgb.b},${a})`;

  const getVar = (name, fallback) => {
    const v = getComputedStyle(document.documentElement).getPropertyValue(name);
    return (v && v.trim()) ? v.trim() : fallback;
  };

  let W = 0;
  let H = 0;
  let DPR = 1;
  let particles = [];
  let palette = [];
  let maxDist = 140;
  let maxDist2 = maxDist * maxDist;
  let baseDotAlpha = 0.30;
  let baseLineAlpha = 0.16;

  const isMidnight = () => (document.documentElement.getAttribute('data-theme') || '').toLowerCase() === 'midnight';

  const recomputePalette = () => {
    const a1 = parseColorToRGB(getVar('--accent', '#f59e0b'));
    const a2 = parseColorToRGB(getVar('--accent2', '#22c55e'));
    const a3 = parseColorToRGB(getVar('--accent3', '#38bdf8'));
    palette = [a1, a2, a3];

    if (isMidnight()) {
      baseDotAlpha = 0.42;
      baseLineAlpha = 0.22;
    } else {
      baseDotAlpha = 1;
      baseLineAlpha = 1;
    }
  };

  const resize = () => {
    DPR = clamp(window.devicePixelRatio || 1, 1, 2);
    W = Math.max(1, Math.floor(window.innerWidth));
    H = Math.max(1, Math.floor(window.innerHeight));

    canvas.width = Math.floor(W * DPR);
    canvas.height = Math.floor(H * DPR);
    ctx.setTransform(DPR, 0, 0, DPR, 0, 0);

    // Tune by device + viewport
    maxDist = isWechat ? 110 : 140;
    maxDist2 = maxDist * maxDist;

    initParticles();
    renderOnce();
  };

  const initParticles = () => {
    const area = W * H;
    const rawCount = Math.round(area / 28000);
    const minCount = isWechat ? 22 : 28;
    const maxCount = isWechat ? 55 : 120;
    const count = clamp(rawCount, minCount, maxCount);

    const speed = (isWechat ? 0.16 : 0.22) * (isMidnight() ? 1.0 : 0.9);

    particles = Array.from({ length: count }, () => {
      const c = palette[Math.floor(Math.random() * palette.length)] || palette[0];
      const sign = () => (Math.random() < 0.5 ? -1 : 1);
      return {
        x: Math.random() * W,
        y: Math.random() * H,
        vx: (0.35 + Math.random() * 0.65) * speed * sign(),
        vy: (0.35 + Math.random() * 0.65) * speed * sign(),
        r: 0.9 + Math.random() * 1.8,
        c
      };
    });
  };

  const step = () => {
    for (const p of particles) {
      p.x += p.vx;
      p.y += p.vy;

      if (p.x < -10) p.x = W + 10;
      if (p.x > W + 10) p.x = -10;
      if (p.y < -10) p.y = H + 10;
      if (p.y > H + 10) p.y = -10;
    }
  };

  const draw = () => {
    ctx.clearRect(0, 0, W, H);

    // Lines
    for (let i = 0; i < particles.length; i++) {
      const p = particles[i];
      for (let j = i + 1; j < particles.length; j++) {
        const q = particles[j];
        const dx = p.x - q.x;
        const dy = p.y - q.y;
        const d2 = dx * dx + dy * dy;
        if (d2 > maxDist2) continue;

        const t = 1 - (d2 / maxDist2);
        const a = baseLineAlpha * t;

        // Blend line color between endpoints (cheap approximation)
        const lr = (p.c.r + q.c.r) >> 1;
        const lg = (p.c.g + q.c.g) >> 1;
        const lb = (p.c.b + q.c.b) >> 1;

        ctx.strokeStyle = `rgba(${lr},${lg},${lb},${a})`;
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(p.x, p.y);
        ctx.lineTo(q.x, q.y);
        ctx.stroke();
      }
    }

    // Dots
    for (const p of particles) {
      ctx.fillStyle = rgba(p.c, baseDotAlpha);
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fill();
    }
  };

  let raf = null;

  const loop = () => {
    raf = window.requestAnimationFrame(loop);
    step();
    draw();
  };

  const stop = () => {
    if (raf) window.cancelAnimationFrame(raf);
    raf = null;
  };

  const renderOnce = () => {
    // In reduced motion mode, show a static pattern (no animation).
    draw();
  };

  const start = () => {
    if (reducedMotion) {
      stop();
      renderOnce();
      return;
    }
    if (!raf) loop();
  };

  // Visibility pause to save CPU
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
      stop();
    } else {
      start();
    }
  });

  // Resize (debounced)
  let t = null;
  window.addEventListener('resize', () => {
    window.clearTimeout(t);
    t = window.setTimeout(resize, 120);
  });

  // Theme changes (data-theme on <html>)
  const mo = new MutationObserver((mutations) => {
    for (const m of mutations) {
      if (m.type === 'attributes' && m.attributeName === 'data-theme') {
        recomputePalette();
        initParticles();
        renderOnce();
        break;
      }
    }
  });
  mo.observe(document.documentElement, { attributes: true });

  // Init
  recomputePalette();
  resize();
  start();
})();

// Placeholder animation: a slowly turning ring of dots that breathes in a wave.
const canvas = document.getElementById('animation');
const ctx = canvas.getContext('2d');
const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

const DOTS = 24;
let size = 0;

function resize() {
  const ratio = window.devicePixelRatio || 1;
  size = canvas.clientWidth;
  canvas.width = size * ratio;
  canvas.height = size * ratio;
  ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
}

function draw(time) {
  const t = time / 1000;
  const centre = size / 2;
  const radius = size * 0.35;

  ctx.clearRect(0, 0, size, size);

  for (let i = 0; i < DOTS; i++) {
    const angle = (i / DOTS) * Math.PI * 2;
    const wave = (Math.sin(t * 1.2 - angle * 2) + 1) / 2; // 0..1
    const r = radius + (wave - 0.5) * size * 0.08;
    const x = centre + Math.cos(angle + t * 0.15) * r;
    const y = centre + Math.sin(angle + t * 0.15) * r;

    ctx.beginPath();
    ctx.arc(x, y, size * (0.012 + 0.008 * wave), 0, Math.PI * 2);
    ctx.fillStyle = `rgba(43, 42, 39, ${0.25 + 0.5 * wave})`;
    ctx.fill();
  }

  if (!reduceMotion) requestAnimationFrame(draw);
}

resize();
window.addEventListener('resize', () => {
  resize();
  if (reduceMotion) draw(0);
});
requestAnimationFrame(draw);

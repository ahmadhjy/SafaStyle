(() => {
  const slider = document.querySelector("[data-slider]");
  if (!slider) return;
  const slides = [...slider.querySelectorAll("[data-slide]")];
  const dots = [...slider.querySelectorAll("[data-slide-dot]")];
  const prev = slider.querySelector("[data-slide-prev]");
  const next = slider.querySelector("[data-slide-next]");
  if (slides.length < 2) return;

  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  let index = 0;
  let timer = null;
  const DELAY = 5500;

  function go(i) {
    index = (i + slides.length) % slides.length;
    slides.forEach((s, n) => s.classList.toggle("is-active", n === index));
    dots.forEach((d, n) => d.classList.toggle("is-active", n === index));
  }

  function start() {
    if (reduced) return;
    stop();
    timer = setInterval(() => go(index + 1), DELAY);
  }
  function stop() {
    if (timer) clearInterval(timer);
  }

  next && next.addEventListener("click", () => { go(index + 1); start(); });
  prev && prev.addEventListener("click", () => { go(index - 1); start(); });
  dots.forEach((d) =>
    d.addEventListener("click", () => { go(Number(d.dataset.slideDot)); start(); })
  );

  slider.addEventListener("mouseenter", stop);
  slider.addEventListener("mouseleave", start);

  // Swipe on touch
  let x0 = null;
  slider.addEventListener("touchstart", (e) => (x0 = e.touches[0].clientX), { passive: true });
  slider.addEventListener("touchend", (e) => {
    if (x0 === null) return;
    const dx = e.changedTouches[0].clientX - x0;
    if (Math.abs(dx) > 45) go(index + (dx < 0 ? 1 : -1));
    x0 = null;
    start();
  });

  go(0);
  start();
})();

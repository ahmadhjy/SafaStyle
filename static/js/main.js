document.addEventListener("DOMContentLoaded", () => {
  const prefersReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // Mobile nav
  const toggle = document.querySelector("[data-menu-toggle]");
  if (toggle) {
    toggle.addEventListener("click", () => {
      document.body.classList.toggle("nav-open");
      const open = document.body.classList.contains("nav-open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
  }

  // Header shrink on scroll
  const header = document.querySelector(".site-header");
  const onScroll = () => {
    if (window.scrollY > 20) header.classList.add("is-scrolled");
    else header.classList.remove("is-scrolled");
  };
  onScroll();
  window.addEventListener("scroll", onScroll, { passive: true });

  // Auto-dismiss flashes
  document.querySelectorAll(".flash").forEach((el) => {
    setTimeout(() => {
      el.style.opacity = "0";
      el.style.transition = "opacity .4s ease";
      setTimeout(() => el.remove(), 400);
    }, 4200);
  });

  if (prefersReduced) {
    document.querySelectorAll(".reveal, .reveal-word").forEach((el) =>
      el.classList.add("is-visible")
    );
    return;
  }

  // Scroll reveal with stagger for groups
  const io = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        const el = entry.target;
        const group = el.closest(".reveal-group");
        if (group && !group.dataset.staggered) {
          group.dataset.staggered = "1";
          [...group.querySelectorAll(".reveal")].forEach((child, i) => {
            child.style.transitionDelay = `${Math.min(i * 70, 560)}ms`;
            child.classList.add("is-visible");
          });
        } else {
          el.classList.add("is-visible");
        }
        io.unobserve(el);
      });
    },
    { threshold: 0.12, rootMargin: "0px 0px -8% 0px" }
  );
  document.querySelectorAll(".reveal").forEach((el) => io.observe(el));

  // Hero word cascade
  document.querySelectorAll(".reveal-word").forEach((el, i) => {
    el.style.transitionDelay = `${150 + i * 130}ms`;
    requestAnimationFrame(() => el.classList.add("is-visible"));
  });

  // Hero parallax
  const heroMedia = document.querySelector(".hero-media");
  if (heroMedia) {
    window.addEventListener(
      "scroll",
      () => {
        const y = window.scrollY;
        if (y < window.innerHeight) {
          heroMedia.style.transform = `scale(1.08) translateY(${y * 0.18}px)`;
        }
      },
      { passive: true }
    );
  }
});

document.addEventListener("DOMContentLoaded", () => {
  const prefersReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  const toggle = document.querySelector("[data-menu-toggle]");
  const bagMenu = document.querySelector("[data-bag-menu]");
  const bagToggle = document.querySelector("[data-bag-toggle]");
  const bagPreview = document.querySelector("[data-bag-preview]");

  function setBagOpen(open) {
    if (!bagToggle || !bagPreview) return;
    bagPreview.hidden = !open;
    bagToggle.setAttribute("aria-expanded", open ? "true" : "false");
    document.body.classList.toggle("bag-open", open);
  }

  function closeBag() {
    setBagOpen(false);
  }

  function setNavOpen(open) {
    document.body.classList.toggle("nav-open", open);
    if (toggle) toggle.setAttribute("aria-expanded", open ? "true" : "false");
    document.body.style.overflow = open ? "hidden" : "";
    if (open) {
      closeBag();
      const nav = document.getElementById("primary-nav");
      if (nav) {
        nav.scrollTop = 0;
        const header = document.querySelector(".site-header");
        if (header) {
          const h = header.getBoundingClientRect().height;
          nav.style.maxHeight = `calc(100dvh - ${Math.ceil(h)}px)`;
        }
      }
    }
  }

  // Mobile nav
  if (toggle) {
    toggle.addEventListener("click", () => {
      const open = !document.body.classList.contains("nav-open");
      setNavOpen(open);
    });
  }

  // Bag preview (all devices)
  if (bagToggle && bagPreview) {
    bagToggle.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      const open = bagPreview.hidden;
      if (open) setNavOpen(false);
      setBagOpen(open);
    });

    document.addEventListener("click", (e) => {
      if (!bagMenu) return;
      if (!bagMenu.contains(e.target)) closeBag();
    });

    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") {
        closeBag();
        if (document.body.classList.contains("nav-open")) setNavOpen(false);
      }
    });
  }

  // Expose helpers for store.js after AJAX add-to-bag.
  window.SafaBag = {
    close: closeBag,
    open: () => setBagOpen(true),
    render(items, total, count) {
      const list = document.querySelector("[data-bag-items]");
      const totalEl = document.querySelector("[data-bag-total]");
      const countLabel = document.querySelector("[data-bag-count-label]");
      if (totalEl) {
        totalEl.textContent = `$${Number(total || 0).toFixed(2)}`;
      }
      if (countLabel) {
        countLabel.textContent =
          count > 0 ? `${count} item${count === 1 ? "" : "s"}` : "Empty";
      }
      if (!list) return;
      if (!items || !items.length) {
        list.innerHTML =
          '<p class="bag-preview-empty" data-bag-empty>Your bag is empty.</p>';
        return;
      }
      list.innerHTML = items
        .map((item) => {
          const thumb = item.image
            ? `<img class="bag-preview-thumb" src="${escapeAttr(item.image)}" alt="" width="56" height="72" loading="lazy">`
            : `<span class="bag-preview-thumb bag-preview-thumb--ph" aria-hidden="true"></span>`;
          const label = item.label
            ? `<p class="bag-preview-label">${escapeHtml(item.label)}</p>`
            : "";
          return (
            `<div class="bag-preview-row">${thumb}` +
            `<div class="bag-preview-info">` +
            `<p class="bag-preview-name">${escapeHtml(item.name || "Item")}</p>` +
            label +
            `<p class="bag-preview-qty">Qty ${Number(item.qty) || 1}</p>` +
            `</div>` +
            `<p class="bag-preview-line">$${Number(item.total || 0).toFixed(2)}</p>` +
            `</div>`
          );
        })
        .join("");
    },
  };

  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function escapeAttr(value) {
    return escapeHtml(value).replace(/'/g, "&#39;");
  }

  // Categories dropdown accessibility
  document.querySelectorAll(".nav-dropdown").forEach((dd) => {
    const btn = dd.querySelector(".nav-dropdown-toggle");
    if (!btn) return;
    const sync = () => {
      const open = dd.matches(":focus-within") || dd.classList.contains("is-open");
      btn.setAttribute("aria-expanded", open ? "true" : "false");
    };
    btn.addEventListener("click", () => {
      dd.classList.toggle("is-open");
      sync();
    });
    dd.addEventListener("focusin", sync);
    dd.addEventListener("focusout", () => setTimeout(sync, 0));
  });

  // Header shrink on scroll
  const header = document.querySelector(".site-header");
  const onScroll = () => {
    if (!header) return;
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

  // Hero: no parallax on banner images (keeps wide art sharp on scroll)
});

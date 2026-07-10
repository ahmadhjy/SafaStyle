/* Storefront interactions: add-to-bag from cards, quick-view modal, toasts. */
(() => {
  "use strict";

  const QUICK_ADD_URL = "/cart/quick-add/";
  const QUICK_VIEW_URL = (slug) => `/api/quick-view/${slug}/`;

  function csrfToken() {
    const el = document.getElementById("csrf-token");
    if (el && el.dataset.token) return el.dataset.token;
    const m = document.cookie.match("(^|;)\\s*csrftoken\\s*=\\s*([^;]+)");
    return m ? m.pop() : "";
  }

  // --- Toast ---------------------------------------------------------------
  let toastStack;
  function toast(message, { error = false, link } = {}) {
    if (!toastStack) {
      toastStack = document.createElement("div");
      toastStack.className = "toast-stack";
      document.body.appendChild(toastStack);
    }
    const el = document.createElement("div");
    el.className = "toast" + (error ? " is-error" : "");
    el.innerHTML = link
      ? `${message} <a href="${link.href}">${link.text}</a>`
      : message;
    toastStack.appendChild(el);
    requestAnimationFrame(() => el.classList.add("is-visible"));
    setTimeout(() => {
      el.classList.remove("is-visible");
      setTimeout(() => el.remove(), 300);
    }, 3800);
  }

  // --- Header cart badge ---------------------------------------------------
  function updateCartMeta(count, total) {
    const meta = document.getElementById("cart-meta");
    if (meta) meta.textContent = `${count} / $${Number(total).toFixed(2)}`;
    const badge = document.getElementById("cart-badge");
    if (badge) {
      badge.textContent = String(count);
      badge.classList.toggle("is-empty", count < 1);
    }
    const cartBtn = document.querySelector(".cart-btn");
    if (cartBtn) {
      cartBtn.setAttribute("aria-label", `Bag, ${count} item${count === 1 ? "" : "s"}`);
    }
  }

  // --- Add to bag (AJAX) ---------------------------------------------------
  function addToBag(payload) {
    const body = new URLSearchParams(payload);
    return fetch(QUICK_ADD_URL, {
      method: "POST",
      headers: {
        "X-CSRFToken": csrfToken(),
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body,
    }).then((r) => r.json().then((d) => ({ status: r.status, data: d })));
  }

  function handleAddResult({ data }) {
    if (data.ok) {
      updateCartMeta(data.cart_count, data.cart_total);
      toast(data.message || "Added to your bag.", {
        link: { href: "/cart/", text: "View bag" },
      });
      return true;
    }
    toast(data.error || "Could not add to bag.", { error: true });
    return false;
  }

  // --- Quick-view modal ----------------------------------------------------
  const modal = {
    overlay: null,
    state: null,

    ensure() {
      if (this.overlay) return;
      const overlay = document.createElement("div");
      overlay.className = "qv-overlay";
      overlay.innerHTML = `
        <div class="qv-modal" role="dialog" aria-modal="true" aria-label="Product quick view">
          <div class="qv-media"><img alt="" id="qv-img"></div>
          <div class="qv-body">
            <button type="button" class="qv-close" aria-label="Close">&times;</button>
            <p class="eyebrow" id="qv-eyebrow"></p>
            <h2 id="qv-name"></h2>
            <div class="qv-price price"><span class="was" id="qv-was" hidden></span><span class="now" id="qv-now"></span></div>
            <p class="qv-short" id="qv-short"></p>
            <div class="qv-block" id="qv-color-block" hidden>
              <span class="option-label">Color <span id="qv-color-name"></span></span>
              <div class="qv-swatches" id="qv-colors"></div>
            </div>
            <div class="qv-block" id="qv-size-block" hidden>
              <span class="option-label">Size</span>
              <div class="qv-sizes" id="qv-sizes"></div>
            </div>
            <p class="qv-stock" id="qv-stock">Select options</p>
            <div class="qv-actions">
              <input type="number" id="qv-qty" value="1" min="1" max="99" aria-label="Quantity">
              <button type="button" class="btn btn-gold" id="qv-add" disabled>Add to bag</button>
            </div>
            <a class="qv-full-link" id="qv-full" href="#">View full details</a>
          </div>
        </div>`;
      document.body.appendChild(overlay);
      this.overlay = overlay;

      overlay.addEventListener("click", (e) => {
        if (e.target === overlay || e.target.closest(".qv-close")) this.close();
      });
      document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") this.close();
      });
    },

    close() {
      if (this.overlay) this.overlay.classList.remove("is-open");
    },

    open(slug) {
      this.ensure();
      this.overlay.classList.add("is-open");
      document.getElementById("qv-name").textContent = "Loading…";
      document.getElementById("qv-short").textContent = "";
      fetch(QUICK_VIEW_URL(slug), { headers: { "X-Requested-With": "XMLHttpRequest" } })
        .then((r) => r.json())
        .then((d) => this.render(d))
        .catch(() => {
          toast("Could not load product.", { error: true });
          this.close();
        });
    },

    render(p) {
      this.state = {
        product: p,
        color: null,
        size: null,
        needColor: p.colors.length > 0,
        needSize: p.sizes.length > 0,
      };

      document.getElementById("qv-name").textContent = p.name;
      document.getElementById("qv-short").textContent = p.short_description || "";
      document.getElementById("qv-full").href = p.url;
      document.getElementById("qv-qty").value = 1;

      // Colors
      const colorBlock = document.getElementById("qv-color-block");
      const colorsWrap = document.getElementById("qv-colors");
      colorsWrap.innerHTML = "";
      if (p.colors.length) {
        colorBlock.hidden = false;
        p.colors.forEach((c) => {
          const b = document.createElement("button");
          b.type = "button";
          b.className = "qv-swatch";
          b.style.background = c.hex;
          b.title = c.name;
          b.addEventListener("click", () => this.selectColor(c));
          colorsWrap.appendChild(b);
          b._color = c;
        });
      } else {
        colorBlock.hidden = true;
      }

      // Sizes
      const sizeBlock = document.getElementById("qv-size-block");
      const sizesWrap = document.getElementById("qv-sizes");
      sizesWrap.innerHTML = "";
      if (p.sizes.length) {
        sizeBlock.hidden = false;
        p.sizes.forEach((s) => {
          const b = document.createElement("button");
          b.type = "button";
          b.className = "qv-size";
          b.textContent = s.name;
          b.addEventListener("click", () => this.selectSize(s, b));
          sizesWrap.appendChild(b);
          b._size = s;
        });
      } else {
        sizeBlock.hidden = true;
      }

      this.setImage(null, null);
      // Auto-select the first color so gallery + price populate.
      if (p.colors.length) this.selectColor(p.colors[0]);
      this.update();

      const addBtn = document.getElementById("qv-add");
      addBtn.onclick = () => this.add();
    },

    imagesForColor(colorId) {
      const imgs = this.state.product.images_by_color;
      const key = colorId ? String(colorId) : "default";
      return imgs[key] && imgs[key].length ? imgs[key] : imgs.default || [];
    },

    previewImageForColor(color) {
      if (color && color.preview_image) return color.preview_image;
      const imgs = this.imagesForColor(color ? color.id : null);
      return imgs.length ? imgs[0].url : "";
    },

    setImage(colorId, colorObj) {
      const url = colorObj ? this.previewImageForColor(colorObj) : "";
      const imgs = url ? [{ url, alt: "" }] : this.imagesForColor(colorId);
      const el = document.getElementById("qv-img");
      if (imgs.length) {
        el.src = imgs[0].url;
        el.alt = imgs[0].alt || "";
      } else {
        el.removeAttribute("src");
      }
    },

    selectColor(c) {
      this.state.color = c.id;
      document.getElementById("qv-color-name").textContent = `— ${c.name}`;
      [...document.querySelectorAll("#qv-colors .qv-swatch")].forEach((b) =>
        b.classList.toggle("is-active", b._color.id === c.id)
      );
      this.setImage(c.id, c);
      this.syncSizes();
      this.update();
    },

    selectSize(s, btn) {
      if (btn.disabled) return;
      this.state.size = s.id;
      [...document.querySelectorAll("#qv-sizes .qv-size")].forEach((b) =>
        b.classList.toggle("is-active", b._size.id === s.id)
      );
      this.update();
    },

    syncSizes() {
      const { product, color } = this.state;
      [...document.querySelectorAll("#qv-sizes .qv-size")].forEach((btn) => {
        const sid = btn._size.id;
        const exists = product.variations.some(
          (v) => (!color || v.color_id === color) && v.size_id === sid
        );
        btn.disabled = color != null && !exists;
        if (btn.disabled && this.state.size === sid) {
          this.state.size = null;
          btn.classList.remove("is-active");
        }
      });
    },

    currentVariation() {
      const { product, color, size, needColor, needSize } = this.state;
      if (needColor && color == null) return null;
      if (needSize && size == null) return null;
      return product.variations.find(
        (v) =>
          (!needColor || v.color_id === color) && (!needSize || v.size_id === size)
      );
    },

    update() {
      const stock = document.getElementById("qv-stock");
      const now = document.getElementById("qv-now");
      const was = document.getElementById("qv-was");
      const addBtn = document.getElementById("qv-add");
      const qty = document.getElementById("qv-qty");
      const p = this.state.product;

      const v = this.currentVariation();
      if (!v) {
        now.textContent = `$${p.price}`;
        was.hidden = true;
        stock.textContent =
          this.state.needColor || this.state.needSize ? "Select options" : "Unavailable";
        stock.className = "qv-stock";
        addBtn.disabled = true;
        return;
      }
      now.textContent = `$${v.current_price}`;
      if (v.sale_price && Number(v.sale_price) < Number(v.price)) {
        was.hidden = false;
        was.textContent = `$${v.price}`;
      } else {
        was.hidden = true;
      }
      if (v.in_stock) {
        stock.textContent = "In stock";
        stock.className = "qv-stock in-stock";
        addBtn.disabled = false;
        qty.max = v.stock;
      } else {
        stock.textContent = "Out of stock";
        stock.className = "qv-stock out";
        addBtn.disabled = true;
      }
    },

    add() {
      const { product, color, size } = this.state;
      const addBtn = document.getElementById("qv-add");
      addBtn.disabled = true;
      addToBag({
        product_id: product.id,
        color_id: color || "",
        size_id: size || "",
        quantity: document.getElementById("qv-qty").value || 1,
      })
        .then((res) => {
          if (handleAddResult(res)) this.close();
          else addBtn.disabled = false;
        })
        .catch(() => {
          toast("Network error.", { error: true });
          addBtn.disabled = false;
        });
    },
  };

  // --- Wire up product cards ----------------------------------------------
  document.addEventListener("click", (e) => {
    const quickBtn = e.target.closest("[data-quick]");
    const addBtn = e.target.closest("[data-add]");
    if (!quickBtn && !addBtn) return;

    const card = e.target.closest(".product-card");
    if (!card) return;
    e.preventDefault();

    const slug = card.dataset.slug;
    const isVariable = card.dataset.variable === "1";

    if (quickBtn) {
      modal.open(slug);
      return;
    }
    // add button
    if (isVariable) {
      modal.open(slug); // needs option selection
      return;
    }
    addBtn.disabled = true;
    addToBag({ product_id: card.dataset.productId, quantity: 1 })
      .then((res) => {
        handleAddResult(res);
        addBtn.disabled = false;
      })
      .catch(() => {
        toast("Network error.", { error: true });
        addBtn.disabled = false;
      });
  });
})();

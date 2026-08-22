(() => {
  const root = document.querySelector("[data-product-page]");
  if (!root) return;

  const variations = JSON.parse(document.getElementById("variations-data").textContent);
  const imagesByColor = JSON.parse(document.getElementById("images-data").textContent);

  const mainImg = document.getElementById("gallery-main-img");
  const thumbs = document.getElementById("gallery-thumbs");
  const priceNow = document.getElementById("price-now");
  const priceWas = document.getElementById("price-was");
  const stockNote = document.getElementById("stock-note");
  const addBtn = document.getElementById("add-btn");
  const addForm = document.getElementById("add-form");
  const qtyInput = document.getElementById("quantity");
  const colorLabel = document.getElementById("color-label");
  const lightbox = document.getElementById("gallery-lightbox");
  const lightboxImg = document.getElementById("gallery-lightbox-img");
  const zoomBtn = document.querySelector("[data-gallery-zoom-btn]");
  const zoomClose = document.querySelector("[data-gallery-zoom-close]");
  const galleryMain = document.querySelector("[data-gallery-zoom]");

  let selectedColor = null;
  let selectedSize = null;

  const colorBtns = [...document.querySelectorAll("[data-color-id]")];
  const sizeBtns = [...document.querySelectorAll("[data-size-id]")];

  function showOptionError(message) {
    if (!stockNote) return;
    stockNote.textContent = message;
    stockNote.className = "stock-note stock-note--error";
    stockNote.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  function imagesForColor(colorId) {
    const key = colorId ? String(colorId) : "default";
    const colorImgs = imagesByColor[key] || [];
    const defaultImgs = imagesByColor.default || [];
    const merged = [];
    const seen = new Set();
    [...colorImgs, ...defaultImgs, ...Object.values(imagesByColor).flat()].forEach((img) => {
      if (!img || !img.url || seen.has(img.url)) return;
      seen.add(img.url);
      merged.push(img);
    });
    return merged;
  }

  function openZoom() {
    if (!lightbox || !lightboxImg || !mainImg) return;
    lightboxImg.src = mainImg.src;
    lightboxImg.alt = mainImg.alt || "";
    lightbox.hidden = false;
    lightbox.classList.add("is-open");
    document.body.style.overflow = "hidden";
  }

  function closeZoom() {
    if (!lightbox) return;
    lightbox.classList.remove("is-open");
    lightbox.hidden = true;
    document.body.style.overflow = "";
  }

  zoomBtn?.addEventListener("click", (e) => {
    e.stopPropagation();
    openZoom();
  });
  galleryMain?.addEventListener("click", () => openZoom());
  zoomClose?.addEventListener("click", closeZoom);
  lightbox?.addEventListener("click", (e) => {
    if (e.target === lightbox) closeZoom();
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeZoom();
  });

  function bindThumbButtons() {
    if (!thumbs) return;
    thumbs.querySelectorAll("button[data-thumb-url]").forEach((btn) => {
      btn.addEventListener("click", () => {
        mainImg.src = btn.dataset.thumbUrl;
        thumbs.querySelectorAll("button").forEach((b) => b.classList.remove("is-active"));
        btn.classList.add("is-active");
        btn.scrollIntoView({ behavior: "smooth", block: "nearest", inline: "center" });
      });
    });
  }

  function setGallery(colorId) {
    const imgs = imagesForColor(colorId);
    if (!imgs.length || !mainImg) return;
    mainImg.src = imgs[0].url;
    mainImg.alt = imgs[0].alt || "";
    if (!thumbs) return;

    const serverThumbs = thumbs.querySelectorAll("button[data-thumb-url]");
    if (serverThumbs.length) {
      let activeSet = false;
      serverThumbs.forEach((btn) => {
        const isMatch = imgs.some((img) => img.url === btn.dataset.thumbUrl);
        btn.classList.toggle("is-active", !activeSet && isMatch);
        if (!activeSet && isMatch) activeSet = true;
      });
      if (!activeSet && serverThumbs[0]) {
        serverThumbs[0].classList.add("is-active");
        mainImg.src = serverThumbs[0].dataset.thumbUrl;
      }
      return;
    }
    thumbs.innerHTML = "";
    imgs.forEach((img, idx) => {
      const btn = document.createElement("button");
      btn.type = "button";
      if (idx === 0) btn.classList.add("is-active");
      btn.dataset.thumbUrl = img.url;
      btn.innerHTML = `<img src="${img.url}" alt="" loading="lazy" decoding="async" width="80" height="80">`;
      btn.addEventListener("click", () => {
        mainImg.src = img.url;
        thumbs.querySelectorAll("button").forEach((b) => b.classList.remove("is-active"));
        btn.classList.add("is-active");
        btn.scrollIntoView({ behavior: "smooth", block: "nearest", inline: "center" });
      });
      thumbs.appendChild(btn);
    });
  }

  function variationInStock(v) {
    return Boolean(v && v.in_stock);
  }

  function variationFor(colorId, sizeId) {
    return variations.find(
      (v) =>
        (colorId == null || Number(v.color_id) === Number(colorId)) &&
        (sizeId == null || Number(v.size_id) === Number(sizeId))
    );
  }

  // Walk colors in the order they're shown, then sizes in the order they're
  // shown, and return the first in-stock combination. This matches exactly
  // what the shopper sees (e.g. Black + second size before moving to Gray).
  function firstStockedCombo() {
    const colorIds = colorBtns.length
      ? colorBtns.map((b) => Number(b.dataset.colorId))
      : [null];
    const sizeIds = sizeBtns.length
      ? sizeBtns.map((b) => Number(b.dataset.sizeId))
      : [null];
    for (const cid of colorIds) {
      for (const sid of sizeIds) {
        const v = variationFor(cid, sid);
        if (v && variationInStock(v)) return { colorId: cid, sizeId: sid };
      }
    }
    return null;
  }

  function firstStockedSizeForColor(colorId) {
    for (const btn of sizeBtns) {
      const sid = Number(btn.dataset.sizeId);
      const v = variationFor(colorId, sid);
      if (v && variationInStock(v)) return sid;
    }
    return null;
  }

  function activateColor(colorId) {
    if (!colorBtns.length || colorId == null) return;
    const btn = colorBtns.find((b) => Number(b.dataset.colorId) === Number(colorId));
    if (!btn) return;
    selectedColor = Number(btn.dataset.colorId);
    colorBtns.forEach((b) => b.classList.remove("is-active"));
    btn.classList.add("is-active");
    if (colorLabel) colorLabel.textContent = `— ${btn.title}`;
    setGallery(selectedColor);
  }

  function activateSize(sizeId) {
    if (!sizeBtns.length || sizeId == null) return;
    const btn = sizeBtns.find((b) => Number(b.dataset.sizeId) === Number(sizeId));
    if (!btn) return;
    selectedSize = Number(btn.dataset.sizeId);
    sizeBtns.forEach((b) => b.classList.remove("is-active"));
    btn.classList.add("is-active");
    btn.disabled = false;
  }

  function selectFirstInStockSize() {
    if (!sizeBtns.length) return false;
    const colorId = selectedColor;
    const inStockBtn = sizeBtns.find((b) => {
      if (b.disabled) return false;
      return variations.some(
        (v) =>
          variationInStock(v) &&
          Number(v.size_id) === Number(b.dataset.sizeId) &&
          (colorId == null || Number(v.color_id) === Number(colorId))
      );
    });
    const fallback =
      inStockBtn ||
      sizeBtns.find((b) => !b.disabled) ||
      sizeBtns[0];
    if (!fallback) return false;
    activateSize(fallback.dataset.sizeId);
    return true;
  }

  function findVariation() {
    const needColor = colorBtns.length > 0;
    const needSize = sizeBtns.length > 0;
    if (needColor && selectedColor == null) return null;
    if (needSize && selectedSize == null) return null;
    return variations.find((v) => {
      if (needColor && Number(v.color_id) !== Number(selectedColor)) return false;
      if (needSize && Number(v.size_id) !== Number(selectedSize)) return false;
      return true;
    });
  }

  function syncSizeAvailability() {
    sizeBtns.forEach((btn) => {
      const id = Number(btn.dataset.sizeId);
      const exists =
        selectedColor == null
          ? variations.some((v) => Number(v.size_id) === id)
          : variations.some(
              (v) => Number(v.color_id) === Number(selectedColor) && Number(v.size_id) === id
            );
      btn.disabled = selectedColor != null && !exists;
      if (btn.disabled && selectedSize === id) {
        selectedSize = null;
        btn.classList.remove("is-active");
      }
    });
    syncOosMarkers();
  }

  // Visual only: slash/fade OOS colors and sizes. Does not change selection rules.
  function syncOosMarkers() {
    colorBtns.forEach((btn) => {
      const cid = Number(btn.dataset.colorId);
      const inStock = variations.some(
        (v) => Number(v.color_id) === cid && variationInStock(v)
      );
      btn.classList.toggle("is-oos", !inStock);
    });

    sizeBtns.forEach((btn) => {
      const sid = Number(btn.dataset.sizeId);
      const exists =
        selectedColor == null
          ? variations.some((v) => Number(v.size_id) === sid)
          : variations.some(
              (v) =>
                Number(v.color_id) === Number(selectedColor) && Number(v.size_id) === sid
            );
      const inStock = variations.some((v) => {
        if (Number(v.size_id) !== sid || !variationInStock(v)) return false;
        if (selectedColor == null) return true;
        return Number(v.color_id) === Number(selectedColor);
      });
      btn.classList.toggle("is-oos", exists && !inStock);
    });
  }

  function selectedLabel() {
    const parts = [];
    if (selectedColor != null) {
      const c = colorBtns.find((b) => Number(b.dataset.colorId) === Number(selectedColor));
      if (c) parts.push(c.title);
    }
    if (selectedSize != null) {
      const s = sizeBtns.find((b) => Number(b.dataset.sizeId) === Number(selectedSize));
      if (s) parts.push(s.textContent.trim());
    }
    return parts.join(" / ");
  }

  function updateUI() {
    const v = findVariation();
    if (!v) {
      if (sizeBtns.length && selectedSize == null) {
        stockNote.textContent = "Please select a size";
      } else if (colorBtns.length && selectedColor == null) {
        stockNote.textContent = "Please select a color";
      } else if (colorBtns.length || sizeBtns.length) {
        stockNote.textContent = "Select color & size";
      } else {
        stockNote.textContent = "Unavailable";
      }
      stockNote.className = "stock-note";
      addBtn.disabled = false;
      addBtn.dataset.incomplete = "1";
      return;
    }

    delete addBtn.dataset.incomplete;
    priceNow.textContent = `$${v.current_price}`;
    if (v.sale_price && Number(v.sale_price) < Number(v.price)) {
      priceWas.hidden = false;
      priceWas.textContent = `$${v.price}`;
    } else {
      priceWas.hidden = true;
    }

    if (v.in_stock) {
      stockNote.textContent = "In stock";
      stockNote.className = "stock-note in-stock";
      addBtn.disabled = false;
      qtyInput.max = v.stock;
      if (parseInt(qtyInput.value, 10) > v.stock) {
        qtyInput.value = String(Math.max(1, v.stock));
      }
      qtyInput.dispatchEvent(new Event("change"));
      const stepper = qtyInput.closest("[data-qty-stepper]");
      if (stepper) {
        const minus = stepper.querySelector("[data-qty-minus]");
        const plus = stepper.querySelector("[data-qty-plus]");
        const val = parseInt(qtyInput.value, 10) || 1;
        if (minus) minus.disabled = val <= 1;
        if (plus) plus.disabled = val >= v.stock;
      }
      addForm.action = `/cart/add/${v.id}/`;
    } else {
      const hasOther = variations.some(variationInStock);
      const label = selectedLabel();
      stockNote.textContent = hasOther
        ? `${label || "This option"} is out of stock — try another color or size`
        : "Currently out of stock";
      stockNote.className = "stock-note out";
      addBtn.disabled = true;
    }
  }

  function applyColor(btn) {
    activateColor(btn.dataset.colorId);
    syncSizeAvailability();
    // Keep the shopper on the color they chose; pick its first in-stock size.
    const sid = firstStockedSizeForColor(selectedColor);
    if (sid != null) {
      activateSize(sid);
    } else {
      selectFirstInStockSize();
    }
    updateUI();
  }

  function selectInitialStockedOptions() {
    const pick = firstStockedCombo();
    if (pick) {
      if (pick.colorId != null && colorBtns.length) {
        activateColor(pick.colorId);
      } else {
        setGallery(null);
      }
      syncSizeAvailability();
      if (pick.sizeId != null && sizeBtns.length) {
        activateSize(pick.sizeId);
      }
      updateUI();
      return;
    }
    // Nothing is in stock — still select the first shown color/size so the
    // options are highlighted, and the note explains it's out of stock.
    if (colorBtns.length) {
      activateColor(colorBtns[0].dataset.colorId);
    } else {
      setGallery(null);
    }
    syncSizeAvailability();
    if (sizeBtns.length) selectFirstInStockSize();
    updateUI();
  }

  colorBtns.forEach((btn) => {
    btn.addEventListener("click", () => applyColor(btn));
  });

  sizeBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      if (btn.disabled) return;
      activateSize(btn.dataset.sizeId);
      updateUI();
    });
  });

  bindThumbButtons();
  selectInitialStockedOptions();

  addForm?.addEventListener("submit", (e) => {
    const v = findVariation();
    if (!v || addBtn.dataset.incomplete === "1") {
      e.preventDefault();
      if (sizeBtns.length && selectedSize == null) {
        showOptionError("Please select a size before adding to your bag.");
      } else if (colorBtns.length && selectedColor == null) {
        showOptionError("Please select a color before adding to your bag.");
      } else {
        showOptionError("Please select the available options before adding to your bag.");
      }
      return;
    }
    if (!v.in_stock) {
      e.preventDefault();
      showOptionError("This option is out of stock — try another color or size.");
    }
  });
})();

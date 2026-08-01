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

  function sizeMatchesVariation(sizeId, colorId) {
    return variations.some((v) => {
      const sizeOk = Number(v.size_id) === Number(sizeId);
      if (!sizeOk) return false;
      if (colorBtns.length && colorId != null) {
        return Number(v.color_id) === Number(colorId);
      }
      return true;
    });
  }

  function selectFirstAvailableSize() {
    if (!sizeBtns.length) return false;
    // Prefer first size that exists for the current color (even if out of stock),
    // so the pill is always selected and the shopper sees a clear stock state.
    let first =
      sizeBtns.find((b) => !b.disabled && sizeMatchesVariation(b.dataset.sizeId, selectedColor)) ||
      sizeBtns.find((b) => !b.disabled) ||
      sizeBtns[0];
    if (!first) return false;
    selectedSize = Number(first.dataset.sizeId);
    sizeBtns.forEach((b) => b.classList.remove("is-active"));
    first.classList.add("is-active");
    first.disabled = false;
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
      if (!needColor && v.color_id != null && colorBtns.length) return false;
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
      // Keep button clickable so shoppers always get feedback.
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
      addForm.action = `/cart/add/${v.id}/`;
    } else {
      stockNote.textContent = "Out of stock";
      stockNote.className = "stock-note out";
      addBtn.disabled = true;
    }
  }

  function applyColor(btn) {
    selectedColor = Number(btn.dataset.colorId);
    colorBtns.forEach((b) => b.classList.remove("is-active"));
    btn.classList.add("is-active");
    if (colorLabel) colorLabel.textContent = `— ${btn.title}`;
    setGallery(selectedColor);
    syncSizeAvailability();
    selectFirstAvailableSize();
    updateUI();
  }

  colorBtns.forEach((btn) => {
    btn.addEventListener("click", () => applyColor(btn));
  });

  sizeBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      if (btn.disabled) return;
      selectedSize = Number(btn.dataset.sizeId);
      sizeBtns.forEach((b) => b.classList.remove("is-active"));
      btn.classList.add("is-active");
      updateUI();
    });
  });

  bindThumbButtons();
  if (colorBtns.length) {
    applyColor(colorBtns[0]);
  } else {
    setGallery(null);
    if (sizeBtns.length) selectFirstAvailableSize();
    updateUI();
  }

  // Single-size products: always force-select after init.
  if (sizeBtns.length === 1) {
    selectFirstAvailableSize();
    updateUI();
  }

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
      showOptionError("This option is out of stock.");
    }
  });
})();

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
    if (!imgs.length) return;
    mainImg.src = imgs[0].url;
    mainImg.alt = imgs[0].alt || "";
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

  function findVariation() {
    return variations.find((v) => {
      const colorOk = selectedColor ? v.color_id === selectedColor : v.color_id == null || !colorBtns.length;
      const sizeOk = selectedSize ? v.size_id === selectedSize : v.size_id == null || !sizeBtns.length;
      // When colors exist, require color; when sizes exist, require size
      const needColor = colorBtns.length > 0;
      const needSize = sizeBtns.length > 0;
      if (needColor && selectedColor == null) return false;
      if (needSize && selectedSize == null) return false;
      if (needColor && v.color_id !== selectedColor) return false;
      if (needSize && v.size_id !== selectedSize) return false;
      if (!needColor && !needSize) return true;
      return true;
    });
  }

  function availableSizesForColor(colorId) {
    const set = new Set();
    variations.forEach((v) => {
      if ((!colorId || v.color_id === colorId) && v.in_stock && v.size_id) {
        set.add(v.size_id);
      }
    });
    return set;
  }

  function syncSizeAvailability() {
    const available = availableSizesForColor(selectedColor);
    sizeBtns.forEach((btn) => {
      const id = Number(btn.dataset.sizeId);
      const ok = !selectedColor || available.has(id) || variations.some(
        (v) => v.color_id === selectedColor && v.size_id === id
      );
      btn.disabled = selectedColor != null && !variations.some(
        (v) => v.color_id === selectedColor && v.size_id === id
      );
      if (btn.disabled && selectedSize === id) {
        selectedSize = null;
        btn.classList.remove("is-active");
      }
    });
  }

  function updateUI() {
    const v = findVariation();
    if (!v) {
      stockNote.textContent = colorBtns.length || sizeBtns.length
        ? "Select color & size"
        : "Unavailable";
      stockNote.className = "stock-note";
      addBtn.disabled = true;
      return;
    }

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

  colorBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      selectedColor = Number(btn.dataset.colorId);
      colorBtns.forEach((b) => b.classList.remove("is-active"));
      btn.classList.add("is-active");
      if (colorLabel) colorLabel.textContent = `— ${btn.title}`;
      setGallery(selectedColor);
      syncSizeAvailability();
      updateUI();
    });
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

  // Defaults: first color (loads its gallery), first available size
  bindThumbButtons();
  if (colorBtns.length) {
    colorBtns[0].click();
  } else {
    setGallery(null);
    if (sizeBtns.length) sizeBtns[0].click();
    else updateUI();
  }
  if (colorBtns.length && sizeBtns.length) {
    const firstSize = sizeBtns.find((b) => !b.disabled) || sizeBtns[0];
    if (firstSize) firstSize.click();
  }
})();

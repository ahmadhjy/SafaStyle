/* WordPress-style media gallery for the Product admin. */
(function () {
  "use strict";

  function ready(fn) {
    if (document.readyState !== "loading") fn();
    else document.addEventListener("DOMContentLoaded", fn);
  }

  function csrfToken() {
    var el = document.querySelector("input[name=csrfmiddlewaretoken]");
    return el ? el.value : "";
  }

  function el(tag, cls, html) {
    var node = document.createElement(tag);
    if (cls) node.className = cls;
    if (html != null) node.innerHTML = html;
    return node;
  }

  function initGallery(root) {
    var input = document.getElementById(root.dataset.input);
    var grid = root.querySelector("[data-role=grid]");
    var emptyMsg = root.querySelector("[data-role=empty]");
    var addBtn = root.querySelector(".ss-gallery-add");
    var colors = JSON.parse(root.querySelector(".ss-gallery-colors").textContent || "[]");
    var libraryUrl = root.dataset.libraryUrl;
    var uploadUrl = root.dataset.uploadUrl;

    var items = [];
    try {
      items = JSON.parse(input.value || "[]");
    } catch (e) {
      items = [];
    }

    function sync() {
      input.value = JSON.stringify(items);
      emptyMsg.style.display = items.length ? "none" : "";
      input.dispatchEvent(new Event("input", { bubbles: true }));
    }

    function colorOptions(selected) {
      var opts = '<option value="">No color (default gallery)</option>';
      colors.forEach(function (c) {
        var sel = String(c.id) === String(selected) ? " selected" : "";
        opts += '<option value="' + c.id + '"' + sel + ">" + c.name + "</option>";
      });
      return opts;
    }

    function render() {
      grid.innerHTML = "";
      items.forEach(function (item, index) {
        var card = el("div", "ss-tile");
        card.setAttribute("draggable", "true");
        card.dataset.index = index;

        var media = el("div", "ss-tile-media");
        media.appendChild(el("img", null)).src = item.url;
        if (item.is_primary) media.appendChild(el("span", "ss-primary-flag", "Primary"));
        card.appendChild(media);

        var body = el("div", "ss-tile-body");

        var colorWrap = el("label", "ss-tile-color");
        colorWrap.appendChild(el("span", null, "Color"));
        var select = el("select");
        select.innerHTML = colorOptions(item.color_id);
        select.addEventListener("change", function () {
          items[index].color_id = select.value ? Number(select.value) : null;
          sync();
        });
        colorWrap.appendChild(select);
        body.appendChild(colorWrap);

        var actions = el("div", "ss-tile-actions");
        var star = el(
          "button",
          "ss-tile-btn" + (item.is_primary ? " is-on" : ""),
          "&#9733; Primary"
        );
        star.type = "button";
        star.addEventListener("click", function () {
          items.forEach(function (it, i) {
            it.is_primary = i === index;
          });
          render();
          sync();
        });
        actions.appendChild(star);

        var remove = el("button", "ss-tile-btn ss-tile-remove", "Remove");
        remove.type = "button";
        remove.addEventListener("click", function () {
          items.splice(index, 1);
          render();
          sync();
        });
        actions.appendChild(remove);
        body.appendChild(actions);

        card.appendChild(body);

        // drag reorder
        card.addEventListener("dragstart", function (e) {
          e.dataTransfer.setData("text/plain", index);
          card.classList.add("is-dragging");
        });
        card.addEventListener("dragend", function () {
          card.classList.remove("is-dragging");
        });
        card.addEventListener("dragover", function (e) {
          e.preventDefault();
        });
        card.addEventListener("drop", function (e) {
          e.preventDefault();
          var from = Number(e.dataTransfer.getData("text/plain"));
          var to = index;
          if (from === to || isNaN(from)) return;
          var moved = items.splice(from, 1)[0];
          items.splice(to, 0, moved);
          render();
          sync();
        });

        grid.appendChild(card);
      });
    }

    function addAssets(assets) {
      assets.forEach(function (a) {
        // avoid duplicates by asset id
        var exists = items.some(function (it) {
          return it.asset_id && String(it.asset_id) === String(a.id);
        });
        if (exists) return;
        items.push({
          image_id: null,
          asset_id: a.id,
          url: a.url,
          color_id: null,
          is_primary: false,
        });
      });
      if (!items.some(function (it) { return it.is_primary; }) && items.length) {
        items[0].is_primary = true;
      }
      render();
      sync();
    }

    /* ---------------- Modal ---------------- */
    function openModal() {
      var overlay = el("div", "ss-modal-overlay");
      var modal = el("div", "ss-modal");

      var header = el("div", "ss-modal-head");
      header.appendChild(el("h2", null, "Add media"));
      var close = el("button", "ss-modal-close", "&times;");
      close.type = "button";
      header.appendChild(close);
      modal.appendChild(header);

      var tabs = el("div", "ss-modal-tabs");
      var tabLib = el("button", "ss-tab is-active", "Media Library");
      var tabUp = el("button", "ss-tab", "Upload files");
      tabLib.type = "button";
      tabUp.type = "button";
      tabs.appendChild(tabUp);
      tabs.appendChild(tabLib);
      modal.appendChild(tabs);

      var bodyLib = el("div", "ss-modal-body");
      var searchWrap = el("div", "ss-lib-search");
      var searchInput = el("input");
      searchInput.type = "search";
      searchInput.className = "ss-lib-search-input";
      searchInput.placeholder = "Search by file name or title…";
      searchInput.setAttribute("autocomplete", "off");
      searchWrap.appendChild(searchInput);
      bodyLib.appendChild(searchWrap);
      var libGrid = el("div", "ss-lib-grid");
      bodyLib.appendChild(libGrid);

      var bodyUp = el("div", "ss-modal-body");
      bodyUp.style.display = "none";
      var drop = el(
        "div",
        "ss-dropzone",
        "<p><strong>Drop files here</strong> or click to select</p>" +
          "<p class='ss-dz-hint'>Uploads are added to the library and selected below.</p>"
      );
      var fileInput = el("input");
      fileInput.type = "file";
      fileInput.multiple = true;
      fileInput.accept = "image/*";
      fileInput.style.display = "none";
      bodyUp.appendChild(drop);
      bodyUp.appendChild(fileInput);

      modal.appendChild(bodyLib);
      modal.appendChild(bodyUp);

      var footer = el("div", "ss-modal-foot");
      var count = el("span", "ss-sel-count", "0 selected");
      var insert = el("button", "ss-insert button", "Add to product");
      insert.type = "button";
      footer.appendChild(count);
      footer.appendChild(insert);
      modal.appendChild(footer);

      overlay.appendChild(modal);
      document.body.appendChild(overlay);

      var selected = {};

      function updateCount() {
        var n = Object.keys(selected).length;
        count.textContent = n + " selected";
      }

      var searchTimer = null;

      function renderLibraryCells(assets) {
        libGrid.innerHTML = "";
        if (!assets.length) {
          var query = searchInput.value.trim();
          libGrid.innerHTML = query
            ? "<p class='ss-lib-loading'>No images match “" + query + "”.</p>"
            : "<p class='ss-lib-loading'>Library is empty. Use “Upload files”.</p>";
          return;
        }
        assets.forEach(function (a) {
          var cell = el("button", "ss-lib-cell");
          cell.type = "button";
          if (a.title) cell.title = a.title;
          cell.appendChild(el("img", null)).src = a.url;
          if (selected[a.id]) cell.classList.add("is-selected");
          cell.addEventListener("click", function () {
            if (selected[a.id]) {
              delete selected[a.id];
              cell.classList.remove("is-selected");
            } else {
              selected[a.id] = a;
              cell.classList.add("is-selected");
            }
            updateCount();
          });
          libGrid.appendChild(cell);
        });
      }

      function loadLibrary(query) {
        var q = (query || "").trim();
        libGrid.innerHTML = "<p class='ss-lib-loading'>Loading…</p>";
        var url = libraryUrl + (q ? "?q=" + encodeURIComponent(q) : "");
        fetch(url, { credentials: "same-origin" })
          .then(function (r) { return r.json(); })
          .then(function (data) {
            renderLibraryCells(data.assets || []);
          })
          .catch(function () {
            libGrid.innerHTML = "<p class='ss-lib-loading'>Failed to load library.</p>";
          });
      }

      function uploadFiles(fileList) {
        if (!fileList || !fileList.length) return;
        var fd = new FormData();
        Array.prototype.forEach.call(fileList, function (f) {
          fd.append("files", f);
        });
        drop.classList.add("is-busy");
        drop.querySelector("strong").textContent = "Uploading…";
        fetch(uploadUrl, {
          method: "POST",
          credentials: "same-origin",
          headers: { "X-CSRFToken": csrfToken() },
          body: fd,
        })
          .then(function (r) { return r.json(); })
          .then(function (data) {
            drop.classList.remove("is-busy");
            drop.querySelector("strong").textContent = "Drop files here";
            (data.assets || []).forEach(function (a) {
              selected[a.id] = a;
            });
            updateCount();
            tabLib.click();
            loadLibrary();
          })
          .catch(function () {
            drop.classList.remove("is-busy");
            drop.querySelector("strong").textContent = "Upload failed — retry";
          });
      }

      searchInput.addEventListener("input", function () {
        clearTimeout(searchTimer);
        searchTimer = setTimeout(function () {
          loadLibrary(searchInput.value);
        }, 280);
      });

      tabLib.addEventListener("click", function () {
        tabLib.classList.add("is-active");
        tabUp.classList.remove("is-active");
        bodyLib.style.display = "";
        bodyUp.style.display = "none";
        searchInput.focus();
      });
      tabUp.addEventListener("click", function () {
        tabUp.classList.add("is-active");
        tabLib.classList.remove("is-active");
        bodyUp.style.display = "";
        bodyLib.style.display = "none";
      });

      drop.addEventListener("click", function () { fileInput.click(); });
      fileInput.addEventListener("change", function () { uploadFiles(fileInput.files); });
      drop.addEventListener("dragover", function (e) {
        e.preventDefault();
        drop.classList.add("is-over");
      });
      drop.addEventListener("dragleave", function () { drop.classList.remove("is-over"); });
      drop.addEventListener("drop", function (e) {
        e.preventDefault();
        drop.classList.remove("is-over");
        uploadFiles(e.dataTransfer.files);
      });

      function destroy() { document.body.removeChild(overlay); }
      close.addEventListener("click", destroy);
      overlay.addEventListener("click", function (e) {
        if (e.target === overlay) destroy();
      });
      insert.addEventListener("click", function () {
        addAssets(Object.keys(selected).map(function (k) { return selected[k]; }));
        destroy();
      });

      loadLibrary();
    }

    addBtn.addEventListener("click", openModal);
    render();
    sync();
  }

  ready(function () {
    document.querySelectorAll(".ss-gallery").forEach(initGallery);
  });
})();

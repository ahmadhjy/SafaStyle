(() => {
  const body = document.querySelector("[data-legal]");
  const toc = document.querySelector("[data-toc]");
  if (!body || !toc) return;

  const headings = [...body.querySelectorAll("h2")];
  if (!headings.length) {
    toc.style.display = "none";
    return;
  }

  const slugify = (t) =>
    t
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/(^-|-$)/g, "");

  headings.forEach((h) => {
    if (!h.id) h.id = slugify(h.textContent);
    const a = document.createElement("a");
    a.href = `#${h.id}`;
    a.textContent = h.textContent;
    a.addEventListener("click", (e) => {
      e.preventDefault();
      document
        .getElementById(h.id)
        .scrollIntoView({ behavior: "smooth", block: "start" });
      history.replaceState(null, "", `#${h.id}`);
    });
    toc.appendChild(a);
  });
})();

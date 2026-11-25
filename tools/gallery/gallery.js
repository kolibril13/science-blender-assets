async function loadSources() {
  try {
    const response = await fetch("nodebpy/index.json", {cache: "no-cache"});
    const rows = await response.json();
    return new Map(rows.map(([file, type, name, hash]) => [JSON.stringify([file, type, name]), hash]));
  } catch {
    return new Map();
  }
}

function addSourceControls(card, name, hash) {
  const base = "nodebpy/" + hash;
  const dialog = document.querySelector("#source-dialog");
  const menu = document.querySelector("#source-menu");
  const copy = document.createElement("button");
  copy.textContent = "Copy nodebpy";
  copy.title = "Copy Python source. Right-click to view code.";
  function preview() {
    document.querySelector("#source-title").textContent = name;
    dialog.querySelector("iframe").src = base + ".html";
    dialog.showModal();
  }
  copy.onclick = async () => {
    const source = fetch(base + ".py").then(async response => {
      if (!response.ok) throw new Error("Source unavailable");
      return new Blob([await response.text()], {type: "text/plain"});
    });
    try {
      if (window.ClipboardItem && navigator.clipboard?.write) {
        await navigator.clipboard.write([new ClipboardItem({"text/plain": source})]);
      } else {
        await navigator.clipboard.writeText(await (await source).text());
      }
      copy.textContent = "Copied";
    } catch {
      source.catch(() => {});
      copy.textContent = "Copy failed";
      preview();
    }
    setTimeout(() => { copy.textContent = "Copy nodebpy"; }, 1800);
  };
  card.append(copy);
  card.oncontextmenu = event => {
    event.preventDefault();
    menu.showPopover();
    const rect = copy.getBoundingClientRect();
    menu.style.left = Math.min(event.clientX || rect.left, innerWidth - menu.offsetWidth) + "px";
    menu.style.top = Math.min(event.clientY || rect.bottom, innerHeight - menu.offsetHeight) + "px";
    menu.onclick = () => { menu.hidePopover(); preview(); };
    menu.focus();
  };
}

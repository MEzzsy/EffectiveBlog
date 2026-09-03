"use strict";

function topLevelPaths(paths) {
  const unique = [...new Set(paths)];
  return unique.filter(path => !unique.some(parent => parent !== path && path.startsWith(parent + "/")));
}

function canMovePaths(paths, target) {
  return paths.length > 0 && topLevelPaths(paths).every(path =>
    path !== target && !target.startsWith(path + "/") &&
    path.slice(0, Math.max(0, path.lastIndexOf("/"))) !== target
  );
}

function titleWithoutNumber(name) {
  return name.replace(/^[0-9]{1,2}[ -]+/u, "");
}

const nameCollator = new Intl.Collator("zh-CN", { numeric: true, sensitivity: "base" });
function sortEntries(entries) {
  return [...entries].sort((a, b) => (a.kind === b.kind ? 0 : a.kind === "directory" ? -1 : 1)
    || (Number.isFinite(a.sortOrder) && Number.isFinite(b.sortOrder) ? a.sortOrder - b.sortOrder : 0)
    || nameCollator.compare(a.name, b.name) || nameCollator.compare(a.path, b.path));
}

function visibleRows(entries, parent, expanded, query = "") {
  if (query) return sortEntries(entries.filter(entry => entry.path.toLocaleLowerCase().includes(query.toLocaleLowerCase())))
    .map(entry => ({ ...entry, depth: 0 }));
  const groups = new Map();
  for (const entry of entries) {
    if (!groups.has(entry.parent)) groups.set(entry.parent, []);
    groups.get(entry.parent).push(entry);
  }
  const result = [];
  function visit(path, depth) {
    for (const entry of sortEntries(groups.get(path) || [])) {
      result.push({ ...entry, depth });
      if (entry.kind === "directory" && expanded.has(entry.path)) visit(entry.path, depth + 1);
    }
  }
  visit(parent, 0);
  return result;
}

function remapPath(path, mappings) {
  if (path === null) return null;
  const match = mappings.filter(item => path === item.from || path.startsWith(item.from + "/"))
    .sort((a, b) => b.from.length - a.from.length)[0];
  return match ? match.to + path.slice(match.from.length) : path;
}

function reorderProposal(entries, paths, anchor, position) {
  const reference = entries.find(entry => entry.path === anchor);
  const sources = topLevelPaths(paths);
  const isNumbered = entry => entry && !(entry.kind === "file" && titleWithoutNumber(entry.name).toLowerCase() === "readme.md");
  if (!isNumbered(reference) || !sources.length || sources.includes(anchor) || !["before", "after"].includes(position)) return null;
  if (!sources.every(path => {
    const entry = entries.find(item => item.path === path);
    return isNumbered(entry) && entry.parent === reference.parent && entry.kind === reference.kind;
  })) return null;
  const siblings = sortEntries(entries.filter(entry => entry.parent === reference.parent && entry.kind === reference.kind && isNumbered(entry)))
    .map(entry => entry.path);
  const block = siblings.filter(path => sources.includes(path));
  const remaining = siblings.filter(path => !sources.includes(path));
  const index = remaining.indexOf(anchor) + (position === "after" ? 1 : 0);
  const reordered = [...remaining.slice(0, index), ...block, ...remaining.slice(index)];
  if (reordered.every((path, i) => path === siblings[i])) return null;
  return { paths: block, anchor, position };
}

function rowDropIntent(entries, paths, anchor, fraction, allowReorder = true) {
  const entry = entries.find(item => item.path === anchor);
  if (!entry) return null;
  if (entry.kind === "directory" && fraction >= 0.25 && fraction <= 0.75) {
    return canMovePaths(paths, anchor) ? { action: "move", payload: { paths: topLevelPaths(paths), target: anchor } } : null;
  }
  const payload = allowReorder && reorderProposal(entries, paths, anchor, fraction < 0.5 ? "before" : "after");
  return payload ? { action: "reorder", payload } : null;
}

if (typeof module !== "undefined") module.exports = { topLevelPaths, canMovePaths, titleWithoutNumber, visibleRows, remapPath, reorderProposal, rowDropIntent };
if (typeof document !== "undefined") initializeApp();

function initializeApp() {
  const $ = id => document.getElementById(id);
  const token = document.querySelector('meta[name="eb-token"]').content;
  let state = { entries: [], undo: { available: false }, revision: null };
  let current = "", query = "", selected = new Set(), anchor = null, rows = [];
  let expanded = new Set([""]), busy = false, dragging = [], naming = null, moveSources = [], moveTarget = null;
  let listExpanded = new Set();
  let toastTimeout = null;
  const dropTargets = new WeakMap();
  let pointerDrag = null, highlightedDrop = null, suppressClick = false, scrollFrame = null;
  const dragFeedback = element("div", "drag-feedback");
  dragFeedback.setAttribute("role", "status"); dragFeedback.hidden = true; document.body.append(dragFeedback);
  const insertion = element("div", "drop-insertion");
  insertion.hidden = true; insertion.setAttribute("aria-hidden", "true"); document.body.append(insertion);

  function element(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }
  function icon(kind) {
    const node = element("span", kind === "directory" ? "folder-icon" : "document-icon", kind === "file" ? "M↓" : "");
    node.setAttribute("aria-hidden", "true");
    return node;
  }
  function parentOf(path) { const index = path.lastIndexOf("/"); return index < 0 ? "" : path.slice(0, index); }
  function byPath(path) { return state.entries.find(entry => entry.path === path); }
  function children(path) { return sortEntries(state.entries.filter(entry => entry.parent === path)); }
  function showError(message, target = "error") {
    if (target === "error") $("error-message").textContent = message;
    else $(target).textContent = message;
    $(target).hidden = false;
  }
  function toast(message) {
    clearTimeout(toastTimeout);
    $("toast-message").textContent = message;
    $("toast-undo").hidden = !state.undo.available;
    $("toast").hidden = false;
    toastTimeout = setTimeout(() => { $("toast").hidden = true; }, 9000);
  }
  async function request(path, payload) {
    let response;
    try {
      response = await fetch(path, {
        method: payload === undefined ? "GET" : "POST",
        headers: { "X-EB-Token": token, ...(payload === undefined ? {} : { "Content-Type": "application/json" }) },
        ...(payload === undefined ? {} : { body: JSON.stringify(payload) })
      });
    } catch {
      throw new Error("无法连接本地服务。若刚提交了操作，请恢复连接并刷新列表后确认结果。");
    }
    const data = await response.json();
    if (!response.ok) { const error = new Error(data.error || "操作失败"); error.status = response.status; throw error; }
    return data;
  }
  function acceptState(next, focus = false) {
    if (next.pathMappings?.length) {
      const mapped = path => remapPath(path, next.pathMappings);
      current = mapped(current); anchor = mapped(anchor);
      selected = new Set([...selected].map(mapped));
      expanded = new Set([...expanded].map(mapped));
      listExpanded = new Set([...listExpanded].map(mapped));
    }
    state = next;
    selected = new Set([...selected].filter(path => byPath(path)));
    while (current && byPath(current)?.kind !== "directory") current = parentOf(current);
    if (focus && next.focusPaths?.length) {
      while (current && !next.focusPaths.every(path => path.startsWith(current + "/"))) current = parentOf(current);
      selected = new Set(next.focusPaths);
      query = ""; $("search").value = "";
      for (const result of next.focusPaths) {
        let parent = parentOf(result);
        while (parent && parent !== current) { listExpanded.add(parent); parent = parentOf(parent); }
      }
      anchor = next.focusPaths[0];
    }
    listExpanded = new Set([...listExpanded].filter(path => byPath(path)?.kind === "directory"));
    let path = current;
    while (path) { expanded.add(path); path = parentOf(path); }
    render();
    if (focus && next.focusPaths?.length) focusRow(next.focusPaths[0], true);
  }
  async function refresh() {
    if (busy) return;
    $("refresh").disabled = true;
    try { acceptState(await request("/api/state")); $("error").hidden = true; }
    catch (error) { showError(error.message); $("connection-status").textContent = "连接中断"; }
    finally { $("refresh").disabled = busy; }
  }
  function setBusy(value) {
    busy = value;
    document.body.classList.toggle("busy", value);
    for (const control of document.querySelectorAll("dialog input, dialog button")) control.disabled = value;
    for (const button of $("file-list").querySelectorAll("button")) button.disabled = value;
    $("search").disabled = value;
    $("refresh").disabled = value;
    $("select-all").disabled = value || !rows.length;
    $("up").disabled = value || (!current && !query);
    if (!value) $("move-submit").disabled = moveTarget === null;
    updateToolbar();
    if (value) $("connection-status").textContent = "正在处理文件…";
  }
  async function mutate(action, payload, errorTarget = "error") {
    if (busy) return { ok: false, error: "正在执行文件操作，请稍后重试" };
    $(errorTarget).hidden = true;
    $("toast").hidden = true;
    setBusy(true);
    try {
      const next = await request("/api/" + action, { ...payload, revision: state.revision });
      for (const dialog of document.querySelectorAll("dialog[open]")) dialog.close();
      acceptState(next, true);
      const info = next.summary;
      toast(info.message + (info.renumberedItems ? " · 同级改号 " + info.renumberedItems + " 项" : "")
        + (info.updatedReferences ? " · 更新 " + info.updatedReferences + " 处引用" : ""));
      return { ok: true, summary: info, focusPaths: next.focusPaths, revision: next.revision };
    } catch (error) {
      showError(error.message, errorTarget);
      if (error.status === 409) {
        try { acceptState(await request("/api/state")); } catch { /* 保留原始冲突提示。 */ }
      }
      return { ok: false, error: error.message };
    } finally {
      setBusy(false);
      $("connection-status").replaceChildren(element("span", "status-dot"), document.createTextNode("本地连接"));
    }
  }
  function navigate(path) {
    if (busy) return;
    current = path; query = ""; $("search").value = ""; selected.clear(); anchor = null;
    expanded.add(path); render();
  }
  function setupDrop(node, target) {
    dropTargets.set(node, () => typeof target === "function" ? target() : target);
  }
  function setupDrag(node, path) {
    node.draggable = false;
    node.addEventListener("pointerdown", event => {
      if (busy || event.button !== 0 || event.pointerType === "touch" || event.target.closest("input, .tree-toggle, .outline-toggle")) return;
      pointerDrag = { path, x: event.clientX, y: event.clientY, active: false };
    });
  }
  function dropAt(x, y) {
    let node = document.elementFromPoint(x, y);
    const row = node?.closest("#file-list tr");
    if (row) {
      const bounds = row.getBoundingClientRect();
      const intent = rowDropIntent(state.entries, dragging, row.dataset.path, (y - bounds.top) / bounds.height, !query);
      return intent ? { ...intent, node: row } : null;
    }
    while (node && !dropTargets.has(node)) node = node.parentElement;
    if (!node) return null;
    const target = dropTargets.get(node)();
    return target !== null && canMovePaths(dragging, target)
      ? { node, action: "move", payload: { paths: [...dragging], target } } : null;
  }
  function showDrop(destination) {
    if (highlightedDrop) highlightedDrop.classList.remove("drop-target");
    highlightedDrop = null; insertion.hidden = true;
    if (destination?.action === "reorder") {
      const { anchor: reference, position } = destination.payload;
      let edge = destination.node;
      if (position === "after") {
        while (edge.nextElementSibling?.dataset.path.startsWith(reference + "/")) edge = edge.nextElementSibling;
      }
      const bounds = edge.getBoundingClientRect(), surface = document.querySelector(".file-surface").getBoundingClientRect();
      const top = position === "before" ? bounds.top : bounds.bottom;
      const depth = rows.find(entry => entry.path === reference).depth;
      insertion.style.left = (bounds.left + 16 + depth * 20) + "px";
      insertion.style.width = Math.max(0, bounds.width - 26 - depth * 20) + "px";
      insertion.style.top = (top - 1) + "px";
      insertion.hidden = top < $("files").tHead.getBoundingClientRect().bottom || top > surface.bottom;
      dragFeedback.textContent = "调整 " + dragging.length + " 项顺序：放到「" + byPath(reference).name + "」" + (position === "before" ? "之前" : "之后");
    } else if (destination) {
      highlightedDrop = destination.node; highlightedDrop.classList.add("drop-target");
      dragFeedback.textContent = "移入目录：" + (destination.payload.target || state.rootName) + " · " + dragging.length + " 项";
    } else {
      dragFeedback.textContent = "同级同类项目拖到行间排序 · 拖到目录中间移入 · Esc 取消";
    }
  }
  function scrollWhileDragging() {
    scrollFrame = null;
    if (!pointerDrag?.active) return;
    const surface = document.querySelector(".file-surface"), bounds = surface.getBoundingClientRect();
    const { lastX: x, lastY: y } = pointerDrag;
    if (x >= bounds.left && x <= bounds.right && y >= bounds.top && y <= bounds.bottom) {
      const step = y < bounds.top + 64 ? -9 : y > bounds.bottom - 32 ? 9 : 0;
      if (step) { surface.scrollTop += step; showDrop(dropAt(x, y)); }
    }
    scrollFrame = requestAnimationFrame(scrollWhileDragging);
  }
  function finishDrag() {
    if (highlightedDrop) highlightedDrop.classList.remove("drop-target");
    pointerDrag = null; highlightedDrop = null; dragging = [];
    cancelAnimationFrame(scrollFrame); scrollFrame = null;
    insertion.hidden = true; dragFeedback.hidden = true; document.body.classList.remove("dragging");
  }
  document.addEventListener("pointerdown", () => { suppressClick = false; }, true);
  document.addEventListener("pointermove", event => {
    if (!pointerDrag || busy) return;
    if (!pointerDrag.active && Math.hypot(event.clientX - pointerDrag.x, event.clientY - pointerDrag.y) < 6) return;
    if (!pointerDrag.active) {
      if (!selected.has(pointerDrag.path)) { selected = new Set([pointerDrag.path]); updateSelection(); }
      dragging = topLevelPaths([...selected]); pointerDrag.active = true;
      dragFeedback.hidden = false; document.body.classList.add("dragging");
      scrollFrame = requestAnimationFrame(scrollWhileDragging);
    }
    pointerDrag.lastX = event.clientX; pointerDrag.lastY = event.clientY;
    showDrop(dropAt(event.clientX, event.clientY));
  });
  document.addEventListener("pointerup", event => {
    if (!pointerDrag) return;
    const destination = pointerDrag.active ? dropAt(event.clientX, event.clientY) : null;
    suppressClick = pointerDrag.active;
    if (pointerDrag.active) event.preventDefault();
    finishDrag();
    if (destination && !busy) mutate(destination.action, destination.payload);
  });
  document.addEventListener("pointercancel", finishDrag);
  window.addEventListener("blur", finishDrag);
  document.addEventListener("click", event => {
    if (suppressClick) { event.preventDefault(); event.stopPropagation(); suppressClick = false; }
  }, true);
  function renderTree() {
    const tree = $("tree"); tree.replaceChildren();
    function branch(path, name, container) {
      const row = element("div", "tree-row" + (!query && current === path ? " active" : ""));
      const directories = children(path).filter(entry => entry.kind === "directory");
      const toggle = element("button", "tree-toggle", expanded.has(path) ? "▾" : "▸");
      toggle.disabled = !directories.length;
      toggle.setAttribute("aria-label", (expanded.has(path) ? "收起 " : "展开 ") + name);
      toggle.setAttribute("aria-expanded", String(expanded.has(path)));
      toggle.addEventListener("click", () => { if (!busy) { expanded.has(path) ? expanded.delete(path) : expanded.add(path); renderTree(); } });
      const button = element("button", "tree-name");
      button.title = path || state.rootPath || "";
      button.append(icon("directory"), element("span", "tree-label", name));
      if (!query && current === path) button.setAttribute("aria-current", "page");
      button.addEventListener("click", () => navigate(path));
      row.append(toggle, button);
      if (!path) row.append(element("span", "tree-count", state.entries.filter(entry => entry.kind === "file").length));
      setupDrop(row, path); if (path) setupDrag(row, path);
      container.append(row);
      if (expanded.has(path) && directories.length) {
        const nested = element("div", "tree-branch");
        for (const child of directories) branch(child.path, child.name, nested);
        container.append(nested);
      }
    }
    branch("", state.rootName || "EffectiveBlog", tree);
    $("directory-count").textContent = state.entries.filter(entry => entry.kind === "directory").length;
  }
  function renderBreadcrumbs() {
    const navigation = $("breadcrumbs"); navigation.replaceChildren();
    const parts = [["", state.rootName || "EffectiveBlog"]];
    let path = "";
    for (const part of current.split("/").filter(Boolean)) { path = path ? path + "/" + part : part; parts.push([path, part]); }
    for (const [index, [target, name]] of parts.entries()) {
      if (index) navigation.append(element("span", "", "›"));
      const button = element("button", "", name); button.title = target || name; button.addEventListener("click", () => navigate(target));
      setupDrop(button, target); navigation.append(button);
    }
    if (query) navigation.append(element("span", "", "›"), element("span", "", "搜索结果"));
  }
  function select(path, event) {
    if (busy) return;
    const add = event.metaKey || event.ctrlKey || event.target.type === "checkbox";
    if (event.shiftKey && anchor && rows.some(entry => entry.path === anchor)) {
      const start = rows.findIndex(entry => entry.path === anchor), end = rows.findIndex(entry => entry.path === path);
      if (!add) selected.clear();
      for (const entry of rows.slice(Math.min(start, end), Math.max(start, end) + 1)) selected.add(entry.path);
    } else {
      if (add) selected.has(path) ? selected.delete(path) : selected.add(path);
      else selected = new Set([path]);
      anchor = path;
    }
    updateSelection();
  }
  function updateSelection() {
    const tabStop = rows.find(entry => selected.has(entry.path))?.path || rows[0]?.path;
    for (const row of $("file-list").children) {
      const active = selected.has(row.dataset.path);
      row.classList.toggle("selected", active);
      row.setAttribute("aria-selected", String(active));
      row.tabIndex = row.dataset.path === tabStop ? 0 : -1;
    }
    const count = rows.filter(entry => selected.has(entry.path)).length;
    $("select-all").checked = rows.length > 0 && count === rows.length;
    $("select-all").indeterminate = count > 0 && count < rows.length;
    updateToolbar();
  }
  function updateToolbar() {
    $("selection-count").textContent = selected.size ? "已选 " + selected.size + " 项" : query ? "搜索结果" : "当前目录";
    $("item-count").textContent = rows.length + (query ? " 个结果" : " 个可见项目");
    $("rename").disabled = busy || selected.size !== 1;
    $("move").disabled = busy || !selected.size;
    $("mkdir").disabled = busy || !state.revision;
    $("undo").disabled = $("toast-undo").disabled = busy || !state.undo.available;
    $("undo").title = state.undo.available ? "撤销：" + state.undo.label + " · ⌘/Ctrl Z" : "没有可撤销的操作";
    $("up").disabled = busy || (!current && !query);
  }
  function focusRow(path, scroll = false) {
    const target = [...$("file-list").children].find(row => row.dataset.path === path);
    if (!target) return;
    for (const row of $("file-list").children) row.tabIndex = row === target ? 0 : -1;
    target.focus({ preventScroll: true });
    if (scroll) target.scrollIntoView({ block: "nearest" });
  }
  function toggleOutline(path) {
    if (busy || query) return;
    if (listExpanded.has(path)) {
      listExpanded.delete(path);
      const hiddenSelection = [...selected].some(item => item.startsWith(path + "/"));
      selected = new Set([...selected].filter(item => !item.startsWith(path + "/")));
      if (hiddenSelection) selected.add(path);
      if (anchor?.startsWith(path + "/")) anchor = path;
    } else listExpanded.add(path);
    renderRows(); focusRow(path);
  }
  function handleRowKey(event, entry) {
    if (busy || event.target.closest("button")) return;
    const index = rows.findIndex(item => item.path === entry.path);
    let target = null;
    if (["ArrowUp", "ArrowDown", "Home", "End"].includes(event.key)) {
      const position = event.key === "Home" ? 0 : event.key === "End" ? rows.length - 1
        : Math.max(0, Math.min(rows.length - 1, index + (event.key === "ArrowDown" ? 1 : -1)));
      target = rows[position];
    } else if (event.key === "ArrowRight" && !query && entry.kind === "directory") {
      if (!listExpanded.has(entry.path)) toggleOutline(entry.path);
      else if (rows[index + 1]?.parent === entry.path) target = rows[index + 1];
    } else if (event.key === "ArrowLeft" && !query) {
      if (entry.kind === "directory" && listExpanded.has(entry.path)) toggleOutline(entry.path);
      else target = rows.find(item => item.path === entry.parent);
    } else if (event.key === "Enter" && entry.kind === "directory") navigate(entry.path);
    else if (event.key === " ") select(entry.path, event);
    else return;
    event.preventDefault(); event.stopPropagation();
    if (target) { select(target.path, event); focusRow(target.path, true); }
  }
  function renderRows() {
    rows = visibleRows(state.entries, current, listExpanded, query);
    const visible = new Set(rows.map(entry => entry.path));
    selected = new Set([...selected].filter(path => visible.has(path)));
    $("files").classList.toggle("search-results", Boolean(query));
    const body = $("file-list"); body.replaceChildren();
    for (const entry of rows) {
      const row = element("tr"); row.dataset.path = entry.path; row.tabIndex = -1;
      row.setAttribute("aria-level", String(entry.depth + 1));
      if (entry.kind === "directory" && !query) row.setAttribute("aria-expanded", String(listExpanded.has(entry.path)));
      const nameCell = element("td"), name = element("div", "file-name");
      nameCell.setAttribute("role", "gridcell");
      for (let depth = 0; depth < entry.depth; depth++) {
        const indent = element("span", "outline-indent"); indent.setAttribute("aria-hidden", "true"); name.append(indent);
      }
      if (entry.kind === "directory" && !query) {
        const toggle = element("button", "outline-toggle"); toggle.disabled = busy; toggle.tabIndex = -1;
        toggle.setAttribute("aria-label", (listExpanded.has(entry.path) ? "收起 " : "展开 ") + entry.name);
        toggle.setAttribute("aria-expanded", String(listExpanded.has(entry.path)));
        toggle.append(element("span", "chevron"));
        toggle.addEventListener("click", event => { event.stopPropagation(); toggleOutline(entry.path); });
        name.append(toggle);
      } else {
        const spacer = element("span", "outline-spacer"); spacer.setAttribute("aria-hidden", "true"); name.append(spacer);
      }
      const fileIcon = element("span", "entry-icon"); fileIcon.append(icon(entry.kind));
      name.append(fileIcon, element("span", "name-text", entry.name)); name.title = entry.path; nameCell.append(name);
      const pathCell = element("td", "file-path", entry.parent || "根目录"); pathCell.title = entry.parent || "根目录";
      pathCell.setAttribute("role", "gridcell");
      row.append(nameCell, pathCell);
      row.addEventListener("click", event => { if (!event.target.closest("button")) { select(entry.path, event); focusRow(entry.path); } });
      row.addEventListener("dblclick", event => { if (!event.target.closest("button") && entry.kind === "directory") navigate(entry.path); });
      row.addEventListener("keydown", event => handleRowKey(event, entry));
      setupDrag(row, entry.path);
      if (entry.kind === "directory") setupDrop(row, entry.path);
      body.append(row);
    }
    $("empty").hidden = rows.length > 0;
    $("empty-title").textContent = query ? "没有找到匹配的项目" : "目录里还没有文档";
    $("empty-description").textContent = query ? "试试其他名称或路径关键词。" : "可以将文档拖到这里，或新建一个目录。";
    $("select-all").disabled = busy || !rows.length;
    updateSelection();
  }
  function render() {
    renderTree(); renderBreadcrumbs(); renderRows();
    $("heading").textContent = query ? "搜索结果" : current ? byPath(current)?.name || "当前目录" : state.rootName || "全部文档";
    $("description").textContent = query ? "搜索整个工作空间" : "文档与目录";
    $("connection-status").replaceChildren(element("span", "status-dot"), document.createTextNode("本地连接"));
  }
  function openName(action) {
    if (busy || !state.revision || (action === "rename" && selected.size !== 1)) return;
    const entry = action === "rename" ? byPath([...selected][0]) : null;
    naming = { action, entry };
    $("name-title").textContent = action === "rename" ? "重命名" : "新建目录";
    $("name-context").textContent = action === "rename" ? entry.path : "创建于：" + (current || state.rootName);
    $("name-input").value = entry ? titleWithoutNumber(entry.kind === "file" ? entry.name.slice(0, -3) : entry.name) : "";
    $("extension").hidden = entry?.kind !== "file";
    $("extension").textContent = entry?.kind === "file" ? entry.name.slice(-3) : ".md";
    $("name-submit").textContent = action === "rename" ? "保存名称" : "创建目录";
    $("number-hint").textContent = action === "mkdir"
      ? "每个目录内从 01 连续编号，新目录排在末尾，内含空的 README.md。只需填写标题。"
      : "只需填写标题。同级文件和子目录分别从 01 连续编号，README.md 不编号。";
    $("name-error").hidden = true;
    $("name-dialog").showModal(); $("name-input").focus(); $("name-input").select();
  }
  function renderMoveTargets() {
    const container = $("move-targets"); container.replaceChildren();
    const filter = $("move-search").value.trim().toLocaleLowerCase();
    const options = [{ path: "", name: state.rootName }, ...sortEntries(state.entries.filter(entry => entry.kind === "directory"))];
    for (const entry of options) {
      if (!canMovePaths(moveSources, entry.path) || !(entry.path || entry.name).toLocaleLowerCase().includes(filter)) continue;
      const button = element("button", "move-target" + (moveTarget === entry.path ? " selected" : ""));
      button.setAttribute("aria-pressed", String(moveTarget === entry.path));
      button.append(icon("directory"), element("span", "", entry.path || entry.name + "（根目录）"));
      button.addEventListener("click", () => { if (!busy) { moveTarget = entry.path; renderMoveTargets(); $("move-submit").disabled = false; } });
      container.append(button);
    }
    if (!container.children.length) container.append(element("p", "dialog-context", "没有可用的目标目录。"));
  }
  $("search").addEventListener("input", () => { query = $("search").value.trim(); selected.clear(); anchor = null; render(); });
  $("refresh").addEventListener("click", refresh);
  $("up").addEventListener("click", () => navigate(query ? current : parentOf(current)));
  $("mkdir").addEventListener("click", () => openName("mkdir"));
  $("rename").addEventListener("click", () => openName("rename"));
  $("undo").addEventListener("click", () => mutate("undo", {}));
  $("toast-undo").addEventListener("click", () => mutate("undo", {}));
  $("dismiss-error").addEventListener("click", () => { $("error").hidden = true; });
  $("dismiss-toast").addEventListener("click", () => { $("toast").hidden = true; });
  $("select-all").addEventListener("change", () => { if (!busy) { selected = new Set($("select-all").checked ? rows.map(entry => entry.path) : []); updateSelection(); } });
  $("name-form").addEventListener("submit", event => {
    event.preventDefault();
    const name = $("name-input").value.trim();
    if (!name) { showError("请输入名称", "name-error"); return; }
    if (naming.action === "rename") mutate("rename", { path: naming.entry.path, name: name + (naming.entry.kind === "file" ? naming.entry.name.slice(-3) : "") }, "name-error");
    else mutate("mkdir", { parent: current, name }, "name-error");
  });
  $("move").addEventListener("click", () => {
    if (busy || !selected.size) return;
    moveSources = topLevelPaths([...selected]); moveTarget = null;
    $("move-context").textContent = "将 " + moveSources.length + " 个项目移动到目标目录末尾，源目录和目标目录分别从 01 连续编号并更新链接。README.md 不编号。";
    $("move-search").value = ""; $("move-error").hidden = true; $("move-submit").disabled = true;
    renderMoveTargets(); $("move-dialog").showModal(); $("move-search").focus();
  });
  $("move-search").addEventListener("input", renderMoveTargets);
  $("move-submit").addEventListener("click", () => { if (moveTarget !== null) mutate("move", { paths: moveSources, target: moveTarget }, "move-error"); });
  for (const button of document.querySelectorAll(".close-dialog")) button.addEventListener("click", () => { if (!busy) button.closest("dialog").close(); });
  for (const dialog of document.querySelectorAll("dialog")) dialog.addEventListener("cancel", event => { if (busy) event.preventDefault(); });
  setupDrop(document.querySelector(".file-surface"), () => query ? null : current);
  document.addEventListener("keydown", event => {
    suppressClick = false;
    if (event.key === "Escape" && pointerDrag) { event.preventDefault(); finishDrag(); return; }
    if (event.target.closest("input, textarea, dialog") || busy) return;
    if (event.key === "F2") { event.preventDefault(); openName("rename"); }
    if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "z" && !event.shiftKey) { event.preventDefault(); if (state.undo.available) mutate("undo", {}); }
    if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "a") { event.preventDefault(); selected = new Set(rows.map(entry => entry.path)); updateSelection(); }
    if (event.key === "/" && !event.metaKey && !event.ctrlKey) { event.preventDefault(); $("search").focus(); }
  });
  window.addEventListener("focus", () => { if (!busy && !pointerDrag && !document.querySelector("dialog[open]")) refresh(); });
  // 支持该接口的浏览器可调用相同的界面动作；文件操作仍全部在 eb_tool.py。
  const context = document.modelContext;
  if (typeof context?.registerTool === "function") {
    const lifecycle = new AbortController();
    const string = { type: "string" };
    const definitions = [
      ["eb_list_entries", "列出文档与目录", "读取当前仓库中可管理项目的相对路径及撤销状态。", null, {}],
      ["eb_rename_entry", "重命名项目", "重命名并将同级项目从 01 连续编号、维护链接。Markdown 名称须含 .md 扩展名。README.md 不编号。", "rename", { path: string, name: string }],
      ["eb_move_entries", "移动所选项目", "移动多个项目到目标末尾，源目录和目标目录分别从 01 连续编号并维护链接。README.md 不编号。target 为空字符串表示根目录。", "move", { paths: { type: "array", items: string, minItems: 1 }, target: string }],
      ["eb_reorder_entries", "调整同级顺序", "将同目录、同类型的所选项目放到 anchor 项目之前或之后，再从 01 连续编号并维护链接。README.md 不参与排序。", "reorder", { paths: { type: "array", items: string, minItems: 1 }, anchor: string, position: { type: "string", enum: ["before", "after"] } }],
      ["eb_create_directory", "新建目录", "在 parent 下新建目录，内含空的 README.md，同级项目从 01 连续编号；parent 为空字符串表示根目录。", "mkdir", { parent: string, name: string }],
      ["eb_undo_last_operation", "撤销最近操作", "恢复最近一次成功操作的文件位置、引用和目录；外部修改可能使撤销失败。", "undo", {}]
    ];
    for (const [name, title, description, action, properties] of definitions) {
      try {
        Promise.resolve(context.registerTool({
          name, title, description,
          inputSchema: { type: "object", properties, required: Object.keys(properties), additionalProperties: false },
          annotations: { readOnlyHint: action === null, untrustedContentHint: true },
          async execute(input) {
            if (!input || typeof input !== "object" || Array.isArray(input)
                || Object.keys(input).some(key => !Object.hasOwn(properties, key))
                || Object.entries(properties).some(([key, schema]) =>
                  schema.type === "string" ? typeof input[key] !== "string"
                    : !Array.isArray(input[key]) || !input[key].length || input[key].some(value => typeof value !== "string"))) {
              return { ok: false, error: "参数不符合此操作的输入要求" };
            }
            if (busy) return { ok: false, error: "正在执行文件操作，请稍后重试" };
            if (action) return mutate(action, input);
            try {
              acceptState(await request("/api/state"));
              return { ok: true, rootName: state.rootName, entries: state.entries, revision: state.revision, undo: state.undo };
            } catch (error) { return { ok: false, error: error.message }; }
          }
        }, { signal: lifecycle.signal })).catch(error => console.warn("WebMCP 工具注册失败", error));
      } catch (error) { console.warn("WebMCP 工具注册失败", error); }
    }
    window.addEventListener("pagehide", () => lifecycle.abort(), { once: true });
  }
  refresh();
}

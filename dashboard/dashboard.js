"use strict";

const $ = id => document.getElementById(id);
const fields = { confidence: $("confidence"), factType: $("factType"), graph: $("graphFilter"), search: $("search") };
const defaults = { confidence: "all", factType: "both", graph: "", search: "" };
const graphNames = { "urn:ofbiz_structural": "Code & data", "urn:airflow": "Airflow workflows", "urn:cicd": "CI/CD workflows", "urn:ofbiz_semantic": "Code semantics", "urn:document_semantic": "Document semantics", "urn:cuad": "Contracts", "urn:edgar": "SEC filings", "urn:bridges": "Cross-source bridges" };
const emptyInspector = $("provenance").firstElementChild.cloneNode(true);
let currentPayload = { nodes: [], edges: [] };
let network = null;
let graphNodes = null;
let graphEdges = null;
let request = null;
let evidenceRequest = null;
let selectionRequest = 0;
let layoutEnabled = false;
let summary = null;
let resizeTimer = null;
let selectedNodeId = null;
let selectedEdge = null;
let highlightedNodes = new Set();
let hasLoaded = false;
let displayedParams = new URLSearchParams();
let graphPalette = {};

function element(tag, text, className) {
  const item = document.createElement(tag);
  // ASVS V1.2: labels, paths, URIs, and evidence are text, never executable markup.
  if (text !== undefined) item.textContent = text;
  if (className) item.className = className;
  return item;
}
function localName(value) { return String(value || "Unknown").split(/[\/#]/).pop(); }
function readable(value) { return localName(value).replace(/([a-z])([A-Z])/g, "$1 $2").toLowerCase(); }
function percent(value) { return value !== undefined && value !== null && value !== "" && Number.isFinite(Number(value)) ? `${Math.round(Number(value) * 100)}%` : "Unavailable"; }
function nodeById(id) { return currentPayload.nodes.find(node => node.id === id) || { id, label: localName(id) }; }
function nodeType(node) { return localName((node.classes || [node.class])[0]); }
function connectedEdges(uri) { return currentPayload.edges.filter(edge => edge.from === uri || edge.to === uri); }
function setStatus(text, state = "ready") { $("status").textContent = text; $("status").dataset.state = state; }
function message(title, body, retry = false) {
  $("graphMessage").hidden = !title;
  $("messageTitle").textContent = title;
  $("messageBody").textContent = body;
  $("retry").hidden = !retry;
}
async function getJSON(url, signal) {
  const response = await fetch(url, { signal, headers: { Accept: "application/json" } });
  if (!response.ok) throw new Error(`Request failed (${response.status})`);
  return response.json();
}
function appendDetails(container, pairs) {
  const list = element("dl", undefined, "inspect-meta");
  for (const [label, value] of pairs) list.append(element("dt", label), element("dd", value || "Unavailable in this graph"));
  container.append(list);
}
function inspectSection(title) {
  const section = element("section", undefined, "inspect-section");
  section.append(element("h4", title));
  return section;
}
function revealOnMobile(target) {
  if (!target || !matchMedia("(max-width: 700px)").matches) return;
  requestAnimationFrame(() => target.scrollIntoView({
    block: "start", behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "instant" : "smooth"
  }));
}
function inspectLink(label, uri) {
  const button = element("button", label, "node-link");
  button.type = "button";
  button.addEventListener("click", () => selectNode(uri, true));
  return button;
}
function updateSelectionControls() {
  if ($("focusSelection")) $("focusSelection").disabled = !selectedNodeId || !network;
  if ($("clearSelection")) $("clearSelection").disabled = !selectedNodeId && !selectedEdge;
  if ($("selectionBadge")) $("selectionBadge").textContent = selectedNodeId ? nodeType(nodeById(selectedNodeId)) : selectedEdge ? "Relationship" : "No selection";
  for (const button of document.querySelectorAll("#nodelist button[data-node-id]")) button.setAttribute("aria-pressed", String(button.dataset.nodeId === selectedNodeId));
}
function resetInspector() {
  selectionRequest += 1;
  if (evidenceRequest) evidenceRequest.abort();
  evidenceRequest = null;
  selectedNodeId = null;
  selectedEdge = null;
  highlightedNodes = new Set();
  if (network) network.unselectAll();
  applyGraphEmphasis();
  $("provenance").replaceChildren(emptyInspector.cloneNode(true));
  updateSelectionControls();
}
function renderInspectorHeading(panel, node, label = node.label) {
  const header = element("div", undefined, "inspect-header");
  header.append(element("span", nodeType(node), `inspect-type ${category(node)}`), element("h3", label));
  panel.replaceChildren(header);
}
async function selectNode(uri, focus = false, emphasize = true) {
  const selected = nodeById(uri);
  const selection = ++selectionRequest;
  if (evidenceRequest) evidenceRequest.abort();
  const controller = new AbortController();
  evidenceRequest = controller;
  const timeout = setTimeout(() => controller.abort(), 12000);
  selectedNodeId = uri;
  selectedEdge = null;
  highlightedNodes = new Set([uri, ...connectedEdges(uri).flatMap(edge => [edge.from, edge.to])]);
  applyGraphEmphasis(emphasize ? highlightedNodes : null);
  if (network) { network.selectNodes([uri]); if (focus) focusNeighborhood(); }
  updateSelectionControls();
  const panel = $("provenance");
  renderInspectorHeading(panel, selected);
  panel.append(element("p", "Reading source evidence…", "inspect-loading"));
  if (emphasize) revealOnMobile(panel.closest(".inspector"));
  const params = new URLSearchParams({ uri, graph: displayedParams.get("graph") || selected.graph || "" });
  try {
    const prov = await getJSON("/node?" + params, controller.signal);
    if (selection !== selectionRequest) return;
    renderInspectorHeading(panel, selected, prov.label || selected.label);
    const confidence = inspectSection("Extraction confidence");
    const row = element("div", undefined, "confidence-row");
    row.append(element("strong", percent(prov.confidence)), element("span", prov.ft === "probabilistic" ? "Probabilistic" : prov.ft === "deterministic" ? "Deterministic" : "Method unavailable", "inspect-method"));
    confidence.append(row);
    const numeric = prov.confidence !== undefined && prov.confidence !== null && prov.confidence !== "" ? Number(prov.confidence) : NaN;
    if (Number.isFinite(numeric)) {
      const meter = element("div", undefined, "confidence-meter");
      meter.setAttribute("role", "meter"); meter.setAttribute("aria-label", "Extraction confidence");
      meter.setAttribute("aria-valuemin", "0"); meter.setAttribute("aria-valuemax", "100");
      meter.setAttribute("aria-valuenow", String(Math.round(Math.max(0, Math.min(1, numeric)) * 100)));
      const fill = element("span"); fill.style.width = `${Math.max(0, Math.min(1, numeric)) * 100}%`;
      meter.append(fill); confidence.append(meter);
    }
    confidence.append(element("p", prov.ft === "probabilistic" ? "Model or annotation confidence. It has not been calibrated against business truth." : prov.ft === "deterministic" ? "Recorded by a parser or fixed rule. This does not verify the meaning of the fact." : "The extraction method was not recorded for this item.", "inspector-note"));
    panel.append(confidence);
    const source = inspectSection("Source evidence");
    if (prov.source) source.append(element("div", prov.source.replace(/^file:\/\//, ""), "source-code"));
    else source.append(element("p", "A source file was not recorded for this item.", "source-unavailable"));
    source.append(element("p", prov.line ? `Line ${prov.line}${prov.location && prov.location !== `Line ${prov.line}` ? ` · ${prov.location}` : ""}` : prov.location || "Source location unavailable", "source-location"));
    appendDetails(source, [["Extractor / model", prov.extractedBy || (prov.generatedBy ? localName(prov.generatedBy) : "")], ["Evidence graph", graphNames[prov.graph] || prov.graph]]);
    panel.append(source);
    const connections = connectedEdges(uri);
    const relationships = inspectSection(`Visible connections (${connections.length})`);
    if (!connections.length) relationships.append(element("p", "No connected item is visible under the current filters.", "inspector-note"));
    for (const edge of connections) {
      const incoming = edge.to === uri;
      const target = nodeById(incoming ? edge.from : edge.to);
      const button = element("button", undefined, "node-link"); button.type = "button";
      button.append(element("span", `${incoming ? "←" : "→"} ${readable(edge.label)}`, "connection-label"), element("strong", target.label, "connection-target"));
      button.setAttribute("aria-label", `${incoming ? "Incoming" : "Outgoing"} relationship: ${readable(edge.label)}, ${target.label}. Inspect relationship.`);
      button.addEventListener("click", () => showEdge(edge)); relationships.append(button);
    }
    panel.append(relationships);
    const technical = element("details", undefined, "inspect-technical"); technical.append(element("summary", "Technical details"));
    appendDetails(technical, [["Node URI", uri], ["Graph memberships", (selected.graphs || [prov.graph]).map(graph => graphNames[graph] || graph).join(", ")], ["Generated at", prov.generatedAt]]);
    panel.append(technical, element("p", "A node’s source does not establish evidence for every connected arrow. Source text is not exposed by this API.", "inspector-note"));
    // Evidence can expand the page after the loading state; reveal it again
    // once its final height exists, rather than stopping at the old scroll limit.
    if (emphasize) revealOnMobile(panel.closest(".inspector"));
  } catch (_) {
    if (selection !== selectionRequest) return;
    renderInspectorHeading(panel, selected);
    panel.append(element("p", "The graph is available, but this item’s evidence could not be loaded. Check the local server and try again.", "inspector-note"));
    const retry = element("button", "Retry evidence", "evidence-retry"); retry.type = "button";
    retry.addEventListener("click", () => selectNode(uri)); panel.append(retry);
  } finally { clearTimeout(timeout); if (evidenceRequest === controller) evidenceRequest = null; }
}
function showEdge(edge) {
  if (!edge) return;
  selectionRequest += 1;
  if (evidenceRequest) evidenceRequest.abort();
  selectedNodeId = null; selectedEdge = edge;
  highlightedNodes = new Set([edge.from, edge.to]); applyGraphEmphasis(highlightedNodes);
  if (network) { network.unselectAll(); network.selectEdges([`e${currentPayload.edges.indexOf(edge)}`]); }
  updateSelectionControls();
  const panel = $("provenance"), from = nodeById(edge.from), to = nodeById(edge.to);
  const header = element("div", undefined, "inspect-header");
  header.append(element("span", "Recorded arrow", "inspect-type"), element("h3", "Relationship")); panel.replaceChildren(header);
  const path = element("div", undefined, "relationship-path");
  path.append(element("strong", from.label), element("span", `↓ ${readable(edge.label)}`), element("strong", to.label)); panel.append(path);
  const evidence = inspectSection("Relationship evidence");
  appendDetails(evidence, [["Recorded predicate", edge.label], ["Relationship graph", graphNames[edge.graph] || edge.graph]]); panel.append(evidence);
  const endpoints = inspectSection("Explore endpoints");
  endpoints.append(inspectLink(`Source · ${from.label}`, edge.from), inspectLink(`Target · ${to.label}`, edge.to));
  panel.append(endpoints, element("p", "This arrow is recorded in the graph. Endpoint provenance is available above; per-arrow source and calibrated confidence are not exposed by this API.", "inspector-note"));
  revealOnMobile(panel.closest(".inspector"));
}
function category(node) {
  const types = (node.classes || [node.class]).map(localName);
  if (types.some(type => ["DAG", "Task", "Workflow", "Job", "Step"].includes(type))) return "workflow";
  if (node.factType !== "probabilistic" && types.some(type => ["Module", "Service", "Entity", "Field", "JavaClass", "JavaMethod", "ECA"].includes(type))) return "code";
  return "semantic";
}
function wrapLabel(label) {
  const words = String(label || "Unnamed item").split(/\s+/), lines = [];
  let line = "";
  for (const word of words) {
    if (line && line.length + word.length > 24) { lines.push(line.trim()); line = ""; }
    line += (line ? " " : "") + word;
  }
  if (line) lines.push(line.trim());
  return lines.slice(0, 3).map((part, index) => part.length > 30 ? part.slice(0, 28) + "…" : index === 2 && lines.length > 3 ? part + "…" : part).join("\n");
}
function graphPositions() {
  const nodes = currentPayload.nodes, adjacency = new Map(nodes.map(node => [node.id, new Set()]));
  for (const edge of currentPayload.edges) if (adjacency.has(edge.from) && adjacency.has(edge.to)) { adjacency.get(edge.from).add(edge.to); adjacency.get(edge.to).add(edge.from); }
  // Stable, topology-aware positions: connected neighbours begin together;
  // a bounded force pass separates labels without a moving initial viewport.
  const visited = new Set(), ordered = [];
  const roots = [...nodes].sort((a, b) => adjacency.get(b.id).size - adjacency.get(a.id).size || a.id.localeCompare(b.id));
  for (const root of roots) {
    if (visited.has(root.id)) continue;
    const queue = [root.id]; visited.add(root.id);
    for (let i = 0; i < queue.length; i++) {
      const id = queue[i]; ordered.push(id);
      for (const neighbour of adjacency.get(id)) if (!visited.has(neighbour)) { visited.add(neighbour); queue.push(neighbour); }
    }
  }
  const indices = new Map(ordered.map((id, index) => [id, index])), count = nodes.length;
  const radius = Math.max(150, Math.sqrt(count) * 60);
  const points = ordered.map((id, index) => ({ id, x: Math.cos(index * Math.PI * 2 / count - Math.PI / 2) * radius, y: Math.sin(index * Math.PI * 2 / count - Math.PI / 2) * radius }));
  if (count > 180) return new Map(points.map(point => [point.id, point]));
  const k = Math.max(145, Math.min(200, 480 / Math.sqrt(Math.max(1, count))));
  const links = currentPayload.edges.map(edge => [indices.get(edge.from), indices.get(edge.to)]).filter(([from, to]) => from !== undefined && to !== undefined);
  for (let iteration = 0; iteration < 180; iteration++) {
    const forces = points.map(point => ({ x: -point.x * 1.7, y: -point.y * 1.7 }));
    for (let i = 0; i < count; i++) for (let j = i + 1; j < count; j++) {
      const dx = points[i].x - points[j].x || .1, dy = points[i].y - points[j].y || .1, distance = Math.max(1, Math.hypot(dx, dy));
      const repulsion = k * k / distance, fx = dx / distance * repulsion, fy = dy / distance * repulsion;
      forces[i].x += fx; forces[i].y += fy; forces[j].x -= fx; forces[j].y -= fy;
    }
    for (const [from, to] of links) {
      const dx = points[from].x - points[to].x, dy = points[from].y - points[to].y, distance = Math.max(1, Math.hypot(dx, dy));
      const attraction = distance * distance / (k * 1.45), fx = dx / distance * attraction, fy = dy / distance * attraction;
      forces[from].x -= fx; forces[from].y -= fy; forces[to].x += fx; forces[to].y += fy;
    }
    const temperature = 14 * (1 - iteration / 180) + .25;
    for (let i = 0; i < count; i++) {
      const size = Math.max(1, Math.hypot(forces[i].x, forces[i].y));
      points[i].x += forces[i].x / size * Math.min(size, temperature); points[i].y += forces[i].y / size * Math.min(size, temperature);
    }
  }
  // Disconnected components must not force a tiny overview. Give small graphs
  // a bounded frame matching this canvas, leaving room for names and controls.
  if (count <= 80) {
    const xs = points.map(point => point.x), ys = points.map(point => point.y);
    const minX = Math.min(...xs), maxX = Math.max(...xs), minY = Math.min(...ys), maxY = Math.max(...ys);
    const width = Math.max(320, Math.min(680, $("graph").clientWidth - 170));
    const height = Math.max(300, Math.min(520, $("graph").clientHeight - 130));
    for (const point of points) {
      point.x = (point.x - (minX + maxX) / 2) * width / Math.max(1, maxX - minX);
      point.y = (point.y - (minY + maxY) / 2) * height / Math.max(1, maxY - minY);
    }
  }
  return new Map(points.map(point => [point.id, point]));
}
function applyGraphEmphasis(neighbourhood = null) {
  if (!graphNodes || !graphEdges) return;
  graphNodes.update(currentPayload.nodes.map(node => {
    const colors = graphPalette[category(node)], dimmed = neighbourhood && !neighbourhood.has(node.id);
    return { id: node.id, color: { border: dimmed ? "#455263" : colors.border, background: dimmed ? "#1c2736" : colors.background,
      highlight: { border: "#a8bdff", background: "#315efb" }, hover: { border: "#d4e1ff", background: colors.background } },
      font: { color: dimmed ? "#8492a6" : "#e7edf7" }, borderWidth: node.id === selectedNodeId ? 3 : 1.5 };
  }));
  graphEdges.update(currentPayload.edges.map((edge, index) => {
    const emphasized = neighbourhood && neighbourhood.has(edge.from) && neighbourhood.has(edge.to), dimmed = neighbourhood && !emphasized;
    return { id: `e${index}`, color: { color: emphasized ? "#9cbbfa" : dimmed ? "#334154" : "#60738c", highlight: "#b7ccff", hover: "#c4d6ff", inherit: false }, width: emphasized ? 2 : 1.2,
      font: { color: emphasized ? "#d6e2fb" : dimmed ? "#78889e" : "#afbdd0" } };
  }));
}
function fitGraph() {
  if (!network || ($("workspace") && $("workspace").dataset.view === "list")) return;
  network.fit({ animation: false }); network.moveTo({ scale: Math.min(network.getScale() * .92, 1.35), animation: false });
}
function focusNeighborhood() {
  if (!network || !selectedNodeId) return;
  network.fit({ nodes: [...highlightedNodes], animation: false });
  network.moveTo({ scale: Math.min(network.getScale() * .8, 1.35), animation: false }); applyGraphEmphasis(highlightedNodes);
}
function paintGraph() {
  if (network) { network.destroy(); network = null; }
  graphNodes = null; graphEdges = null;
  const enabled = currentPayload.nodes.length > 0 && typeof vis !== "undefined";
  for (const id of ["fit", "zoomIn", "zoomOut", "physics"]) $(id).disabled = !enabled;
  layoutEnabled = false; $("physics").textContent = "Auto-layout: off"; $("physics").setAttribute("aria-pressed", "false");
  if ($("exportGraph")) $("exportGraph").disabled = !hasLoaded;
  if (!currentPayload.nodes.length) { updateSelectionControls(); return; }
  if (typeof vis === "undefined") {
    message("The graph renderer could not load.", "Your data is available in List view. Select an item there to inspect its evidence. Refresh the page to retry the renderer.");
    $("fallback").open = true; setStatus("Graph data loaded. Renderer unavailable; use the node directory.", "error"); updateSelectionControls(); return;
  }
  try {
    const css = getComputedStyle(document.documentElement);
    const fallback = { code: ["#70a5ec", "#243b59"], workflow: ["#e1b363", "#443823"], semantic: ["#71c6b2", "#23423d"] };
    graphPalette = Object.fromEntries(Object.keys(fallback).map(kind => [kind, { border: css.getPropertyValue(`--${kind}`).trim() || fallback[kind][0], background: css.getPropertyValue(`--${kind}-wash`).trim() || fallback[kind][1] }]));
    const positions = graphPositions();
    const nodes = currentPayload.nodes.map(node => {
      const kind = category(node), colors = graphPalette[kind], point = positions.get(node.id), primary = nodeType(node) === "Service";
      return { id: node.id, label: wrapLabel(node.label), x: point.x, y: point.y, shape: kind === "semantic" ? "diamond" : "dot", size: primary ? 22 : kind === "workflow" ? 17 : 15,
        color: { ...colors, highlight: { border: "#a8bdff", background: "#315efb" }, hover: { border: "#d4e1ff", background: colors.background } },
        shapeProperties: { borderDashes: node.factType === "probabilistic" ? [4, 3] : false },
        font: { face: "Segoe UI", size: primary ? 18 : 16, color: "#e7edf7", strokeWidth: 4, strokeColor: "#151d2b", vadjust: 5 },
        borderWidth: 2, borderWidthSelected: 3, shadow: { enabled: primary, color: "rgba(70,125,235,0.14)", size: 18, x: 0, y: 0 } };
    });
    graphNodes = new vis.DataSet(nodes);
    graphEdges = new vis.DataSet(currentPayload.edges.map((edge, index) => ({ id: `e${index}`, from: edge.from, to: edge.to, label: readable(edge.label) })));
    network = new vis.Network($("graph"), { nodes: graphNodes, edges: graphEdges }, {
      autoResize: true, layout: { randomSeed: 42, improvedLayout: false },
      interaction: { hover: true, dragNodes: true, dragView: true, zoomView: true, keyboard: { enabled: true, bindToWindow: false }, tooltipDelay: 250, hoverConnectedEdges: false },
      nodes: { chosen: { label: false } },
      edges: { arrows: { to: { enabled: true, scaleFactor: .65 } }, arrowStrikethrough: false,
        color: { color: "#60738c", highlight: "#b7ccff", hover: "#c4d6ff", inherit: false }, width: 1.3, selectionWidth: 1.4, hoverWidth: .6,
        font: { size: 12, face: "Segoe UI", color: "#afbdd0", strokeWidth: 5, strokeColor: "#151d2b", align: "horizontal", vadjust: -5 },
        smooth: { enabled: true, type: "continuous", roundness: .12 } },
      physics: { enabled: false, stabilization: { iterations: 120 }, barnesHut: { gravitationalConstant: -4500, springLength: 175, springConstant: .025, damping: .3, avoidOverlap: .4 } }
    });
    network.on("click", props => {
      if (props.nodes.length) selectNode(props.nodes[0]);
      else if (props.edges.length) showEdge(currentPayload.edges[Number(props.edges[0].slice(1))]);
      else resetInspector();
    });
    network.on("doubleClick", props => { if (props.nodes.length) { selectNode(props.nodes[0]); focusNeighborhood(); } });
    const canvas = $("graph").querySelector("canvas");
    if (canvas) { canvas.setAttribute("tabindex", "0"); canvas.setAttribute("aria-label", "Interactive context graph. Arrow keys pan, plus and minus zoom. Use List view to inspect items with a keyboard."); }
    fitGraph(); message("", ""); updateSelectionControls();
  } catch (_) {
    if (network) { network.destroy(); network = null; } graphNodes = null; graphEdges = null;
    for (const id of ["fit", "zoomIn", "zoomOut", "physics"]) $(id).disabled = true;
    message("The graph could not be drawn.", "Your data is still available. Open the node directory to inspect the loaded items.");
    $("fallback").open = true; setStatus("Graph data loaded. Drawing failed; use the node directory.", "error"); updateSelectionControls();
  }
}
function renderDirectory() {
  const fragment = document.createDocumentFragment();
  for (const node of currentPayload.nodes) {
    const item = element("li"), button = element("button"); button.type = "button"; button.dataset.nodeId = node.id; button.dataset.category = category(node); button.setAttribute("aria-pressed", "false");
    button.append(element("span", node.label, "directory-node-name"), element("small", `${nodeType(node)} · ${node.factType} · ${percent(node.confidence)}`));
    button.addEventListener("click", () => selectNode(node.id, true)); item.append(button); fragment.append(item);
  }
  $("nodelist").replaceChildren(fragment); $("directorySummary").textContent = `Browse the node directory (${currentPayload.nodes.length}) · Keyboard accessible`;
  if ($("visibleSummary")) $("visibleSummary").textContent = `${currentPayload.nodes.length} nodes · ${currentPayload.edges.length} connections`;
}
function currentParams() { return new URLSearchParams(Object.entries(fields).map(([name, field]) => [name, field.value])); }
function readURL() {
  const params = new URLSearchParams(location.search);
  for (const [name, field] of Object.entries(fields)) {
    const value = params.get(name) || defaults[name];
    if (name === "graph" && value && !Array.from(field.options).some(option => option.value === value)) field.add(new Option(graphNames[value] || value, value));
    field.value = value; if (name !== "search" && field.selectedIndex < 0) field.value = defaults[name];
  }
}
function renderSources() {
  if (!$("sourceList") || !summary) return;
  const fragment = document.createDocumentFragment();
  const entries = [{ id: "", label: "All sources", triples: summary.graphs.reduce((total, graph) => total + graph.triples, 0) }, ...summary.graphs.map(graph => ({ ...graph, label: graphNames[graph.id] || graph.id }))];
  for (const graph of entries) {
    const button = element("button", undefined, "source-button"); button.type = "button"; button.dataset.graphId = graph.id;
    button.setAttribute("aria-pressed", String(fields.graph.value === graph.id)); button.setAttribute("aria-label", `${graph.label}, ${graph.triples} stored triples`); button.title = `${graph.triples} stored RDF triples`;
    button.append(element("span", graph.label, "source-name"), element("span", graph.triples.toLocaleString(), "source-total"));
    button.addEventListener("click", () => { fields.graph.value = graph.id; updateSourceSelection(); loadGraph(); }); fragment.append(button);
  }
  $("sourceList").replaceChildren(fragment); if ($("sourceCount")) $("sourceCount").textContent = summary.graphs.length;
}
function updateSourceSelection() { for (const button of document.querySelectorAll(".source-button[data-graph-id]")) button.setAttribute("aria-pressed", String(button.dataset.graphId === fields.graph.value)); }
function applySummary(metadata) {
  summary = metadata;
  const selected = fields.graph.value; fields.graph.replaceChildren(new Option("All source graphs", ""));
  for (const graph of summary.graphs) fields.graph.add(new Option(`${graphNames[graph.id] || graph.id} (${graph.triples})`, graph.id));
  if (selected && !summary.graphs.some(graph => graph.id === selected)) fields.graph.add(new Option(selected + " (not loaded)", selected));
  fields.graph.value = selected; $("graphCount").textContent = summary.graphs.length;
  $("connection").textContent = summary.mode === "demo" ? "Demo fixtures · Local store" : "Local graph store"; $("connection").dataset.state = "ready";
  $("dataScope").textContent = `${summary.mode === "demo" ? "Demo data: curated test fixtures." : "Local data: loaded Turtle files."} Source: ${summary.source}. Stored facts only; runtime agent monitoring and automatic remediation are not connected.`;
  renderSources();
}
async function loadGraph(saveURL = true) {
  if (request) request.abort();
  const controller = new AbortController(); request = controller;
  const timeout = setTimeout(() => controller.abort(), 15000), params = currentParams();
  if (saveURL) {
    const visible = new URLSearchParams();
    for (const [name, value] of params) if (value !== defaults[name]) visible.set(name, value);
    const url = location.pathname + (visible.size ? "?" + visible : "") + location.hash;
    if (url !== location.pathname + location.search + location.hash) history.pushState(null, "", url);
  }
  updateSourceSelection();
  $("reload").disabled = true; $("reload").setAttribute("aria-busy", "true"); $("reload").textContent = "Loading…";
  $("graph").setAttribute("aria-busy", "true");
  setStatus(currentPayload.nodes.length ? "Updating… The previous graph remains visible." : "Loading nodes and relationships…", "loading");
  if (!currentPayload.nodes.length) message("Loading the context graph…", "Reading nodes and relationships from the local store.");
  try {
    // Commit metadata only after the active payload succeeds. Cancelled or
    // superseded responses must not mutate visible source navigation.
    const [payload, metadata] = await Promise.allSettled([getJSON("/graph/nodes?" + params, controller.signal), getJSON("/graph/summary", controller.signal)]);
    if (request !== controller) return;
    if (payload.status !== "fulfilled") throw payload.reason;
    if (!Array.isArray(payload.value.nodes) || !Array.isArray(payload.value.edges)) throw new Error("Invalid graph response");
    resetInspector(); currentPayload = payload.value; displayedParams = new URLSearchParams(params);
    const firstLoad = !hasLoaded; hasLoaded = true;
    if (metadata.status === "fulfilled" && Array.isArray(metadata.value.graphs)) applySummary(metadata.value);
    $("nodeCount").textContent = currentPayload.nodes.length; $("edgeCount").textContent = currentPayload.edges.length;
    $("inferredCount").textContent = currentPayload.nodes.filter(node => node.factType === "probabilistic").length;
    renderDirectory(); setStatus(`${currentPayload.nodes.length} nodes · ${currentPayload.edges.length} relationships${!currentPayload.edges.length && currentPayload.nodes.length ? " · No connections within these filters" : ""}`); paintGraph();
    const filtered = [...params].some(([name, value]) => value !== defaults[name]);
    if (!currentPayload.nodes.length) message(filtered ? "No nodes match these filters." : "The graph store is empty.", fields.search.value ? `No visible item matches “${fields.search.value}”. Reset filters to explore the full graph.` : filtered ? "Reset filters to see all available nodes." : "Start the server with --demo to explore the sample, or load extracted Turtle files into the local store.");
    if (metadata.status !== "fulfilled" || !Array.isArray(metadata.value.graphs)) {
      $("connection").textContent = "Graph loaded · Source details unavailable"; $("connection").dataset.state = "error";
      $("dataScope").textContent = "Graph data is available, but source details could not load. Apply filters to retry. This dashboard does not monitor running agents.";
    }
    $("updated").textContent = `Loaded ${new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`;
    // Useful first impression without moving the viewport or keyboard focus.
    if (firstLoad && currentPayload.nodes.length) {
      const initial = currentPayload.nodes.find(node => node.label === "findOrders") || currentPayload.nodes.find(node => connectedEdges(node.id).length && nodeType(node) === "Service") || currentPayload.nodes.find(node => connectedEdges(node.id).length) || currentPayload.nodes[0];
      selectNode(initial.id, false, false);
    }
  } catch (_) {
    if (request !== controller) return;
    $("connection").textContent = "Connection unavailable"; $("connection").dataset.state = "error";
    const reason = location.protocol === "file:" ? "Open the served page at http://127.0.0.1:8000/dashboard after starting the server." : "Check that the local server is still running, then retry.";
    setStatus(`${currentPayload.nodes.length ? "Refresh failed. Showing the previous graph; filters have not been applied. " : "Could not load graph data. "}${reason}`, "error");
    message(currentPayload.nodes.length ? "Refresh failed. Previous graph retained." : "Could not load the context graph.", reason, true);
    $("dataScope").textContent = "Source details could not be refreshed. Any graph still visible is from the previous successful load. This dashboard does not monitor running agents.";
  } finally {
    clearTimeout(timeout);
    if (request === controller) {
      $("reload").disabled = false; $("reload").removeAttribute("aria-busy"); $("reload").textContent = "Apply filters"; $("graph").setAttribute("aria-busy", "false");
    }
  }
}
function switchView(view) {
  if (!$("workspace")) return;
  $("workspace").dataset.view = view;
  if ($("viewGraph")) $("viewGraph").setAttribute("aria-pressed", String(view === "graph"));
  if ($("viewList")) $("viewList").setAttribute("aria-pressed", String(view === "list"));
  $("fallback").open = view === "list";
  if (view === "graph") requestAnimationFrame(() => { if (network) { network.redraw(); fitGraph(); } });
}
function exportGraph() {
  if (!hasLoaded) return;
  const output = { exportedAt: new Date().toISOString(), filters: Object.fromEntries(displayedParams), ...currentPayload };
  const url = URL.createObjectURL(new Blob([JSON.stringify(output, null, 2)], { type: "application/json" }));
  const link = element("a"); link.href = url; link.download = "context-atlas-graph.json";
  document.body.append(link); link.click(); link.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  setStatus(`Exported ${currentPayload.nodes.length} visible nodes and ${currentPayload.edges.length} relationships as JSON.`);
}
$("filters").addEventListener("submit", event => { event.preventDefault(); loadGraph(); });
for (const field of [fields.confidence, fields.factType, fields.graph]) field.addEventListener("change", () => loadGraph());
$("reset").addEventListener("click", () => { for (const [name, field] of Object.entries(fields)) field.value = defaults[name]; loadGraph(); });
$("retry").addEventListener("click", () => loadGraph());
$("fit").addEventListener("click", fitGraph);
$("zoomIn").addEventListener("click", () => network && network.moveTo({ scale: Math.min(network.getScale() * 1.3, 3), animation: false }));
$("zoomOut").addEventListener("click", () => network && network.moveTo({ scale: Math.max(network.getScale() / 1.3, .05), animation: false }));
$("physics").addEventListener("click", () => {
  if (!network) return;
  layoutEnabled = !layoutEnabled; network.setOptions({ physics: { enabled: layoutEnabled } });
  $("physics").textContent = `Auto-layout: ${layoutEnabled ? "on" : "off"}`; $("physics").setAttribute("aria-pressed", String(layoutEnabled));
});
if ($("focusSelection")) $("focusSelection").addEventListener("click", () => {
  switchView("graph");
  requestAnimationFrame(() => { focusNeighborhood(); revealOnMobile($("graph")); });
});
if ($("clearSelection")) $("clearSelection").addEventListener("click", resetInspector);
if ($("exportGraph")) { $("exportGraph").disabled = true; $("exportGraph").addEventListener("click", exportGraph); }
if ($("viewGraph")) $("viewGraph").addEventListener("click", () => switchView("graph"));
if ($("viewList")) $("viewList").addEventListener("click", () => switchView("list"));
for (const link of document.querySelectorAll(".rail-nav a, .rail-link")) link.addEventListener("click", () => {
  for (const other of document.querySelectorAll(".rail-nav a, .rail-link")) other.removeAttribute("aria-current");
  link.setAttribute("aria-current", "location");
});
for (const link of document.querySelectorAll('a[href="#help"], a[href="#workflow"]')) link.addEventListener("click", () => {
  const target = $(link.getAttribute("href").slice(1));
  if (target instanceof HTMLDetailsElement) target.open = true;
});
document.addEventListener("keydown", event => {
  if (event.ctrlKey || event.metaKey || event.altKey || event.defaultPrevented) return;
  const target = event.target, editing = target instanceof Element && (target.closest("input,textarea,select") || target.isContentEditable);
  if (event.key === "/" && !editing) { event.preventDefault(); fields.search.focus(); }
  if (event.key === "Escape" && !editing) { event.preventDefault(); resetInspector(); }
});
if ($("advancedFilters")) {
  const compactFilters = matchMedia("(max-width: 700px)");
  const syncAdvancedFilters = () => { $("advancedFilters").open = !compactFilters.matches; };
  syncAdvancedFilters();
  compactFilters.addEventListener("change", syncAdvancedFilters);
}
window.addEventListener("popstate", () => { readURL(); loadGraph(false); });
window.addEventListener("resize", () => { clearTimeout(resizeTimer); resizeTimer = setTimeout(fitGraph, 150); });
readURL();
loadGraph(false);

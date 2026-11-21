const FR = new Intl.NumberFormat("fr-FR", { maximumFractionDigits: 3 });
const palette = ["#19634f", "#ab4d23", "#365b99", "#614870"];

function element(tag, value = "") {
  const node = document.createElement(tag);
  node.textContent = value;
  return node;
}

function format(value) {
  return typeof value === "number" ? FR.format(Math.abs(value) < 0.0005 ? 0 : value) : String(value ?? "");
}

function table(block) {
  const wrap = element("div");
  wrap.className = "table-region";
  wrap.tabIndex = 0;
  wrap.setAttribute("role", "region");
  wrap.setAttribute("aria-label", block.titre);
  const grid = element("table");
  grid.createCaption().textContent = block.titre;
  const row = grid.createTHead().insertRow();
  block.colonnes.forEach(colonne => {
    const header = element("th", colonne);
    header.scope = "col";
    row.append(header);
  });
  const body = grid.createTBody();
  block.lignes.forEach(values => {
    const row = body.insertRow();
    values.forEach((value, i) => {
      if (i === 0) {
        const label = element("th", format(value));
        label.scope = "row";
        row.append(label);
      } else {
        row.insertCell().textContent = format(value);
      }
    });
  });
  wrap.append(grid);
  return wrap;
}

function chart(block) {
  const width = 680, height = 290;
  const left = 72, top = 20, plotWidth = 590, plotHeight = 210;
  const values = block.series.flatMap(series => series.valeurs);
  const min = Math.min(0, ...values);
  const max = Math.max(0, ...values);
  const range = max - min || 1;
  const y = value => top + plotHeight * (1 - (value - min) / range);
  const categoryWidth = plotWidth / block.categories.length;
  const x = index => left + categoryWidth * (index + 0.5);
  const barWidth = Math.min(35, categoryWidth * 0.75 / block.series.length);

  const figure = element("figure");
  figure.className = "lab-figure";
  const caption = element("figcaption", block.titre + " (" + block.unite + ")");
  const wrap = element("div");
  wrap.className = "lab-chart";
  wrap.tabIndex = 0;
  const svgNS = "http://www.w3.org/2000/svg";
  const svg = document.createElementNS(svgNS, "svg");
  svg.setAttribute("viewBox", "0 0 " + width + " " + height);
  svg.setAttribute("role", "img");
  svg.setAttribute("aria-label", caption.textContent + ". Données accessibles dans le tableau sous le graphique.");
  function draw(tag, attrs, label) {
    const node = document.createElementNS(svgNS, tag);
    Object.entries(attrs).forEach(([key, value]) => node.setAttribute(key, value));
    if (label !== undefined) node.textContent = label;
    svg.append(node);
    return node;
  }

  for (let i = 0; i <= 4; i++) {
    const tick = min + range * i / 4;
    draw("line", { x1: left, x2: left + plotWidth, y1: y(tick), y2: y(tick), stroke: "#d8e4dd" });
    draw("text", { x: left - 8, y: y(tick) + 4, "text-anchor": "end" }, format(tick));
  }
  draw("line", { x1: left, x2: left + plotWidth, y1: y(0), y2: y(0), stroke: "#567164" });
  block.categories.forEach((category, index) =>
    draw("text", { x: x(index), y: top + plotHeight + 24, "text-anchor": "middle" }, category)
  );

  const legend = element("ul");
  legend.className = "lab-legend";
  block.series.forEach((series, j) => {
    const color = palette[j % palette.length];
    if (block.type === "barres") {
      series.valeurs.forEach((value, i) => draw("rect", {
        x: x(i) + (j - block.series.length / 2) * barWidth + 1,
        y: Math.min(y(value), y(0)), width: barWidth - 2,
        height: Math.abs(y(0) - y(value)), rx: 2, fill: color
      }));
    } else {
      const path = series.valeurs.map((value, i) => x(i) + "," + y(value)).join(" ");
      draw("polyline", { points: path, fill: "none", stroke: color, "stroke-width": 2.8,
        "stroke-dasharray": j === block.series.length - 1 && block.series.length > 1 ? "6 4" : "none" });
      series.valeurs.forEach((value, i) =>
        draw("circle", { cx: x(i), cy: y(value), r: 3.4, fill: color })
      );
    }
    const item = element("li");
    const swatch = element("span");
    swatch.style.backgroundColor = color;
    swatch.setAttribute("aria-hidden", "true");
    item.append(swatch, document.createTextNode(series.nom));
    legend.append(item);
  });

  const data = element("details");
  data.append(element("summary", "Afficher les données du graphique"), table({
    titre: block.titre + " • " + block.unite,
    colonnes: ["Point", ...block.series.map(series => series.nom)],
    lignes: block.categories.map((category, i) => [category, ...block.series.map(series => series.valeurs[i])])
  }));
  wrap.append(svg);
  figure.append(caption, wrap, legend, data);
  return figure;
}

for (const lab of document.querySelectorAll("[data-python-lab]")) {
  const code = lab.querySelector("textarea");
  const run = lab.querySelector("[data-run]");
  const reset = lab.querySelector("[data-reset]");
  const stop = lab.querySelector("[data-stop]");
  const status = lab.querySelector("[role=status]");
  const results = lab.querySelector("[data-results]");
  let original, worker, timeout;

  function idle() {
    clearTimeout(timeout);
    run.disabled = false;
    stop.hidden = true;
  }

  function end(message) {
    worker?.terminate();
    worker = undefined;
    idle();
    status.textContent = message;
  }

  async function loadCode() {
    if (original !== undefined) return;
    const response = await fetch(lab.dataset.pythonLab);
    if (!response.ok) throw new Error("Le fichier Python n’est pas disponible.");
    original = await response.text();
    code.value = original;
    code.disabled = false;
    run.disabled = false;
    reset.disabled = false;
    status.textContent = "Prêt à exécuter.";
  }

  reset.addEventListener("click", () => {
    code.value = original;
    status.textContent = "Code initial restauré. Exécutez-le pour actualiser les sorties.";
  });
  stop.addEventListener("click", () => end("Exécution interrompue. Vous pouvez modifier le code et relancer."));
  run.addEventListener("click", () => {
    run.disabled = true;
    stop.hidden = false;
    status.textContent = worker ? "Calcul en cours…" : "Chargement de Python au premier lancement…";
    worker ??= new Worker(new URL("./python-worker.js", import.meta.url));
    worker.onerror = () => end("Python n’a pas pu démarrer. Réessayez ou utilisez les fichiers .py téléchargeables.");
    worker.onmessage = ({ data }) => {
      if (data.type === "ready") {
        status.textContent = "Calcul en cours…";
        return;
      }
      idle();
      results.replaceChildren();
      if (data.type === "error") {
        status.textContent = "Le programme a renvoyé une erreur.";
        results.append(element("pre", data.message));
        // Une erreur au chargement doit pouvoir être retentée avec un processus neuf.
        worker.terminate();
        worker = undefined;
      } else {
        const { tableaux, graphiques, commentaires } = data.resultat;
        results.append(...(tableaux || []).map(table), ...(graphiques || []).map(chart));
        if (commentaires?.length) {
          const note = element("div");
          note.className = "lab-comments";
          note.append(element("h4", "Interprétation des résultats"), ...commentaires.map(comment => element("p", comment)));
          results.append(note);
        }
        status.textContent = "Calcul terminé. Les tableaux et graphiques sont à jour.";
      }
      if (data.journal?.length) {
        const log = element("details");
        log.append(element("summary", "Afficher la console Python"), element("pre", data.journal.join("\n")));
        results.append(log);
      }
    };
    timeout = setTimeout(() => end("Délai dépassé. Réessayez ou réduisez la durée du calcul."), 90000);
    worker.postMessage({ code: code.value });
  });

  const prepare = lab.closest("details");
  if (prepare) {
    prepare.addEventListener("toggle", async () => {
      if (!prepare.open) return;
      try { await loadCode(); } catch (error) { status.textContent = error.message; }
    });
  } else {
    loadCode().catch(error => { status.textContent = error.message; });
  }
}

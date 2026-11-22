const runtimeURL = "https://cdn.jsdelivr.net/pyodide/v0.27.7/full/";
let runtime;

async function init() {
  importScripts(runtimeURL + "pyodide.js");
  const python = await loadPyodide({ indexURL: runtimeURL });
  const modelURL = new URL("../python/modele.py?v=pdf-aer-1", self.location.href);
  const response = await fetch(modelURL);
  if (!response.ok) throw new Error("Le modèle Python du cours ne se charge pas.");
  python.FS.writeFile("modele.py", await response.text());
  return python;
}

self.onmessage = async ({ data }) => {
  let namespace;
  const journal = [];
  try {
    runtime ??= init();
    const python = await runtime;
    self.postMessage({ type: "ready" });
    const output = { batched: line => journal.push(line) };
    python.setStdout(output);
    python.setStderr(output);
    namespace = python.toPy({ __name__: "__atelier__" });
    await python.runPythonAsync(data.code, { globals: namespace });
    const resultat = python.runPython(
      "__import__('json').dumps(RESULTATS, ensure_ascii=False, allow_nan=False)",
      { globals: namespace }
    );
    self.postMessage({ type: "result", resultat: JSON.parse(resultat), journal });
    try {
      await python.loadPackage("matplotlib");
      const encoded = python.runPython(`
from base64 import b64encode
from io import BytesIO
from modele import exporter_pdf
with BytesIO() as pdf:
    exporter_pdf(RESULTATS, pdf)
    pdf_base64 = b64encode(pdf.getvalue()).decode("ascii")
pdf_base64
`, { globals: namespace });
      const bytes = Uint8Array.from(atob(encoded), c => c.charCodeAt(0));
      self.postMessage({ type: "pdf", bytes }, [bytes.buffer]);
    } catch (error) {
      self.postMessage({ type: "pdf-error", message: String(error.message || error) });
    }
  } catch (error) {
    self.postMessage({ type: "error", message: String(error.message || error), journal });
  } finally {
    namespace?.destroy();
  }
};

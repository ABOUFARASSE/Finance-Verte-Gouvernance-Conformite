const runtimeURL = "https://cdn.jsdelivr.net/pyodide/v0.27.7/full/";
let runtime;

async function init() {
  importScripts(runtimeURL + "pyodide.js");
  const python = await loadPyodide({ indexURL: runtimeURL });
  const modelURL = new URL("../python/modele.py", self.location.href);
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
  } catch (error) {
    self.postMessage({ type: "error", message: String(error.message || error), journal });
  } finally {
    namespace?.destroy();
  }
};

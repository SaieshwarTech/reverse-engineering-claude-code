#!/usr/bin/env node
// postinstall: pip-install the Python package that the JS bins wrap.
"use strict";
const { spawnSync } = require("child_process");

function python() {
  for (const p of ["python3", "python"]) {
    if (spawnSync(p, ["--version"], { stdio: "ignore" }).status === 0) return p;
  }
  return null;
}

const py = python();
if (!py) {
  console.warn("[recc-cli] Python 3.9+ not found. Install it, then run:\n" +
               "  pip install recc-cli");
  process.exit(0); // don't fail the npm install
}
console.log("[recc-cli] installing the Python package (recc-cli) via pip…");
const r = spawnSync(py, ["-m", "pip", "install", "--user", "recc-cli"],
  { stdio: "inherit" });
if (r.status !== 0) {
  console.warn("[recc-cli] pip install did not complete. Run it manually:\n" +
               "  pip install recc-cli");
}
process.exit(0);

#!/usr/bin/env node
// Thin launcher: dispatch `recc*` npm bins to the Python package that does the work.
// The command name (recc, recc-agent, recc-bridge, recc-mail, recc-whatsapp) maps
// to a module in recc_cli; we invoke it via Python.
"use strict";
const { spawnSync } = require("child_process");
const path = require("path");

const MODULES = {
  "recc": "recc_cli.inspector",
  "recc-agent": "recc_cli.agent",
  "recc-bridge": "recc_cli.bridge",
  "recc-mail": "recc_cli.email_channel",
  "recc-whatsapp": "recc_cli.whatsapp",
};

function python() {
  for (const p of ["python3", "python"]) {
    const r = spawnSync(p, ["--version"], { stdio: "ignore" });
    if (r.status === 0) return p;
  }
  console.error("recc-cli needs Python 3.9+ on PATH. Install from https://python.org");
  process.exit(1);
}

const invoked = path.basename(process.argv[1] || "recc").replace(/\.js$/, "");
const mod = MODULES[invoked] || "recc_cli.agent";
const py = python();
const res = spawnSync(py, ["-m", mod, ...process.argv.slice(2)], { stdio: "inherit" });
process.exit(res.status === null ? 1 : res.status);

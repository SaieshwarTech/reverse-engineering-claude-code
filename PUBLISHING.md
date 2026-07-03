# Publishing recc-cli

Name-availability check (2026-07-03): **`recc-cli` is free on both PyPI and npm.**
`recc` (bare) is taken on both, which is why the package name is `recc-cli` while the
installed *commands* stay short (`recc`, `recc-agent`, `recc-bridge`, `recc-mail`,
`recc-whatsapp` — set via `[project.scripts]` in `pyproject.toml`).

Publishing requires **your own PyPI and npm accounts** — an agent cannot create accounts
or hold your credentials, so these steps are for you (or CI configured with your tokens)
to run.

## 1. PyPI

Already verified locally: `python3 -m build` succeeds and `twine check dist/*` passes.

```bash
python3 -m pip install --upgrade build twine
rm -rf dist build *.egg-info
python3 -m build
twine check dist/*                 # sanity check before uploading

# create an account at https://pypi.org/account/register/ if you don't have one,
# then get an API token at https://pypi.org/manage/account/token/
twine upload dist/*                # prompts for token (username: __token__)
```

After this, `pip install recc-cli` works for anyone.

**Recommended: automate it.** Add a `.github/workflows/publish-pypi.yml` that runs on
GitHub Release and uses [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/)
(no stored token needed) — ask me to add this workflow when you're ready.

## 2. npm

The npm package (`npm/`) is a thin wrapper: its `postinstall` pip-installs `recc-cli` from
PyPI, so **publish npm after PyPI**, not before, or the postinstall will fail for users.

```bash
cd npm
npm login                          # your npm account
npm publish --access public
```

After this, `npm install -g recc-cli` works (and pulls in the Python package via pip).

## 3. Verify end-to-end (after both are live)

```bash
python3 -m venv /tmp/v && /tmp/v/bin/pip install recc-cli
/tmp/v/bin/recc-agent --help && /tmp/v/bin/recc --help
npm install -g recc-cli && recc --help
```

## 4. Update the README

Once both are live, change the README's pip/npm lines from "from source" /
"once published" to the direct commands, and close the tracking issue.

## Version bumps

Bump `version` in both `pyproject.toml` and `npm/package.json` together (keep them in
sync) before each release; then repeat steps 1–2.

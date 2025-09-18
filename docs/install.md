## Install Dana v0.5

Use the public v0.5 artifacts.

<Tip>
Need OS setup or from-source development? See Tech Setup.
</Tip>

### macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install dana
dana --version
```

<Check>
If installation succeeds, you should see a version like `Dana 0.5` or higher.
</Check>

### Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install dana
dana --version
```

### Launch Dana Agent Studio

```bash
dana studio
```

<Tip>
If `dana` is not on your PATH, run it via `python -m dana`.
</Tip>



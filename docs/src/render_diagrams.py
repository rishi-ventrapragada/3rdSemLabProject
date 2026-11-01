"""
Renders every docs/src/diagrams/*.puml to docs/src/figures/diagrams/*.png with PlantUML.

PlantUML (pinned below) is downloaded into docs/src/tools/ (git-ignored) on first use and checked
against Maven Central's SHA-1. Its built-in Smetana layout is used, so Graphviz is not needed.
Run from the repo root:  .venv\\Scripts\\python.exe docs\\src\\render_diagrams.py
"""

import hashlib
import subprocess
import sys
import urllib.request
from pathlib import Path

VERSION = "1.2026.9"
SRC = Path(__file__).resolve().parent
JAR = SRC / "tools" / f"plantuml-{VERSION}.jar"
URL = f"https://repo1.maven.org/maven2/net/sourceforge/plantuml/plantuml/{VERSION}/plantuml-{VERSION}.jar"
OUT = SRC / "figures" / "diagrams"


def ensure_jar():
    if JAR.is_file():
        return
    JAR.parent.mkdir(parents=True, exist_ok=True)
    data = urllib.request.urlopen(URL, timeout=120).read()
    expected = urllib.request.urlopen(URL + ".sha1", timeout=60).read().decode().split()[0]
    if hashlib.sha1(data).hexdigest() != expected:
        sys.exit("PlantUML download failed its SHA-1 check")
    JAR.write_bytes(data)


if __name__ == "__main__":
    ensure_jar()
    OUT.mkdir(parents=True, exist_ok=True)
    sources = sorted((SRC / "diagrams").glob("d*.puml"))
    proc = subprocess.run(["java", "-jar", str(JAR), "-tpng", "-charset", "UTF-8", "-o", str(OUT),
                           *map(str, sources)], capture_output=True, text=True)
    print(proc.stdout + proc.stderr)
    missing = [s.stem for s in sources if not (OUT / f"{s.stem}.png").is_file()]
    print(f"{len(sources) - len(missing)}/{len(sources)} diagrams rendered", f"missing: {missing}" if missing else "")
    sys.exit(1 if proc.returncode or missing else 0)

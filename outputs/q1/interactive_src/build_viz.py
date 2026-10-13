import json, sys
from pathlib import Path
here = Path(__file__).parent
data = (here / "viz_data.json").read_text(encoding="utf-8")
html = (here / "viz_template.html").read_text(encoding="utf-8").replace("__DATA__", data)
out = Path(sys.argv[1]); out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(html, encoding="utf-8"); print("wrote", out, round(len(html) / 1024), "KB")

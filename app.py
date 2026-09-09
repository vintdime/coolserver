from flask import Flask, render_template, url_for
from pathlib import Path
import markdown

app = Flask(__name__)

CONTENT_DIR = Path(__file__).parent / "content"

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/Browse/")
@app.route("/Browse/<path:filepath>")
def Browse(filepath=""):

    current_path = (CONTENT_DIR / filepath).resolve()

    if CONTENT_DIR not in current_path.parents and current_path != CONTENT_DIR:
        abort(404)

    if current_path.is_file():

        if current_path.suffix.lower() != ".md":
            abort(404)

        markdown_text = current_path.read_text(encoding="utf-8")

        html = markdown.markdown(
            markdown_text,
            extensions=["fenced_code", "tables", "toc"]
        )

        return render_template(
            "note.html",
            content=html
        )

    if current_path.is_dir():

        items = []

        for item in sorted(current_path.iterdir()):

            if item.is_dir():
                items.append({
                    "name": item.name,
                    "type": "folder"
                })

            elif item.is_file() and item.suffix.lower() == ".md":
                items.append({
                    "name": item.stem,
                    "type": "file"
                })

        return render_template(
            "browse.html",
            items=items,
            current_path=filepath
        )


if __name__ == "__main__":
    app.run(debug=True)
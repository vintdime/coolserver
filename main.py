from flask import Flask, render_template, abort
from pathlib import Path
import markdown
import re
import tempfile
from lzstring import LZString
from excalidraw_render.render import load_scene, render_svg

app = Flask(__name__)

CONTENT_DIR = Path(__file__).parent / "content"


def find_content_file(filename):
    matches = list(CONTENT_DIR.rglob(filename))

    if matches:
        return matches[0]

    matches = list(CONTENT_DIR.rglob(filename + ".md"))

    return matches[0] if matches else None


def render_excalidraw(file_path):
    text = file_path.read_text(encoding="utf-8")

    match = re.search(
        r"```compressed-json\s*(.*?)\s*```",
        text,
        re.DOTALL
    )

    if not match:
        raise ValueError("No compressed-json block found")

    compressed_data = match.group(1).replace("\n", "").replace("\r", "")

    json_text = LZString().decompressFromBase64(compressed_data)

    if not json_text:
        raise ValueError("LZString decompression returned nothing")

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".excalidraw",
        encoding="utf-8",
        delete=False
    ) as temp:
        temp.write(json_text)
        temp_path = temp.name

    try:
        scene = load_scene(temp_path)
        return render_svg(scene)
    finally:
        Path(temp_path).unlink(missing_ok=True)


def process_excalidraw(text):
    pattern = r'!\[\[([^\]]+\.excalidraw)\]\]'

    def replace(match):
        filename = match.group(1)

        file_path = find_content_file(filename)

        if file_path is None:
            return match.group(0)

        try:
            svg = render_excalidraw(file_path)

            return f'<div class="excalidraw-container">{svg}</div>'

        except Exception as e:
            print(f"Excalidraw error for {file_path}: {e}")
            return f'<p>Excalidraw error: {e}</p>'

    return re.sub(pattern, replace, text)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/Browse/")
@app.route("/Browse/<path:filepath>")
def Browse(filepath=""):
    current_path = (CONTENT_DIR / filepath).resolve()

    if any(
        part.startswith(".")
        for part in current_path.relative_to(CONTENT_DIR).parts
    ):
        abort(404)

    if CONTENT_DIR not in current_path.parents and current_path != CONTENT_DIR:
        abort(404)

    # Normal Markdown note
    if current_path.is_file():

        # Excalidraw files should be rendered by the Excalidraw renderer
        if current_path.name.endswith(".excalidraw.md"):
            svg = render_excalidraw(current_path)

            title = current_path.name.removesuffix(".excalidraw.md")

            return render_template(
                "directview.html",
                content=svg,
                title=title
            )

        # Regular Markdown
        if current_path.suffix.lower() != ".md":
            abort(404)

        markdown_text = current_path.read_text(encoding="utf-8")

        markdown_text = process_excalidraw(markdown_text)

        html = markdown.markdown(
            markdown_text,
            extensions=[
                "fenced_code",
                "tables",
                "toc"
            ]
        )

        return render_template(
            "note.html",
            content=html
        )

    # Directory
    if current_path.is_dir():

        items = []

        for item in sorted(current_path.iterdir()):

            if item.name.startswith("."):
                continue

            if item.is_dir():
                items.append({
                    "name": item.name,
                    "type": "folder"
                })

            elif item.is_file():

                # Don't expose the .md extension of Excalidraw files
                if item.name.endswith(".excalidraw.md"):
                    items.append({
                        "name": item.name.removesuffix(".md"),
                        "type": "file"
                    })

                elif item.suffix.lower() == ".md":
                    items.append({
                        "name": item.stem,
                        "type": "file"
                    })

        return render_template(
            "browse.html",
            items=items,
            current_path=filepath
        )

    abort(404)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000)
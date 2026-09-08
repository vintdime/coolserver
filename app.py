from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
import httpx


app = FastAPI()

templates = Jinja2Templates(directory="templates")

GITHUB_API = "https://api.github.com/repos/vintdime/mykpklectures/contents"


def get_repo_contents():
    response = httpx.get(GITHUB_API)
    response.raise_for_status()

    return response.json()


@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )

if __name__ == "__main__":
    items = get_repo_contents()

    for item in items:
        print(item["type"], item["name"])
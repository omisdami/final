import uvicorn

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)




from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

from api.templates_api import router as templates_router

# Initialize FastAPI app
app = FastAPI()

# Static and template folders
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Include template API
app.include_router(templates_router)

# Home route
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Template editor route
@app.get("/template-editor", response_class=HTMLResponse)
def template_editor(request: Request):
    return templates.TemplateResponse("template-editor.html", {"request": request})


# ✅ This block lets you use `python run.py`
if __name__ == "__main__":
    uvicorn.run("run:app", host="127.0.0.1", port=8000, reload=True)

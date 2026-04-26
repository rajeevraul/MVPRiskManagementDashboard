from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def home():
    return {
        "message": "Finalto Risk Dashboard Backend Running"
    }
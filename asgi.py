from app.main import create_app
app = create_app()

@app.get("/")
def main():
    return {"message": "Hello World"}

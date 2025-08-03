from fastapi import FastAPI
from src.components.auth.routes import router as auth_router

app = FastAPI(title="K-Backend", version="1.0.0")

app.include_router(auth_router)

@app.get("/")
async def hello_world():
    return {"message": "Hello World!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)


    # explore:  https://claude.ai/share/d00d3893-7511-4c29-87a8-a3b78419fddb 
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from model import recommend

app = FastAPI(title="AI志愿推荐系统")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/recommend")
def api(data: dict):
    score = data.get("score", 0)
    province = data.get("province", "湖北省")
    result = recommend(score, province)
    return {"result": result, "score": score, "province": province}


@app.get("/health")
def health():
    return {"status": "ok"}

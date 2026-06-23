from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import httpx
import json

app = FastAPI(title="AI 志愿系统 API (真实 AI 驱动)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class StudentProfile(BaseModel):
    score: int
    rank: Optional[int] = None
    province: str = "广东"
    subject_type: str = "物理"

# 配置你的大模型 API 密钥和地址（可根据需要修改为 OpenRouter 或 智介 API）
API_KEY = "YOUR_API_KEY_HERE"
BASE_URL = "https://api.openai.com/v1" # 或 https://openrouter.ai/api/v1 等

@app.post("/api/v1/recommend")
async def get_recommendations(student: StudentProfile):
    # 构建发给 AI 的提示词（Prompt）
    prompt = f"用户高考分数：{student.score}分，省份：{student.province}，选科：{student.subject_type}。请根据这些信息，推荐3所适合的大学，并给出专业和录取概率（冲刺/稳妥/保底）。请严格以 JSON 数组格式返回，不要包含任何多余的解释文本。格式形如：[{{\"university\": \"学校名\", \"major\": \"专业名\", \"probability\": \"冲刺\", \"min_rank\": 1000}}]"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-3.5-turbo", # 或者是 claude-3 等你想用的模型
                    "messages": [
                        {"role": "system", "content": "你是一个高考志愿规划专家。你只能返回结构化的 JSON 数据。"},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7
                },
                timeout=30.0
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail=f"AI 服务侧响应错误: {response.text}")
                
            res_json = response.json()
            ai_content = res_json["choices"][0]["message"]["content"].strip()
            
            # 解析 AI 返回的 JSON 字符串
            recommend_data = json.loads(ai_content)
            
            return {
                "status": "success",
                "meta": {
                    "score": student.score,
                    "province": student.province
                },
                "data": recommend_data
            }
            
    except json.JSONDecodeError:
        # 如果大模型没有老老实实返回 JSON 格式，做个兜底，防止前端崩溃
        return {
            "status": "success",
            "meta": {"score": student.score, "province": student.province},
            "data": [
                {"university": "由于AI格式未能解析，暂提供兜底推荐：中山大学", "major": "软件工程", "probability": "稳妥", "min_rank": 2000}
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"网络或系统异常: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)

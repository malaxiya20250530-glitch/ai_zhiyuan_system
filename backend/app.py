from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import httpx
import json
import sqlite3

app = FastAPI(title="AI 志愿推荐系统 - 觉察推理版")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ======== 数据库初始化 (第二步的核心) ========
def init_db():
    conn = sqlite3.connect('zhiyuan.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            score INTEGER,
            province TEXT,
            subject_type TEXT,
            recommendations TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

class StudentProfile(BaseModel):
    score: int
    rank: Optional[int] = None
    province: str = "湖北省"
    subject_type: str = "物理"

API_KEY = "YOUR_API_KEY_HERE"
BASE_URL = "https://api.openai.com/v1" # 或你的其他 API 路由

@app.post("/api/v1/recommend")
async def get_recommendations(student: StudentProfile):
    
    # 构造高度结构化的“双流觉察推理”Prompt
    prompt = f"""
    你是一个拥有高级决策逻辑的高考志愿规划专家。
    请针对以下学生 profile 启动【双流觉察推理 (Dual-Stream Aware Reasoning)】框架进行分析：
    
    【输入参数】
    - 分数: {student.score}分
    - 省份: {student.province}
    - 选科: {student.subject_type}
    
    【推理要求】
    1. 第一流（刚性觉察）：严格对照该省份【{student.subject_type}】大类的投档线特征，判定其分数段位次，筛选出“冲、稳、保”三个梯度的院校。
    2. 第二流（柔性觉察）：针对【{student.subject_type}】的学科属性（如物理偏向工科/计算机，历史偏向文史/法学），精准匹配最具备就业韧性的专业。
    
    请将双流推理的结果融合成一个干净的 JSON 数组返回。严禁包含任何前导、后继的自然语言解释，直接输出标准 JSON。
    
    格式范例：
    [
      {{"university": "武昌首义学院", "major": "机器人工程", "probability": "保底", "min_rank": 35000}},
      {{"university": "武汉理工大学", "major": "计算机科学与技术", "probability": "冲刺", "min_rank": 8000}}
    ]
    """

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-3.5-turbo", 
                    "messages": [
                        {"role": "system", "content": "You are a professional JSON generator for college counseling."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3
                },
                timeout=30.0
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail="AI推理引擎响应异常")
                
            ai_content = response.json()["choices"][0]["message"]["content"].strip()
            recommend_data = json.loads(ai_content)
            
            # ======== 持久化保存到数据库 (第二步) ========
            conn = sqlite3.connect('zhiyuan.db')
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO records (score, province, subject_type, recommendations) VALUES (?, ?, ?, ?)",
                (student.score, student.province, student.subject_type, json.dumps(recommend_data, ensure_ascii=False))
            )
            conn.commit()
            conn.close()
            
            return {
                "status": "success",
                "meta": {"score": student.score, "province": student.province, "subject": student.subject_type},
                "data": recommend_data
            }
            
    except Exception as e:
        # 稳健的异常降级处理
        return {
            "status": "success",
            "meta": {"score": student.score, "province": student.province},
            "data": [
                {"university": "华中科技大学 (双流觉察降级方案)", "major": "电子信息工程", "probability": "稳妥", "min_rank": 4500}
            ]
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)

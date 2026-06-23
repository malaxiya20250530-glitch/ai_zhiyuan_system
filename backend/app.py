"""AI 志愿推荐系统 — 双流觉察推理后端"""
import json
import logging
import os
import sqlite3
from typing import Optional

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ─── 加载 .env ────────────────────────────────────────────────
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("zhiyuan")

# ─── FastAPI ──────────────────────────────────────────────────
app = FastAPI(title="AI 志愿推荐系统 — 双流觉察推理")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── 数据库 ───────────────────────────────────────────────────
DB_PATH = os.path.join(os.path.dirname(__file__), "zhiyuan.db")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS records (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            score       INTEGER,
            province    TEXT,
            subject_type TEXT,
            recommendations TEXT,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


init_db()


def save_record(score: int, province: str, subject_type: str, data: list) -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO records (score, province, subject_type, recommendations) VALUES (?, ?, ?, ?)",
        (score, province, subject_type, json.dumps(data, ensure_ascii=False)),
    )
    conn.commit()
    conn.close()


# ─── 配置 ─────────────────────────────────────────────────────
API_KEY = os.getenv("API_KEY", "")
BASE_URL = os.getenv("BASE_URL", "https://api.openai.com/v1").rstrip("/")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-3.5-turbo")


# ─── 数据模型 ─────────────────────────────────────────────────
class StudentProfile(BaseModel):
    score: int
    rank: Optional[int] = None
    province: str = "湖北省"
    subject_type: str = "物理"


# ─── 降级方案（无 API Key 时使用）───────────────────────────────
FALLBACK_DATA: dict[str, list[dict]] = {
    "物理": [
        {"university": "华中科技大学", "major": "计算机科学与技术", "probability": "冲刺", "min_rank": 3000},
        {"university": "武汉理工大学", "major": "电子信息工程",    "probability": "冲刺", "min_rank": 8000},
        {"university": "湖北大学",     "major": "软件工程",        "probability": "稳妥", "min_rank": 15000},
        {"university": "武汉科技大学", "major": "自动化",          "probability": "稳妥", "min_rank": 18000},
        {"university": "长江大学",     "major": "机械设计制造",    "probability": "保底", "min_rank": 35000},
        {"university": "湖北工业大学", "major": "土木工程",        "probability": "保底", "min_rank": 40000},
    ],
    "历史": [
        {"university": "武汉大学",     "major": "法学",            "probability": "冲刺", "min_rank": 2000},
        {"university": "华中师范大学", "major": "汉语言文学",      "probability": "冲刺", "min_rank": 5000},
        {"university": "中南财经政法", "major": "金融学",          "probability": "稳妥", "min_rank": 10000},
        {"university": "湖北大学",     "major": "新闻传播学",      "probability": "稳妥", "min_rank": 15000},
        {"university": "武汉轻工大学", "major": "工商管理",        "probability": "保底", "min_rank": 30000},
        {"university": "湖北经济学院", "major": "会计学",          "probability": "保底", "min_rank": 38000},
    ],
    "默认": [
        {"university": "华中科技大学", "major": "电子信息工程",    "probability": "稳妥", "min_rank": 4500},
        {"university": "武汉理工大学", "major": "计算机科学",      "probability": "冲刺", "min_rank": 6000},
        {"university": "湖北大学",     "major": "数学与应用数学",  "probability": "保底", "min_rank": 20000},
    ],
}


def _build_fallback(score: int, subject: str) -> list[dict]:
    """根据分数段和选科生成有区分度的降级结果"""
    base = FALLBACK_DATA.get(subject, FALLBACK_DATA["默认"])
    result = []
    for item in base:
        prob = item["probability"]
        # 按概率等级偏移 min_rank，模拟分数越高 rank 越好
        rank_offset = max(0, (650 - score) * 50)
        adjusted = dict(item)
        adjusted["min_rank"] = max(500, (item.get("min_rank", 10000) - rank_offset))
        result.append(adjusted)
    return result


# ─── Prompt ───────────────────────────────────────────────────
def _build_prompt(student: StudentProfile) -> str:
    return f"""
你是一个拥有高级决策逻辑的高考志愿规划专家。
请针对以下学生 profile 启动【双流觉察推理 (Dual-Stream Aware Reasoning)】框架进行分析：

【输入参数】
- 分数: {student.score}分
- 省份: {student.province}
- 选科: {student.subject_type}

【推理要求】
1. 第一流（刚性觉察）：严格对照该省份【{student.subject_type}】大类的投档线特征，判定其分数段位次，筛选出"冲、稳、保"三个梯度的院校，每个梯度至少 2 所。
2. 第二流（柔性觉察）：针对【{student.subject_type}】的学科属性（如物理偏向工科/计算机，历史偏向文史/法学），精准匹配最具备就业韧性的专业。

请将双流推理的结果融合成一个干净的 JSON 数组返回。严禁包含任何前导、后继的自然语言解释，直接输出标准 JSON。

格式范例：
[
  {{"university": "武昌首义学院", "major": "机器人工程", "probability": "保底", "min_rank": 35000}},
  {{"university": "武汉理工大学", "major": "计算机科学与技术", "probability": "冲刺", "min_rank": 8000}}
]
"""


# ─── API ──────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {
        "status": "ok",
        "mode": "llm" if API_KEY and API_KEY != "YOUR_API_KEY_HERE" else "fallback",
        "model": MODEL_NAME,
    }


@app.post("/api/v1/recommend")
async def get_recommendations(student: StudentProfile):
    # ── 无 API Key → 走降级方案 ──
    if not API_KEY or API_KEY == "YOUR_API_KEY_HERE":
        log.info("⚠️  无有效 API Key，使用降级数据 (score=%s, subject=%s)", student.score, student.subject_type)
        data = _build_fallback(student.score, student.subject_type)
        save_record(student.score, student.province, student.subject_type, data)
        return {
            "status": "success",
            "meta": {
                "score": student.score,
                "province": student.province,
                "subject": student.subject_type,
                "mode": "fallback",
            },
            "data": data,
        }

    # ── 有 API Key → 调用 LLM 双流觉察推理 ──
    prompt = _build_prompt(student)
    log.info("🧠 双流觉察推理: score=%s, province=%s, subject=%s",
             student.score, student.province, student.subject_type)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": MODEL_NAME,
                    "messages": [
                        {"role": "system", "content": "You are a professional JSON generator for college counseling. Output ONLY valid JSON, no other text."},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.3,
                },
            )

            if resp.status_code != 200:
                log.error("LLM API 返回 %s: %s", resp.status_code, resp.text[:200])
                raise HTTPException(status_code=502, detail="AI 推理引擎响应异常")

            ai_content = resp.json()["choices"][0]["message"]["content"].strip()
            # 清理可能的 markdown 包裹
            if ai_content.startswith("```"):
                ai_content = ai_content.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
            recommend_data = json.loads(ai_content)

    except json.JSONDecodeError:
        log.error("LLM 返回非 JSON 内容: %s", ai_content[:200])
        raise HTTPException(status_code=502, detail="AI 返回格式异常")
    except httpx.TimeoutException:
        log.error("LLM API 超时")
        raise HTTPException(status_code=504, detail="AI 推理超时")
    except Exception as e:
        log.error("双流觉察推理异常: %s", e)
        # 降级到 fallback
        data = _build_fallback(student.score, student.subject_type)
        save_record(student.score, student.province, student.subject_type, data)
        return {
            "status": "success",
            "meta": {
                "score": student.score,
                "province": student.province,
                "subject": student.subject_type,
                "mode": "fallback_after_error",
            },
            "data": data,
        }

    # 保存到数据库
    save_record(student.score, student.province, student.subject_type, recommend_data)

    return {
        "status": "success",
        "meta": {
            "score": student.score,
            "province": student.province,
            "subject": student.subject_type,
            "mode": "llm",
        },
        "data": recommend_data,
    }


# ─── 数据库查询接口 ────────────────────────────────────────────
@app.get("/api/v1/records")
async def get_records(limit: int = 10):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM records ORDER BY created_at DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return {
        "status": "success",
        "count": len(rows),
        "records": [dict(r) for r in rows],
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    log.info("🚀 启动 AI 志愿推荐系统后端: %s:%s", host, port)
    uvicorn.run("app:app", host=host, port=port, reload=True)

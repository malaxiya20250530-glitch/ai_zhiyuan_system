#!/usr/bin/env python3
"""
🎯 AI 志愿推荐系统 — 闭环测试 (End-to-End)

测试流程：
  1. 检查后端是否存活
  2. 调用 /api/v1/recommend (正常路径)
  3. 验证返回数据结构与前端模型完全对齐
  4. 测试边缘情况：分数边界、空输入
  5. 检查数据库记录是否写入
  6. ✅/❌ 报告

运行: python3 scripts/test_e2e.py
"""

import json
import os
import sys
import urllib.request
import urllib.error

BASE_URL = os.getenv("TEST_BASE_URL", "http://127.0.0.1:8000")

PASS = 0
FAIL = 0


def check(description: str, condition: bool, detail: str = "") -> None:
    """测试断言"""
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  ✅ {description}")
    else:
        FAIL += 1
        print(f"  ❌ {description}")
        if detail:
            print(f"      → {detail}")


def api_post(path: str, body: dict) -> dict:
    """调用后端 API"""
    url = f"{BASE_URL}{path}"
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return json.loads(e.read())
    except Exception as e:
        return {"error": str(e)}


def api_get(path: str) -> dict:
    """GET 请求"""
    try:
        with urllib.request.urlopen(f"{BASE_URL}{path}", timeout=10) as resp:
            return json.loads(resp.read())
    except Exception as e:
        return {"error": str(e)}


# ─── 测试用例 ─────────────────────────────────────────────────

def test_health():
    print("\n📡 [健康检查]")
    result = api_get("/health")
    check("后端存活", "status" in result and result.get("status") == "ok")


def test_normal_recommend():
    print("\n🎯 [正常推荐 — 物理 600分]")
    result = api_post("/api/v1/recommend", {
        "score": 600,
        "province": "湖北省",
        "subject_type": "物理",
    })

    # 顶层结构
    check("返回 status=success", result.get("status") == "success",
          f"got: {result.get('status')}")
    check("包含 meta 字段", "meta" in result)
    check("包含 data 数组", isinstance(result.get("data"), list))

    if result.get("data"):
        item = result["data"][0]
        check("data[0] 含 university", "university" in item)
        check("data[0] 含 major", "major" in item)
        check("data[0] 含 probability", "probability" in item,
              f"keys: {list(item.keys())}")
        check("data[0] 含 min_rank", "min_rank" in item)

        # 验证概率值合法
        valid_probs = {"冲刺", "稳妥", "保底"}
        for i, it in enumerate(result["data"]):
            prob = it.get("probability", "")
            check(f"data[{i}] probability 合法 ({prob})",
                  prob in valid_probs,
                  f"got: {prob}")

        check("返回至少 3 条推荐", len(result["data"]) >= 3,
              f"count: {len(result['data'])}")


def test_history_recommend():
    print("\n📚 [文科推荐 — 历史 550分]")
    result = api_post("/api/v1/recommend", {
        "score": 550,
        "province": "湖北省",
        "subject_type": "历史",
    })
    check("文科推荐成功", result.get("status") == "success")
    if result.get("data"):
        check("文科返回 >0 条", len(result["data"]) > 0)


def test_boundary_scores():
    print("\n📏 [边界分数]")

    # 极低分
    low = api_post("/api/v1/recommend", {"score": 200, "province": "湖北省", "subject_type": "物理"})
    check("200分仍返回结果", low.get("status") == "success")

    # 满分
    high = api_post("/api/v1/recommend", {"score": 750, "province": "湖北省", "subject_type": "物理"})
    check("750分仍返回结果", high.get("status") == "success")

    # 零分
    zero = api_post("/api/v1/recommend", {"score": 0, "province": "湖北省", "subject_type": "物理"})
    check("0分仍返回结果", zero.get("status") == "success")


def test_database_records():
    print("\n🗄️ [数据库记录]")
    result = api_get("/api/v1/records")
    check("记录查询成功", result.get("status") == "success")
    check("记录数 >0", result.get("count", 0) > 0,
          f"count: {result.get('count', 0)}")

    if result.get("records"):
        rec = result["records"][0]
        check("记录含 score 字段", "score" in rec)
        check("记录含 recommendations (JSON字符串)", "recommendations" in rec)
        # 验证 recommendations 是合法 JSON
        try:
            json.loads(rec["recommendations"])
            check("recommendations 可解析为 JSON", True)
        except (json.JSONDecodeError, TypeError):
            check("recommendations 可解析为 JSON", False)


def test_frontend_alignment():
    """
    关键测试：验证后端返回的数据结构
    与前端 ai_service.dart 的 RecommendItem 模型完全对齐
    """
    print("\n🔄 [前后端对齐验证]")
    result = api_post("/api/v1/recommend", {
        "score": 600,
        "province": "湖北省",
        "subject_type": "物理",
    })

    if not result.get("data"):
        check("有数据可验证", False, "data 为空")
        return

    # 前端 RecommendItem.fromJson 期望的字段
    required_fields = {"university", "major", "probability", "min_rank"}

    for i, item in enumerate(result["data"]):
        keys = set(item.keys())
        missing = required_fields - keys
        check(f"data[{i}] 字段对齐 ({keys & required_fields})",
              not missing,
              f"缺少字段: {missing}")

        # 类型对齐
        if "min_rank" in item:
            check(f"data[{i}] min_rank 是整数", isinstance(item["min_rank"], int),
                  f"type: {type(item['min_rank']).__name__}")


# ─── 主入口 ───────────────────────────────────────────────────

def main():
    print("╔══════════════════════════════════════════╗")
    print("║  🎯 AI 志愿推荐系统 — 闭环测试            ║")
    print("╚══════════════════════════════════════════╝")
    print(f"   后端地址: {BASE_URL}")

    global PASS, FAIL
    PASS = 0
    FAIL = 0

    test_health()
    test_normal_recommend()
    test_history_recommend()
    test_boundary_scores()
    test_database_records()
    test_frontend_alignment()

    # ── 汇总 ──
    print(f"\n{'='*40}")
    print(f"  ✅ 通过: {PASS}   ❌ 失败: {FAIL}   📊 总计: {PASS + FAIL}")
    print(f"{'='*40}")

    if FAIL > 0:
        print("\n⚠️  部分测试未通过，请检查后端日志。")
        sys.exit(1)
    else:
        print("\n🎉 闭环测试全部通过！前后端数据完全对齐。")
        sys.exit(0)


if __name__ == "__main__":
    main()

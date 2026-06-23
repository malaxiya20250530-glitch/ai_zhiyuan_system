#!/usr/bin/env python3
"""
🎯 AI 志愿推荐系统 — 闭环测试 (End-to-End)

自动启动后端 → 运行全部测试 → 清理退出。
无需手动先启动后端。

运行: python3 scripts/test_e2e.py
"""

import json
import os
import signal
import subprocess
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

# ── 配置 ───────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
BACKEND_DIR = PROJECT_DIR / "backend"
BACKEND_SCRIPT = str(BACKEND_DIR / "app.py")
BASE_URL = os.getenv("TEST_BASE_URL", "http://127.0.0.1:8000")
BACKEND_PORT = 8000

PASS = 0
FAIL = 0

backend_proc: subprocess.Popen | None = None


# ── 后端生命周期管理 ───────────────────────────────────────

def start_backend() -> subprocess.Popen | None:
    """启动后端进程，返回 Popen 对象"""
    if not BACKEND_DIR.exists():
        print(f"  ⚠️  后端目录不存在: {BACKEND_DIR}")
        return None
    if not os.path.isfile(BACKEND_SCRIPT):
        print(f"  ⚠️  后端脚本不存在: {BACKEND_SCRIPT}")
        return None

    print(f"  🚀 启动后端: python3 {BACKEND_SCRIPT}")
    proc = subprocess.Popen(
        ["python3", BACKEND_SCRIPT],
        cwd=str(BACKEND_DIR),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        # 让后端进程成为进程组组长，方便后续 kill 整个组
        start_new_session=True,
    )
    return proc


def wait_for_backend(timeout: int = 15) -> bool:
    """等待后端就绪，最多 timeout 秒"""
    print(f"  ⏳ 等待后端就绪 (超时 {timeout}s)...", end="", flush=True)
    for i in range(timeout):
        try:
            req = urllib.request.Request(f"{BASE_URL}/health")
            with urllib.request.urlopen(req, timeout=2) as resp:
                data = json.loads(resp.read())
                if data.get("status") == "ok":
                    print(f" 第 {i+1}s ✅")
                    return True
        except Exception:
            pass
        print(".", end="", flush=True)
        time.sleep(1)
    print(" ❌")
    return False


def stop_backend(proc: subprocess.Popen | None) -> None:
    """停止后端进程"""
    if proc is None:
        return
    print("  🧹 清理后端...", end="", flush=True)
    try:
        # 先优雅终止
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            # 杀整个进程组
            pgid = os.getpgid(proc.pid)
            os.killpg(pgid, signal.SIGKILL)
            proc.wait()
    except Exception:
        try:
            proc.kill()
            proc.wait()
        except Exception:
            pass
    print(" ✅")


# ── 测试工具 ───────────────────────────────────────────────

def check(description: str, condition: bool, detail: str = "") -> None:
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
        try:
            return json.loads(e.read())
        except Exception:
            return {"error": f"HTTP {e.code}"}
    except Exception as e:
        return {"error": str(e)}


def api_get(path: str) -> dict:
    try:
        with urllib.request.urlopen(f"{BASE_URL}{path}", timeout=10) as resp:
            return json.loads(resp.read())
    except Exception as e:
        return {"error": str(e)}


# ─── 测试用例 ──────────────────────────────────────────────

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


def test_with_rank():
    print("\n📊 [带位次推荐 — 物理 600分 省排名5000]")
    result = api_post("/api/v1/recommend", {
        "score": 600,
        "province": "湖北省",
        "subject_type": "物理",
        "rank": 5000,
    })
    check("带位次返回 status=success", result.get("status") == "success")
    if result.get("data"):
        check("带位次返回 >0 条", len(result["data"]) > 0)
        check("meta 含 rank字段", result.get("meta", {}).get("rank") == 5000)


def test_boundary_scores():
    print("\n📏 [边界分数]")
    low = api_post("/api/v1/recommend", {"score": 200, "province": "湖北省", "subject_type": "物理"})
    check("200分仍返回结果", low.get("status") == "success")

    high = api_post("/api/v1/recommend", {"score": 750, "province": "湖北省", "subject_type": "物理"})
    check("750分仍返回结果", high.get("status") == "success")

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
        try:
            json.loads(rec["recommendations"])
            check("recommendations 可解析为 JSON", True)
        except (json.JSONDecodeError, TypeError):
            check("recommendations 可解析为 JSON", False)


def test_frontend_alignment():
    print("\n🔄 [前后端对齐验证]")
    result = api_post("/api/v1/recommend", {
        "score": 600,
        "province": "湖北省",
        "subject_type": "物理",
    })

    if not result.get("data"):
        check("有数据可验证", False, "data 为空")
        return

    required_fields = {"university", "major", "probability", "min_rank"}

    for i, item in enumerate(result["data"]):
        keys = set(item.keys())
        missing = required_fields - keys
        check(f"data[{i}] 字段对齐 ({keys & required_fields})",
              not missing,
              f"缺少字段: {missing}")

        if "min_rank" in item:
            check(f"data[{i}] min_rank 是整数", isinstance(item["min_rank"], int),
                  f"type: {type(item['min_rank']).__name__}")


# ─── 主入口 ───────────────────────────────────────────────────

def main():
    global PASS, FAIL, backend_proc

    print("╔══════════════════════════════════════════╗")
    print("║  🎯 AI 志愿推荐系统 — 闭环测试            ║")
    print("╚══════════════════════════════════════════╝")
    print(f"   后端地址: {BASE_URL}")

    PASS = 0
    FAIL = 0

    # ── 启动后端 ──
    backend_proc = start_backend()
    if backend_proc is None:
        print("\n❌ 无法启动后端，测试终止。")
        sys.exit(1)

    if not wait_for_backend():
        stop_backend(backend_proc)
        print("\n❌ 后端启动超时，测试终止。")
        sys.exit(1)

    # ── 执行测试 ──
    try:
        test_health()
        test_normal_recommend()
        test_history_recommend()
        test_boundary_scores()
        test_with_rank()
        test_database_records()
        test_frontend_alignment()
    finally:
        # ── 清理 ──
        stop_backend(backend_proc)

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

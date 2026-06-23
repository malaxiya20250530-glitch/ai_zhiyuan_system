# 🎓 AI 志愿推荐系统

AI 高考志愿推荐系统 — Flutter App + Python AI 后端（双流觉察推理）

## 🚀 快速启动

### 1️⃣ 启动 AI 后端
```bash
cd ai_backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

或者启动双流觉察版后端：
```bash
cd backend
pip install -r requirements.txt
python app.py
```

### 2️⃣ 构建 APK（☁️ 推荐：GitHub 云编译）

推送到 `main` 分支自动触发 GitHub Actions 编译：

```bash
git add -A
git commit -m "update"
git push
```

然后打开 [Actions 页面](https://github.com/malaxiya20250530-glitch/ai_zhiyuan_system/actions)：
- 点击最新的 **Build APK** workflow
- 进入后下载 **ai-zhiyuan-apk** 工件
- 解压得到 `app-armeabi-v7a-release.apk` 等文件

也可手动触发：Actions → Build APK → **Run workflow**

### 3️⃣ 本地编译（Ubuntu proot）
```bash
proot-distro login ubuntu
cd ~/ai_zhiyuan_system
bash scripts/build_apk.sh
```

## 📁 项目结构
```
ai_zhiyuan_system/
├── app_flutter/           # Flutter App
│   └── lib/
│       ├── main.dart
│       ├── api/
│       │   └── ai_service.dart    # 网络请求层
│       └── pages/
│           ├── home.dart          # 首页 (分数输入)
│           └── result.dart        # 结果页 (推荐展示)
├── ai_backend/            # Python AI 后端（基础版）
│   ├── main.py            # FastAPI 服务
│   ├── model.py           # Sigmoid 推荐算法
│   └── data.py            # 大学分数线数据
├── backend/               # 双流觉察推理后端
│   └── app.py             # LLM 驱动的智能推荐
├── data/                  # 数据文件
├── scripts/               # 运行/构建脚本
├── .github/workflows/
│   └── build_apk.yml      # GitHub Actions 云编译配置
└── README.md
```

## 🧠 双流觉察推理 (Dual-Stream Aware Reasoning)

系统采用双流觉察推理框架：
- **刚性觉察** — 对照投档线特征，筛选"冲/稳/保"梯度院校
- **柔性觉察** — 匹配学科属性与就业韧性，推荐最适专业

## 🔧 Flutter App 配置

如需更改后端地址（默认 `127.0.0.1:8000`，同一台手机无需修改）：

```dart
// 在 lib/api/ai_service.dart 中:
AIService.baseUrl = 'http://你的局域网IP:8000';
```

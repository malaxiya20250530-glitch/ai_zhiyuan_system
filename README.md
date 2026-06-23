# 🎓 AI 志愿推荐系统

AI 高考志愿推荐系统 — Flutter App + Python AI 后端

## 🚀 快速启动

### 1️⃣ 启动 AI 后端
```bash
cd ai_backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 2️⃣ 运行 Flutter App
```bash
cd app_flutter
flutter pub get
flutter run
```

### 3️⃣ 构建 APK
```bash
# 在 Ubuntu proot 中
bash scripts/build_apk.sh
# APK 输出: app_flutter/build/app/outputs/flutter-apk/app-release.apk
```

## 📁 项目结构
```
ai_zhiyuan_system/
├── app_flutter/        # Flutter App
│   ├── lib/
│   │   ├── main.dart
│   │   ├── pages/
│   │   │   ├── home.dart     # 首页 (输入分数)
│   │   │   └── result.dart   # 结果页 (展示推荐)
│   │   └── api/
│   │       └── ai_service.dart  # API 调用
│   └── pubspec.yaml
├── ai_backend/         # Python AI 后端
│   ├── main.py        # FastAPI 服务
│   ├── model.py       # AI 推荐算法 (Sigmoid)
│   └── data.py        # 大学分数线数据
├── data/              # 数据文件
├── scripts/           # 运行/构建脚本
└── README.md
```

## 🧠 AI 算法
基于 Sigmoid 函数的录取概率计算：
- gap = 你的分数 - 学校最低录取分
- prob = 1 / (1 + e^(-gap/15))
- 概率越高，录取可能性越大

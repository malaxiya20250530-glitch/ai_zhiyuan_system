#!/usr/bin/env bash
# 🎯 AI 志愿推荐系统 - APK 构建脚本
#
# 方式一（推荐）：GitHub Cloud Build
#   推送代码到 main 分支，GitHub Actions 自动编译
#   构建完成后在 Actions 页面下载 APK
#
# 方式二：本地构建（Ubuntu proot）
#   proot-distro login ubuntu
#   cd ~/ai_zhiyuan_system
#   bash scripts/build_apk.sh

cd "$(dirname "$0")/.."

echo "=== 🎯 AI 志愿推荐 - APK 构建 ==="
echo ""

# 检查是否在 proot/Ubuntu 环境
IS_UBUNTU=false
if [ -f /etc/os-release ] && grep -qi ubuntu /etc/os-release 2>/dev/null; then
  IS_UBUNTU=true
fi

if [ "$IS_UBUNTU" = false ]; then
  echo "⚠️  当前不在 Ubuntu proot 环境"
  echo ""
  echo "📌 推荐使用 GitHub Actions 云端编译："
  echo "   1. 提交代码到 main 分支"
  echo "   2. 访问 https://github.com/malaxiya20250530-glitch/ai_zhiyuan_system/actions"
  echo "   3. 下载编译好的 APK"
  echo ""
  echo "📌 如需本地编译，请先进入 Ubuntu proot："
  echo "   proot-distro login ubuntu"
  echo "   cd ~/ai_zhiyuan_system"
  echo "   bash scripts/build_apk.sh"
  echo ""
  exit 1
fi

# ─── Ubuntu proot 本地编译 ──────────────────────────────

FLUTTER_ROOT="/data/data/com.termux/files/home/flutter"
export FLUTTER_ROOT
export PATH="$FLUTTER_ROOT/bin:$PATH"

cd app_flutter

echo "1️⃣ 生成 Android 脚手架..."
flutter create --project-name ai_zhiyuan_system --platforms android . 2>/dev/null || true

echo "2️⃣ 获取依赖..."
flutter pub get || { echo "❌ pub get 失败"; exit 1; }

echo "3️⃣ 构建 APK (release)..."
flutter build apk --release --split-per-abi || { echo "❌ 构建失败"; exit 1; }

echo ""
echo "✅ APK 构建成功!"
echo ""
echo "📱 输出文件:"
ls -lh build/app/outputs/flutter-apk/*.apk 2>/dev/null

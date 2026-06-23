#!/usr/bin/env bash
# 在 Ubuntu (proot) 中构建 APK
cd "$(dirname "$0")/.."

echo "=== 构建 Android APK ==="
echo "确保已在 Ubuntu 中运行此脚本"
echo ""

# 检查是否在 proot/Ubuntu 环境
if [ ! -f /etc/os-release ] || ! grep -qi ubuntu /etc/os-release 2>/dev/null; then
  echo "⚠️  建议在 Ubuntu proot 环境中构建"
  echo "   使用: proot-distro login ubuntu"
  echo ""
fi

FLUTTER_ROOT="/data/data/com.termux/files/home/flutter"
export FLUTTER_ROOT
export PATH="$FLUTTER_ROOT/bin:$PATH"

cd app_flutter

echo "1️⃣ 获取依赖..."
flutter pub get || { echo "❌ pub get 失败"; exit 1; }

echo ""
echo "2️⃣ 构建 APK..."
flutter build apk --release || { echo "❌ 构建失败"; exit 1; }

echo ""
echo "✅ APK 构建成功!"
echo "   输出: build/app/outputs/flutter-apk/app-release.apk"

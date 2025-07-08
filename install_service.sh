#!/bin/bash

# 安装和启用 Simple Notes 服务脚本
# 用法: sudo ./install_service.sh

SERVICE_NAME="simple-notes"
SERVICE_FILE="simple-notes.service"
SYSTEMD_DIR="/etc/systemd/system"

echo "🚀 开始安装 Simple Notes 开机自启动服务..."

# 检查是否以 root 权限运行
if [ "$EUID" -ne 0 ]; then
    echo "❌ 请使用 sudo 运行此脚本"
    echo "   sudo ./install_service.sh"
    exit 1
fi

# 检查服务文件是否存在
if [ ! -f "$SERVICE_FILE" ]; then
    echo "❌ 找不到服务文件: $SERVICE_FILE"
    echo "   请确保在正确的目录下运行此脚本"
    exit 1
fi

# 复制服务文件到系统目录
echo "📁 复制服务文件到 $SYSTEMD_DIR..."
cp "$SERVICE_FILE" "$SYSTEMD_DIR/"

# 重新加载 systemd
echo "🔄 重新加载 systemd..."
systemctl daemon-reload

# 启用服务（开机自启动）
echo "✅ 启用开机自启动..."
systemctl enable "$SERVICE_NAME"

# 启动服务
echo "🚀 启动服务..."
systemctl start "$SERVICE_NAME"

# 检查服务状态
echo "📊 检查服务状态..."
if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo "✅ 服务安装成功并正在运行！"
    echo ""
    echo "📋 常用命令："
    echo "   查看状态: sudo systemctl status $SERVICE_NAME"
    echo "   停止服务: sudo systemctl stop $SERVICE_NAME"
    echo "   重启服务: sudo systemctl restart $SERVICE_NAME"
    echo "   查看日志: sudo journalctl -u $SERVICE_NAME -f"
    echo "   禁用自启: sudo systemctl disable $SERVICE_NAME"
    echo ""
    echo "🌐 访问地址: http://$(hostname -I | awk '{print $1}'):8501"
else
    echo "❌ 服务启动失败，请检查配置"
    echo "   查看详细错误: sudo systemctl status $SERVICE_NAME"
    echo "   查看日志: sudo journalctl -u $SERVICE_NAME"
fi
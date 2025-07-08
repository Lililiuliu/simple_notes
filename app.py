#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
极简自托管局域网共享服务
支持文本和文件的上传、下载、删除功能
适合桌面端浏览，局域网内多设备共享
"""

import os
import sqlite3
import time
import base64
import socket
import platform
from datetime import datetime
from pathlib import Path
import streamlit as st

# 配置页面
st.set_page_config(
    page_title="局域网共享",
    page_icon="📂",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 数据库和文件存储路径
DB_PATH = "shared_storage.db"
FILES_DIR = "shared_files"

def init_database():
    """初始化数据库"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 创建文本分享表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS shared_texts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 创建文件分享表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS shared_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            original_name TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def ensure_files_dir():
    """确保文件存储目录存在"""
    Path(FILES_DIR).mkdir(exist_ok=True)

def save_text(content):
    """保存文本分享"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # 使用内容的前30个字符作为标题
    title = content[:30] + ("..." if len(content) > 30 else "")
    cursor.execute(
        "INSERT INTO shared_texts (title, content) VALUES (?, ?)",
        (title, content)
    )
    conn.commit()
    conn.close()

def save_file(uploaded_file):
    """保存文件分享"""
    # 生成唯一文件名
    timestamp = str(int(time.time()))
    filename = f"{timestamp}_{uploaded_file.name}"
    file_path = os.path.join(FILES_DIR, filename)
    
    # 保存文件到磁盘
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    # 保存文件信息到数据库
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO shared_files (filename, original_name, file_size) VALUES (?, ?, ?)",
        (filename, uploaded_file.name, uploaded_file.size)
    )
    conn.commit()
    conn.close()
    
    return filename

def get_shared_texts():
    """获取所有文本分享"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM shared_texts ORDER BY created_at DESC")
    texts = cursor.fetchall()
    conn.close()
    return texts

def get_shared_files():
    """获取所有文件分享"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM shared_files ORDER BY created_at DESC")
    files = cursor.fetchall()
    conn.close()
    return files

def delete_text(text_id):
    """删除文本分享"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM shared_texts WHERE id = ?", (text_id,))
    conn.commit()
    conn.close()

def delete_file(file_id):
    """删除文件分享"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 获取文件信息
    cursor.execute("SELECT filename FROM shared_files WHERE id = ?", (file_id,))
    result = cursor.fetchone()
    
    if result:
        filename = result[0]
        file_path = os.path.join(FILES_DIR, filename)
        
        # 删除物理文件
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # 删除数据库记录
        cursor.execute("DELETE FROM shared_files WHERE id = ?", (file_id,))
        conn.commit()
    
    conn.close()

def format_file_size(size_bytes):
    """格式化文件大小"""
    if size_bytes == 0:
        return "0 B"
    size_names = ["B", "KB", "MB", "GB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"

def get_download_link(filename, original_name):
    """生成文件下载链接"""
    file_path = os.path.join(FILES_DIR, filename)
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            bytes_data = f.read()
            b64 = base64.b64encode(bytes_data).decode()
            href = f'<a href="data:application/octet-stream;base64,{b64}" download="{original_name}">📥 下载</a>'
            return href
    return "文件不存在"

# 初始化
init_database()
ensure_files_dir()

# 主界面
st.title("📂 局域网共享")

# 顶部信息栏 - 统计信息
texts = get_shared_texts()
files = get_shared_files()

col1, col2 = st.columns(2)
with col1:
    st.metric("📝 文本", len(texts))
with col2:
    st.metric("📁 文件", len(files))

st.divider()

# 上传区域
upload_col1, upload_col2 = st.columns(2)

with upload_col1:
    st.subheader("📝 分享文本")
    with st.form("text_form"):
        content = st.text_area("内容", height=150, placeholder="输入要分享的文本内容...")
        
        if st.form_submit_button("🚀 分享文本", use_container_width=True):
            if content.strip():
                save_text(content.strip())
                st.success("✅ 文本分享成功！")
                st.rerun()
            else:
                st.error("❌ 请填写内容")

with upload_col2:
    st.subheader("📁 分享文件")
    uploaded_files = st.file_uploader(
        "选择文件",
        accept_multiple_files=True,
        help="支持多文件上传，单文件最大 100MB"
    )
    
    if uploaded_files:
        st.write(f"已选择 {len(uploaded_files)} 个文件")
        if st.button("🚀 分享文件", use_container_width=True):
            success_count = 0
            for uploaded_file in uploaded_files:
                if uploaded_file.size > 100 * 1024 * 1024:  # 100MB
                    st.error(f"❌ {uploaded_file.name} 超过 100MB")
                    continue
                
                try:
                    save_file(uploaded_file)
                    success_count += 1
                except Exception as e:
                    st.error(f"❌ {uploaded_file.name} 上传失败")
            
            if success_count > 0:
                st.success(f"✅ 成功分享 {success_count} 个文件！")
                st.rerun()

st.divider()

# 内容展示区域
display_col1, display_col2 = st.columns(2)

with display_col1:
    st.subheader("📝 文本列表")
    
    if not texts:
        st.info("暂无文本分享")
    else:
        # 搜索功能
        search_text = st.text_input("🔍 搜索文本", placeholder="输入关键词...")
        
        for text in texts:
            text_id, title, content, created_at = text
            
            # 搜索过滤
            if search_text and search_text.lower() not in content.lower():
                continue
            
            with st.container():
                # 内容和删除按钮
                text_col1, text_col2 = st.columns([4, 1])
                with text_col1:
                    # 显示内容预览
                    if len(content) > 100:
                        st.markdown(f"**{content[:100]}...**")
                        with st.expander("查看完整内容"):
                            st.text(content)
                    else:
                        st.markdown(f"**{content}**")
                with text_col2:
                    if st.button("🗑️", key=f"del_text_{text_id}", help="删除"):
                        delete_text(text_id)
                        st.rerun()
                
                # 时间信息
                st.caption(f"⏰ {created_at}")
                
                st.divider()

with display_col2:
    st.subheader("📁 文件列表")
    
    if not files:
        st.info("暂无文件分享")
    else:
        # 搜索功能
        search_file = st.text_input("🔍 搜索文件", placeholder="输入文件名...")
        
        for file in files:
            file_id, filename, original_name, file_size, created_at = file
            
            # 搜索过滤
            if search_file and search_file.lower() not in original_name.lower():
                continue
            
            with st.container():
                # 文件名和删除按钮
                file_col1, file_col2 = st.columns([4, 1])
                with file_col1:
                    st.markdown(f"**📄 {original_name}**")
                with file_col2:
                    if st.button("🗑️", key=f"del_file_{file_id}", help="删除"):
                        delete_file(file_id)
                        st.rerun()
                
                # 时间信息
                st.caption(f"⏰ {created_at}")
                
                # 文件大小和下载
                size_col, download_col = st.columns([1, 1])
                with size_col:
                    st.text(f"📊 {format_file_size(file_size)}")
                with download_col:
                    download_link = get_download_link(filename, original_name)
                    st.markdown(download_link, unsafe_allow_html=True)
                
                st.divider()

# 页脚提示
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666; font-size: 0.9em;'>"
    "💡 确保设备在同一局域网内，使用 IP:8501 访问此服务"
    "</div>",
    unsafe_allow_html=True
)

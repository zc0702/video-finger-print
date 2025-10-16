# 视频指纹识别系统

基于 Milvus 向量数据库的视频指纹识别系统，支持视频指纹生成和相似内容查找。

## 功能特性

- 视频帧特征提取（基于颜色直方图和纹理特征）
- 基于 Milvus 的高效向量存储和检索
- 相似视频内容查找
- 支持多种视频格式（MP4、AVI、MOV、MKV等）
- 支持视频URL下载和处理（YouTube、Bilibili等）
- 可配置的相似度阈值
- 自动临时文件管理

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 1. 环境准备
```bash
# 安装依赖
pip install -r requirements.txt

# 启动 Milvus 服务
docker-compose up -d milvus etcd minio

# 配置环境变量
cp env.example .env
```

### 2. 基本使用

#### 添加视频（支持文件路径和URL）
```bash
# 添加本地视频文件
python main.py add path/to/video.mp4

# 添加URL视频
python main.py add "https://example.com/video.mp4"
```

#### 搜索相似视频
```bash
# 搜索相似视频
python main.py search query_video.mp4 --top-k 10 --threshold 0.8

# 使用URL搜索
python main.py search "https://example.com/query_video.mp4"
```

#### 比较视频
```bash
# 比较两个视频
python main.py compare video1.mp4 video2.mp4

# 比较URL视频
python main.py compare "https://example.com/video1.mp4" "https://example.com/video2.mp4"
```

#### 运行演示
```bash
# 本地视频演示
python main.py demo

# URL视频演示
python url_example.py
```

## 项目结构

```
video-finger-print/
├── src/
│   ├── __init__.py
│   ├── video_processor.py      # 视频处理模块
│   ├── video_downloader.py     # 视频下载模块
│   ├── feature_extractor.py    # 特征提取模块
│   ├── milvus_client.py        # Milvus 客户端
│   └── similarity_search.py    # 相似度搜索模块
├── config/
│   └── config.py              # 配置文件
├── main.py                    # 主程序
├── example.py                 # 使用示例
├── url_example.py             # URL示例
├── quick_start.py             # 快速开始
├── requirements.txt           # 依赖包
├── docker-compose.yml         # Docker部署
└── README.md                  # 说明文档
```

# 视频指纹识别系统

基于 Milvus 向量数据库的视频指纹识别系统，专注于大规模视频URL去重和相似内容查找。

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## ✨ 核心特性

- 🎯 **视频指纹提取** - 基于多特征融合的512维向量（颜色+纹理+边缘）
- 🔍 **相似度检测** - 毫秒级向量检索，自动分级（⭐~⭐⭐⭐⭐⭐）
- 📊 **CSV批量处理** - 支持10万+视频URL批量处理
- 🤖 **智能去重** - 自动检测并分组相似视频
- 📈 **详细报告** - 文本报告 + JSON数据导出

---

## 🚀 快速开始

### 1. 环境准备

```bash
# 安装依赖
pip install -r requirements.txt

# 启动 Milvus 服务
docker-compose up -d

# 配置环境变量
cp env.example .env
```

### 2. 基本使用

```bash
# 添加单个视频
python main.py add video.mp4

# 搜索相似视频
python main.py search query.mp4 --top-k 10

# 比较两个视频
python main.py compare video1.mp4 video2.mp4
```

### 3. 批量处理（核心功能）

```bash
# 基本用法
python batch_process_csv_urls.py videos.csv

# 完整参数
python batch_process_csv_urls.py videos.csv \
    --url-column video_url \
    --threshold 0.90 \
    --encoding utf-8
```

**CSV文件示例**:
```csv
video_id,title,url,category
1,视频标题1,https://example.com/video1.mp4,教育
2,视频标题2,https://example.com/video2.mp4,娱乐
```

---

## 📊 CSV批量处理详解

### CSV文件格式

#### 格式1：只有URL列
```csv
url
https://example.com/video1.mp4
https://example.com/video2.mp4
```

#### 格式2：包含多列（推荐）
```csv
video_id,title,url,uploader
1,视频A,https://example.com/a.mp4,用户A
2,视频B,https://example.com/b.mp4,用户B
```

### 使用参数

```bash
# 自动检测URL列
python batch_process_csv_urls.py videos.csv

# 指定URL列名
python batch_process_csv_urls.py videos.csv --url-column video_url

# 指定相似度阈值
python batch_process_csv_urls.py videos.csv --threshold 0.90

# 指定文件编码（处理中文）
python batch_process_csv_urls.py videos.csv --encoding gbk

# 指定输出文件
python batch_process_csv_urls.py videos.csv --output report.txt
```

### 自动检测功能

**支持的URL列名**（自动识别）:
- 英文: `url`, `link`, `video_url`, `video_link`, `address`, `src`, `source`
- 中文: `链接`, `地址`, `视频链接`

**支持的编码**（自动尝试）:
- UTF-8, GBK, GB2312, UTF-8-SIG

### 支持的视频源

- ✅ YouTube（需要 yt-dlp）
- ✅ Bilibili
- ✅ 视频直链（MP4、AVI、MOV等）
- ✅ CDN视频链接

---

## 📏 相似度标准

| 相似度 | 等级 | 说明 | 处理建议 |
|--------|------|------|---------|
| **95-100%** | ⭐⭐⭐⭐⭐ | 几乎完全相同 | 直接删除重复 |
| **90-95%** | ⭐⭐⭐⭐ | 极高相似度 | 保留高质量版本 |
| **85-90%** | ⭐⭐⭐ | 高度相似 | 人工审核 |
| **75-85%** | ⭐⭐ | 较高相似 | 标记备查 |
| **<75%** | ⭐ | 低相似度 | 仅记录 |

### 实际案例

#### 案例1: 完全相同（98.7%）⭐⭐⭐⭐⭐
```
视频A: movie_trailer_1080p.mp4
视频B: movie_trailer_1080p_copy.mp4
说明: 同一视频的精确副本 → 删除副本
```

#### 案例2: 不同分辨率（94.2%）⭐⭐⭐⭐
```
视频A: tutorial_4k.mp4 (3840x2160)
视频B: tutorial_720p.mp4 (1280x720)
说明: 同一视频的不同分辨率 → 保留4K版本
```

#### 案例3: 添加水印（91.5%）⭐⭐⭐⭐
```
视频A: vlog_original.mp4
视频B: vlog_with_logo.mp4
说明: 添加了角落水印 → 根据需求保留
```

#### 案例4: 剪辑版本（87.3%）⭐⭐⭐
```
视频A: concert_full.mp4 (60分钟)
视频B: concert_highlights.mp4 (15分钟)
说明: 完整版与精华剪辑 → 可能都需要保留
```

---

## 💼 实际应用案例

### 案例1: 视频网站去重（1,000个视频）

```bash
python batch_process_csv_urls.py user_videos.csv --threshold 0.90
```

**典型结果**:
```
总视频数: 1,000
处理成功: 987 (98.7%)
发现重复: 245 个 (24.8%)
相似视频组: 85 组
可节省存储: 约 450 GB
处理时间: 约 1.4 小时
```

**相似视频组示例**:
```
【组 1】同一视频被多次上传 - 8个视频
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  1. user101/video1.mp4 (原始)
  2. user105/video_copy.mp4(相似度: 99.2%)
  3. user203/my_video.mp4 (相似度: 98.8%)
  ...
建议: 删除7个重复，保留原始
节省: 约 56 GB
```

### 案例2: 处理10万视频

**分批处理策略**:
```bash
# 分割CSV文件（每批5000个）
for i in {1..20}; do
    python batch_process_csv_urls.py videos_part_${i}.csv --threshold 0.90
    sleep 60
done
```

**预期结果**:
```
📈 总体统计
├─ 扫描视频总数: 100,000
├─ 成功处理: 99,876 (99.9%)
├─ 处理耗时: 30-40 小时（16核服务器）
└─ 平均速度: 2,500+ 视频/小时

🔍 重复检测结果
├─ 相似度阈值: 90%
├─ 发现相似视频组: 3,721 组
├─ 涉及重复视频数: 12,458 个
├─ 重复率: 12.48%
└─ 可节省存储: 约 1.8 TB

💰 成本节省
└─ 年度节省: $437 (按$0.02/GB/月计算)
```

---


## ❓ 常见问题

### Q1: 如何选择相似度阈值？

根据应用场景选择：
- **去重场景**: 0.90-0.95 （只删除高度相似的）
- **归档整理**: 0.85-0.90 （包含编辑版本）
- **内容审核**: 0.75-0.85 （捕捉更多相似内容）

### Q2: CSV文件乱码怎么办？

指定正确的编码：
```bash
# Windows系统常用GBK
python batch_process_csv_urls.py videos.csv --encoding gbk

# Mac/Linux常用UTF-8
python batch_process_csv_urls.py videos.csv --encoding utf-8
```

### Q3: 处理失败的视频怎么办？

1. 查看报告中的"处理失败"部分
2. 查看错误日志：`csv_video_batch_*.log`
3. 检查URL是否有效
4. 单独处理失败的URL：
```bash
python main.py add "失败的URL"
```

### Q4: 可以中断后继续吗？

可以，已处理的视频保存在Milvus中：
```bash
# 查看已处理数量
python main.py stats

# 继续处理（会自动跳过已存在的）
python batch_process_csv_urls.py remaining.csv
```

### Q5: 如何分割大型CSV文件？

```python
import pandas as pd

df = pd.read_csv('large_videos.csv')
chunk_size = 5000

for i in range(0, len(df), chunk_size):
    chunk = df[i:i+chunk_size]
    chunk.to_csv(f'videos_part_{i//chunk_size + 1}.csv', index=False)
```

### Q6: 内存占用如何？

- 单个视频处理: 约 500MB - 1GB
- Milvus 数据库: 10万视频约需 5-10 GB
- **建议最小配置**: 16GB 内存

### Q7: 支持哪些视频格式？

支持OpenCV可读取的所有格式：
- MP4, AVI, MOV, MKV, WMV, FLV
- WEBM, M4V, 3GP, MPEG
- 以及更多...

### Q8: 如何查看详细日志？

```bash
# 实时查看日志
tail -f csv_video_batch_*.log

# 搜索错误
grep "ERROR" csv_video_batch_*.log

# 查看特定视频的处理
grep "video_name.mp4" csv_video_batch_*.log
```

---

## 📋 输出报告

### 文本报告示例

```
================================================================================
CSV视频URL批处理报告
================================================================================
生成时间: 2024-10-17 14:32:15

总体统计:
- 扫描视频总数: 1,000
- 成功处理: 987
- 处理失败: 13
- 处理耗时: 82.5 分钟

重复检测结果:
- 相似度阈值: 90%
- 相似视频组: 85 个
- 重复视频数: 245 个
- 重复率: 24.8%

相似视频组详情:
【组 1】包含 8 个相似视频
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  1. CSV第2行 | ID: 1001
     标题: 视频标题1
     URL: https://example.com/video1.mp4
  2. CSV第15行 | ID: 1523 | 相似度: 97.8%
     标题: 视频标题2
     URL: https://example.com/video2.mp4
  ...
```

### JSON结果格式

```json
{
  "timestamp": "2024-10-17T14:32:15",
  "statistics": {
    "total_videos": 1000,
    "processed": 987,
    "failed": 13,
    "duplicates_found": 245,
    "duplicate_rate": 24.8,
    "processing_time": 4950.0
  },
  "video_details": [...],
  "similar_groups": [...],
  "failed_videos": [...]
}
```

---

## 🏗️ 项目结构

```
video-finger-print/
├── src/                              # 核心模块
│   ├── video_processor.py           # 视频处理（帧提取）
│   ├── feature_extractor.py         # 特征提取（颜色+纹理+边缘）
│   ├── milvus_client.py             # 向量数据库操作
│   ├── similarity_search.py         # 相似度搜索
│   ├── video_downloader.py          # URL视频下载
│   ├── batch_processing_base.py     # 批处理基类
│   └── logging_config.py            # 日志配置
├── config/
│   └── config.py                    # 配置文件
├── main.py                          # 主程序（单视频操作）
├── batch_process_csv_urls.py       # CSV批量处理（核心脚本）
├── example_videos.csv              # CSV示例文件
├── requirements.txt                # Python依赖
├── docker-compose.yml              # Milvus部署
└── README.md                       # 本文档
```

---

## 🔧 配置说明

主要配置项在 `config/config.py`:

```python
# 视频处理配置
FRAME_INTERVAL = 15      # 帧采样间隔（越大越快，但准确度略降）
MIN_FRAMES = 5          # 最少提取帧数
MAX_FRAMES = 100        # 最大提取帧数
IMAGE_SIZE = (224, 224) # 图像尺寸

# Milvus配置
MILVUS_HOST = 'localhost'
MILVUS_PORT = 19530
DIMENSION = 512         # 特征维度
METRIC_TYPE = 'L2'      # 距离度量

# 相似度阈值
SIMILARITY_THRESHOLD = 0.8
```

**调整建议**:
```python
# 提升速度（略降准确度）
FRAME_INTERVAL = 30
MAX_FRAMES = 50

# 提升准确度（降低速度）
FRAME_INTERVAL = 10
MAX_FRAMES = 150
```

---

## 🛠️ 使用Python API

```python
from src import SimilaritySearch

# 创建搜索器
searcher = SimilaritySearch()

# 添加视频
video_id = searcher.add_video("https://example.com/video.mp4")
print(f"视频ID: {video_id}")

# 搜索相似视频
results = searcher.search_by_video("query.mp4", top_k=10)
for result in results:
    print(f"相似度: {result['similarity']:.2%} - {result['video_name']}")

# 比较两个视频
similarity = searcher.compare_videos("video1.mp4", "video2.mp4")
print(f"相似度: {similarity:.2%}")
```

---

## 🎯 核心技术

### 特征提取流程

```
视频输入
  ↓
帧提取（每15帧采样1帧）
  ↓
单帧特征提取（462维）
  ├─ 颜色直方图（170维）- HSV空间
  ├─ 纹理特征（256维）- LBP算法
  └─ 边缘特征（36维）- Canny+Sobel
  ↓
视频特征聚合（512维）
  └─ 统计聚合（均值+标准差）+ PCA降维
  ↓
向量存储（Milvus）
  ↓
相似度检索（余弦相似度）
```

### 相似度计算

使用 **余弦相似度**（Cosine Similarity）：

$$
\text{similarity} = \frac{\vec{A} \cdot \vec{B}}{||\vec{A}|| \times ||\vec{B}||}
$$

转换为百分比: `similarity × 100%`

---

## 💡 最佳实践

### 1. 处理前准备
- ✅ 确保有足够磁盘空间（临时文件）
- ✅ 备份重要视频
- ✅ 小批量测试验证效果（先处理100个）

### 2. 处理中监控
- ✅ 定期查看日志 `tail -f *.log`
- ✅ 监控系统资源（CPU、内存、磁盘）
- ✅ 每处理5000个保存一次结果

### 3. 处理后审核
- ✅ 人工抽查高相似度组（>95%）
- ✅ 验证删除决策（避免误删）
- ✅ 保留处理报告作为记录

### 4. 相似度阈值选择

```python
# 保守策略（减少误判）
threshold = 0.95  # 只标记几乎完全相同的

# 平衡策略（推荐）
threshold = 0.90  # 标记高度相似的

# 激进策略（捕捉更多）
threshold = 0.85  # 标记中高度相似的
```

---

## 🤝 开发与贡献

### 环境搭建

```bash
# 克隆项目
git clone https://github.com/zc0702/video-finger-print.git
cd video-finger-print

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 安装开发工具
pip install black isort mypy pytest

# 启动Milvus
docker-compose up -d
```

### 扩展批处理功能

```python
from src import BatchProcessingBase

class CustomBatchProcessor(BatchProcessingBase):
    """自定义批处理器"""
    
    def __init__(self, similarity_threshold: float = 0.90):
        super().__init__(similarity_threshold)
    
    def process_custom_source(self, sources):
        """实现自定义数据源处理"""
        for source in sources:
            # 你的处理逻辑
            pass
        
        # 使用基类功能
        self.generate_report()
        self.export_results_json()
```

### 代码规范

```bash
# 格式化代码
black src/ --line-length 100
isort src/

# 类型检查
mypy src/

# 运行测试
pytest tests/
```

---

## 📚 技术参考

- [OpenCV Documentation](https://docs.opencv.org/) - 计算机视觉库
- [Milvus Documentation](https://milvus.io/docs) - 向量数据库
- [yt-dlp GitHub](https://github.com/yt-dlp/yt-dlp) - 视频下载工具

---

## 📄 许可证

MIT License

---

**⭐ 如果这个项目对你有帮助，请给个 Star！**

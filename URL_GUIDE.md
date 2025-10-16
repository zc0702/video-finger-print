# URL视频处理指南

## 支持的URL类型

### 1. 直接视频文件URL
```bash
# 直接视频文件链接
python main.py add "https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4"
```

### 2. 视频平台URL
```bash
# YouTube视频
python main.py add "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Bilibili视频
python main.py add "https://www.bilibili.com/video/BV1xx411c7mu"

# 其他支持的平台
python main.py add "https://vimeo.com/123456789"
```

## 使用示例

### 命令行使用

#### 添加URL视频
```bash
# 添加单个URL视频
python main.py add "https://example.com/video.mp4"

# 添加YouTube视频
python main.py add "https://www.youtube.com/watch?v=VIDEO_ID"
```

#### 搜索相似视频
```bash
# 使用URL搜索
python main.py search "https://example.com/query_video.mp4" --top-k 10

# 使用YouTube URL搜索
python main.py search "https://www.youtube.com/watch?v=VIDEO_ID" --threshold 0.8
```

#### 比较URL视频
```bash
# 比较两个URL视频
python main.py compare "https://example.com/video1.mp4" "https://example.com/video2.mp4"

# 比较YouTube视频
python main.py compare "https://www.youtube.com/watch?v=VIDEO1" "https://www.youtube.com/watch?v=VIDEO2"
```

### 编程接口使用

```python
from src.similarity_search import SimilaritySearch

searcher = SimilaritySearch()

try:
    # 添加URL视频
    video_id = searcher.add_video("https://example.com/video.mp4")
    print(f"视频ID: {video_id}")
    
    # 搜索相似视频
    results = searcher.search_by_video("https://example.com/query.mp4")
    for result in results:
        print(f"相似视频: {result['video_name']}")
        print(f"相似度: {result['similarity']:.4f}")
    
    # 比较视频
    comparison = searcher.compare_videos(
        "https://example.com/video1.mp4",
        "https://example.com/video2.mp4"
    )
    print(f"相似度: {comparison['similarity']:.4f}")

finally:
    searcher.close()
```

## 高级功能

### 批量处理URL视频
```python
urls = [
    "https://example.com/video1.mp4",
    "https://example.com/video2.mp4",
    "https://www.youtube.com/watch?v=VIDEO_ID"
]

video_ids = searcher.batch_add_videos(urls)
print(f"批量添加了 {len(video_ids)} 个视频")
```

### 获取视频信息
```python
from src.video_downloader import VideoDownloader

downloader = VideoDownloader()

# 获取视频信息（不下载）
info = downloader.get_video_info_from_url("https://www.youtube.com/watch?v=VIDEO_ID")
print(f"标题: {info['title']}")
print(f"时长: {info['duration']}秒")
print(f"上传者: {info['uploader']}")
```

## 注意事项

### 1. 网络要求
- 需要稳定的网络连接
- 某些平台可能需要代理访问
- 大文件下载需要足够的带宽

### 2. 平台限制
- YouTube等平台可能有反爬虫机制
- 某些视频可能需要登录才能访问
- 版权保护的内容可能无法下载

### 3. 性能考虑
- URL视频需要先下载再处理，耗时较长
- 建议设置合适的超时时间
- 大文件可能占用较多临时存储空间

### 4. 临时文件管理
- 系统会自动清理临时下载的文件
- 可以手动调用 `downloader.cleanup_temp_files()` 清理
- 临时文件存储在 `temp_videos/` 目录

## 故障排除

### 常见问题

1. **下载失败**
   - 检查URL是否有效
   - 确认网络连接正常
   - 某些平台可能需要特殊处理

2. **格式不支持**
   - 确保URL指向视频文件
   - 检查视频格式是否支持
   - 某些平台可能需要额外配置

3. **权限问题**
   - 某些视频可能需要登录
   - 检查是否有访问权限
   - 考虑使用代理或VPN

### 调试模式
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# 启用详细日志
searcher = SimilaritySearch()
```

## 示例脚本

运行URL示例：
```bash
python url_example.py
```

这将演示如何处理各种类型的URL视频。

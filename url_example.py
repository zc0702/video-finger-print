"""
URL视频处理示例
"""
import os
from src.similarity_search import SimilaritySearch
from src.video_downloader import VideoDownloader

def url_example():
    """URL视频处理示例"""
    print("🌐 URL视频指纹识别示例")
    print("=" * 50)
    
    # 创建搜索器
    searcher = SimilaritySearch()
    downloader = VideoDownloader()
    
    try:
        # 示例URL列表（请替换为实际的视频URL）
        video_urls = [
            "https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4",
            "https://www.learningcontainer.com/wp-content/uploads/2020/05/sample-mp4-file.mp4",
            # 添加更多URL...
        ]
        
        print("📥 处理URL视频...")
        
        for i, url in enumerate(video_urls, 1):
            print(f"\n{i}. 处理URL: {url}")
            
            try:
                # 检查URL是否有效
                if not downloader.is_url(url):
                    print(f"   ❌ 无效的URL格式")
                    continue
                
                # 获取视频信息（不下载）
                print("   📋 获取视频信息...")
                info = downloader.get_video_info_from_url(url)
                print(f"   📺 标题: {info.get('title', 'Unknown')}")
                print(f"   ⏱️  时长: {info.get('duration', 0)}秒")
                print(f"   👤 上传者: {info.get('uploader', 'Unknown')}")
                
                # 添加视频到数据库
                print("   🔄 添加视频到数据库...")
                video_id = searcher.add_video(url)
                print(f"   ✅ 成功添加，ID: {video_id}")
                
            except Exception as e:
                print(f"   ❌ 处理失败: {e}")
        
        # 搜索相似视频
        if video_urls:
            print(f"\n🔍 搜索相似视频...")
            query_url = video_urls[0]
            
            try:
                results = searcher.search_by_video(
                    query_video_source=query_url,
                    top_k=5,
                    similarity_threshold=0.7
                )
                
                print(f"查询URL: {query_url}")
                print(f"找到 {len(results)} 个相似视频:")
                
                for i, result in enumerate(results, 1):
                    print(f"  {i}. {result['video_name']}")
                    print(f"     相似度: {result['similarity']:.4f}")
                    print(f"     时长: {result['video_duration']:.2f}秒")
                    print(f"     路径: {result['video_path']}")
                    print()
            
            except Exception as e:
                print(f"搜索失败: {e}")
        
        # 比较视频
        if len(video_urls) >= 2:
            print(f"\n⚖️ 比较视频相似度...")
            try:
                comparison = searcher.compare_videos(video_urls[0], video_urls[1])
                print(f"视频1: {comparison['video1']}")
                print(f"视频2: {comparison['video2']}")
                print(f"相似度: {comparison['similarity']:.4f}")
                print(f"视频1帧数: {comparison['frames1']}")
                print(f"视频2帧数: {comparison['frames2']}")
            except Exception as e:
                print(f"比较失败: {e}")
        
        # 显示统计信息
        print(f"\n📊 数据库统计信息...")
        stats = searcher.get_database_stats()
        print(f"视频总数: {stats.get('row_count', 0)}")
        print(f"数据大小: {stats.get('data_size', 0)} 字节")
        
        print(f"\n🎉 URL示例完成！")
        
    except Exception as e:
        print(f"❌ 示例执行失败: {e}")
    
    finally:
        # 清理临时文件
        downloader.cleanup_temp_files()
        searcher.close()

def test_youtube_url():
    """测试YouTube URL（需要安装yt-dlp）"""
    print("\n🎬 YouTube视频测试")
    print("-" * 30)
    
    # 注意：YouTube URL需要特殊处理，可能需要登录或处理反爬虫机制
    youtube_urls = [
        # 添加一些公开的YouTube视频URL进行测试
        # "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    ]
    
    if not youtube_urls:
        print("请添加YouTube URL进行测试")
        return
    
    searcher = SimilaritySearch()
    try:
        for url in youtube_urls:
            print(f"处理YouTube视频: {url}")
            try:
                video_id = searcher.add_video(url)
                print(f"成功添加，ID: {video_id}")
            except Exception as e:
                print(f"添加失败: {e}")
    finally:
        searcher.close()

if __name__ == '__main__':
    url_example()
    test_youtube_url()

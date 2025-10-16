"""
视频指纹识别系统使用示例
"""
import os
import sys
import logging
from src.similarity_search import SimilaritySearch

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def example_usage():
    """使用示例"""
    print("视频指纹识别系统使用示例")
    print("=" * 50)
    
    # 创建相似度搜索器
    searcher = SimilaritySearch()
    
    try:
        # 示例1: 添加视频
        print("\n1. 添加视频到数据库")
        print("-" * 30)
        
        # 假设有一些视频文件
        video_files = [
            "sample1.mp4",
            "sample2.mp4", 
            "sample3.mp4"
        ]
        
        video_ids = []
        for video_file in video_files:
            if os.path.exists(video_file):
                try:
                    video_id = searcher.add_video(video_file)
                    video_ids.append(video_id)
                    print(f"✓ 添加视频: {video_file} (ID: {video_id})")
                except Exception as e:
                    print(f"✗ 添加失败: {video_file} - {e}")
            else:
                print(f"⚠ 文件不存在: {video_file}")
        
        if not video_ids:
            print("没有可用的视频文件，请将视频文件放在当前目录下")
            return
        
        # 示例2: 搜索相似视频
        print(f"\n2. 搜索相似视频")
        print("-" * 30)
        
        query_video = video_files[0]
        if os.path.exists(query_video):
            results = searcher.search_by_video(
                query_video_path=query_video,
                top_k=5,
                similarity_threshold=0.7
            )
            
            print(f"查询视频: {query_video}")
            print(f"找到 {len(results)} 个相似视频:")
            
            for i, result in enumerate(results, 1):
                print(f"  {i}. {result['video_name']}")
                print(f"     相似度: {result['similarity']:.4f}")
                print(f"     时长: {result['video_duration']:.2f}秒")
                print()
        else:
            print(f"查询视频不存在: {query_video}")
        
        # 示例3: 比较两个视频
        print(f"\n3. 比较视频相似度")
        print("-" * 30)
        
        if len(video_files) >= 2 and os.path.exists(video_files[0]) and os.path.exists(video_files[1]):
            comparison = searcher.compare_videos(video_files[0], video_files[1])
            print(f"视频1: {comparison['video1']}")
            print(f"视频2: {comparison['video2']}")
            print(f"相似度: {comparison['similarity']:.4f}")
            print(f"视频1帧数: {comparison['frames1']}")
            print(f"视频2帧数: {comparison['frames2']}")
        else:
            print("需要至少两个视频文件进行比较")
        
        # 示例4: 获取数据库统计信息
        print(f"\n4. 数据库统计信息")
        print("-" * 30)
        
        stats = searcher.get_database_stats()
        print(f"视频总数: {stats.get('row_count', 0)}")
        print(f"数据大小: {stats.get('data_size', 0)} 字节")
        
        # 示例5: 批量添加视频
        print(f"\n5. 批量添加视频")
        print("-" * 30)
        
        # 假设有一个视频目录
        video_directory = "videos"
        if os.path.exists(video_directory):
            print(f"扫描目录: {video_directory}")
            batch_ids = searcher.batch_add_videos([os.path.join(video_directory, f) for f in os.listdir(video_directory) 
                                                 if f.lower().endswith(('.mp4', '.avi', '.mov', '.mkv'))])
            print(f"批量添加完成，添加了 {len(batch_ids)} 个视频")
        else:
            print(f"视频目录不存在: {video_directory}")
        
        print(f"\n示例完成！")
    
    except Exception as e:
        logger.error(f"示例执行失败: {e}")
    
    finally:
        # 关闭连接
        searcher.close()

def create_sample_videos():
    """创建示例视频文件（仅用于演示）"""
    print("创建示例视频文件...")
    
    # 这里可以添加创建示例视频的代码
    # 由于需要视频处理库，这里只是示例
    print("请将您的视频文件放在当前目录下，支持格式: .mp4, .avi, .mov, .mkv")

if __name__ == '__main__':
    # 检查是否有视频文件
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv']
    has_videos = any(f.lower().endswith(ext) for f in os.listdir('.') for ext in video_extensions)
    
    if not has_videos:
        print("当前目录下没有找到视频文件")
        print("请将视频文件放在当前目录下，然后重新运行示例")
        create_sample_videos()
    else:
        example_usage()

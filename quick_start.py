"""
快速开始示例 - 展示如何使用视频指纹识别系统
"""
import os
from src.similarity_search import SimilaritySearch

def quick_start_example():
    """快速开始示例"""
    print("🎬 视频指纹识别系统 - 快速开始")
    print("=" * 50)
    
    # 创建搜索器
    searcher = SimilaritySearch()
    
    try:
        # 1. 检查是否有视频文件
        video_files = []
        for file in os.listdir('.'):
            if file.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
                video_files.append(file)
        
        if not video_files:
            print("❌ 当前目录没有找到视频文件")
            print("请将视频文件放在当前目录下，然后重新运行")
            return
        
        print(f"✅ 找到 {len(video_files)} 个视频文件")
        
        # 2. 添加视频到数据库
        print("\n📁 添加视频到数据库...")
        video_ids = []
        for video_file in video_files[:3]:  # 只处理前3个视频
            try:
                video_id = searcher.add_video(video_file)
                video_ids.append(video_id)
                print(f"  ✅ {video_file} -> ID: {video_id}")
            except Exception as e:
                print(f"  ❌ {video_file} -> 失败: {e}")
        
        if not video_ids:
            print("❌ 没有成功添加任何视频")
            return
        
        # 3. 搜索相似视频
        print(f"\n🔍 搜索相似视频...")
        query_video = video_files[0]
        results = searcher.search_by_video(query_video, top_k=5, similarity_threshold=0.7)
        
        print(f"查询视频: {query_video}")
        print(f"找到 {len(results)} 个相似视频:")
        for i, result in enumerate(results, 1):
            print(f"  {i}. {result['video_name']} (相似度: {result['similarity']:.4f})")
        
        # 4. 比较视频
        if len(video_files) >= 2:
            print(f"\n⚖️ 比较视频相似度...")
            comparison = searcher.compare_videos(video_files[0], video_files[1])
            print(f"  {video_files[0]} vs {video_files[1]}")
            print(f"  相似度: {comparison['similarity']:.4f}")
        
        # 5. 显示统计信息
        print(f"\n📊 数据库统计信息...")
        stats = searcher.get_database_stats()
        print(f"  视频总数: {stats.get('row_count', 0)}")
        print(f"  数据大小: {stats.get('data_size', 0)} 字节")
        
        print(f"\n🎉 示例完成！")
        
    except Exception as e:
        print(f"❌ 执行失败: {e}")
    
    finally:
        searcher.close()

if __name__ == '__main__':
    quick_start_example()

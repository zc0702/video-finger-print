"""
视频指纹识别系统主程序
"""
import os
import sys
import argparse
import logging
from typing import List
from src.similarity_search import SimilaritySearch
from config.config import Config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def add_video_command(args):
    """添加视频命令"""
    searcher = SimilaritySearch()
    try:
        video_id = searcher.add_video(args.video_source)
        print(f"成功添加视频，ID: {video_id}")
    except Exception as e:
        print(f"添加视频失败: {e}")
    finally:
        searcher.close()

def search_command(args):
    """搜索相似视频命令"""
    searcher = SimilaritySearch()
    try:
        results = searcher.search_by_video(
            query_video_source=args.query_video,
            top_k=args.top_k,
            similarity_threshold=args.threshold
        )
        
        if results:
            print(f"\n找到 {len(results)} 个相似视频:")
            print("-" * 80)
            for i, result in enumerate(results, 1):
                print(f"{i}. {result['video_name']}")
                print(f"   相似度: {result['similarity']:.4f}")
                print(f"   路径: {result['video_path']}")
                print(f"   时长: {result['video_duration']:.2f}秒")
                print(f"   帧数: {result['frame_count']}")
                print()
        else:
            print("未找到相似视频")
    
    except Exception as e:
        print(f"搜索失败: {e}")
    finally:
        searcher.close()

def compare_command(args):
    """比较视频命令"""
    searcher = SimilaritySearch()
    try:
        result = searcher.compare_videos(args.video1, args.video2)
        print(f"\n视频比较结果:")
        print("-" * 50)
        print(f"视频1: {result['video1']}")
        print(f"视频2: {result['video2']}")
        print(f"相似度: {result['similarity']:.4f}")
        print(f"视频1帧数: {result['frames1']}")
        print(f"视频2帧数: {result['frames2']}")
    
    except Exception as e:
        print(f"比较失败: {e}")
    finally:
        searcher.close()

def batch_add_command(args):
    """批量添加视频命令"""
    searcher = SimilaritySearch()
    try:
        # 从目录获取所有视频文件
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv']
        video_files = []
        
        for root, dirs, files in os.walk(args.directory):
            for file in files:
                if any(file.lower().endswith(ext) for ext in video_extensions):
                    video_files.append(os.path.join(root, file))
        
        if not video_files:
            print(f"在目录 {args.directory} 中未找到视频文件")
            return
        
        print(f"找到 {len(video_files)} 个视频文件，开始批量添加...")
        
        video_ids = searcher.batch_add_videos(video_files)
        
        print(f"成功添加 {len(video_ids)} 个视频")
        print(f"视频ID列表: {video_ids}")
    
    except Exception as e:
        print(f"批量添加失败: {e}")
    finally:
        searcher.close()

def stats_command(args):
    """统计信息命令"""
    searcher = SimilaritySearch()
    try:
        stats = searcher.get_database_stats()
        print(f"\n数据库统计信息:")
        print("-" * 30)
        print(f"视频总数: {stats.get('row_count', 0)}")
        print(f"数据大小: {stats.get('data_size', 0)} 字节")
    
    except Exception as e:
        print(f"获取统计信息失败: {e}")
    finally:
        searcher.close()

def demo_command(args):
    """演示命令"""
    print("视频指纹识别系统演示")
    print("=" * 50)
    
    # 检查是否有示例视频
    sample_videos = []
    for ext in ['.mp4', '.avi', '.mov']:
        for root, dirs, files in os.walk('.'):
            for file in files:
                if file.lower().endswith(ext):
                    sample_videos.append(os.path.join(root, file))
                    if len(sample_videos) >= 3:
                        break
            if len(sample_videos) >= 3:
                break
        if len(sample_videos) >= 3:
            break
    
    if len(sample_videos) < 2:
        print("未找到足够的示例视频文件，请将视频文件放在当前目录下")
        return
    
    searcher = SimilaritySearch()
    try:
        print(f"\n1. 添加视频到数据库...")
        video_ids = []
        for video in sample_videos[:3]:
            try:
                video_id = searcher.add_video(video)
                video_ids.append(video_id)
                print(f"   添加: {os.path.basename(video)} (ID: {video_id})")
            except Exception as e:
                print(f"   添加失败: {os.path.basename(video)} - {e}")
        
        if len(video_ids) < 2:
            print("视频数量不足，无法进行演示")
            return
        
        print(f"\n2. 搜索相似视频...")
        query_video = sample_videos[0]
        results = searcher.search_by_video(query_video, top_k=5)
        
        print(f"   查询视频: {os.path.basename(query_video)}")
        print(f"   找到 {len(results)} 个相似视频:")
        for i, result in enumerate(results, 1):
            print(f"   {i}. {result['video_name']} (相似度: {result['similarity']:.4f})")
        
        print(f"\n3. 比较视频相似度...")
        if len(sample_videos) >= 2:
            comparison = searcher.compare_videos(sample_videos[0], sample_videos[1])
            print(f"   {os.path.basename(sample_videos[0])} vs {os.path.basename(sample_videos[1])}")
            print(f"   相似度: {comparison['similarity']:.4f}")
        
        print(f"\n4. 数据库统计信息...")
        stats = searcher.get_database_stats()
        print(f"   视频总数: {stats.get('row_count', 0)}")
        print(f"   数据大小: {stats.get('data_size', 0)} 字节")
        
        print(f"\n演示完成！")
    
    except Exception as e:
        print(f"演示失败: {e}")
    finally:
        searcher.close()

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='视频指纹识别系统')
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 添加视频命令
    add_parser = subparsers.add_parser('add', help='添加视频到数据库')
    add_parser.add_argument('video_source', help='视频文件路径或URL')
    
    # 搜索命令
    search_parser = subparsers.add_parser('search', help='搜索相似视频')
    search_parser.add_argument('query_video', help='查询视频路径或URL')
    search_parser.add_argument('--top-k', type=int, default=10, help='返回结果数量')
    search_parser.add_argument('--threshold', type=float, help='相似度阈值')
    
    # 比较命令
    compare_parser = subparsers.add_parser('compare', help='比较两个视频')
    compare_parser.add_argument('video1', help='第一个视频路径或URL')
    compare_parser.add_argument('video2', help='第二个视频路径或URL')
    
    # 批量添加命令
    batch_parser = subparsers.add_parser('batch-add', help='批量添加视频')
    batch_parser.add_argument('directory', help='视频目录路径')
    
    # 统计命令
    stats_parser = subparsers.add_parser('stats', help='显示数据库统计信息')
    
    # 演示命令
    demo_parser = subparsers.add_parser('demo', help='运行演示')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # 执行对应命令
    if args.command == 'add':
        add_video_command(args)
    elif args.command == 'search':
        search_command(args)
    elif args.command == 'compare':
        compare_command(args)
    elif args.command == 'batch-add':
        batch_add_command(args)
    elif args.command == 'stats':
        stats_command(args)
    elif args.command == 'demo':
        demo_command(args)

if __name__ == '__main__':
    main()

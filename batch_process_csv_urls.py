"""
从CSV文件读取视频URL并批量处理
支持多种CSV格式，自动检测URL列
"""
import os
import sys
import csv
import time
import logging
from typing import List, Dict
from datetime import datetime
from collections import defaultdict
from tqdm import tqdm
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing
from threading import Lock

from src.batch_processing_base import BatchProcessingBase
from src.video_processor import VideoProcessor
from src.feature_extractor import FeatureExtractor
from src.milvus_client import MilvusClient
from src.logging_config import setup_batch_logging


class CSVVideoProcessor(BatchProcessingBase):
    """CSV视频URL批处理器"""
    
    def __init__(self, similarity_threshold: float = 0.90):
        """
        初始化处理器
        
        Args:
            similarity_threshold: 相似度阈值
        """
        super().__init__(similarity_threshold)
        
        self.video_processor = VideoProcessor()
        self.feature_extractor = FeatureExtractor()
        self.milvus_client = MilvusClient()
        
        # 扩展统计信息
        self.stats['video_details'] = []
        
        # 线程安全锁（用于多线程时保护共享资源）
        self._stats_lock = Lock()
        self._milvus_lock = Lock()
    
    def read_csv_file(self, csv_file: str, url_column: str = None, 
                     encoding: str = 'utf-8') -> List[Dict]:
        """
        读取CSV文件并提取视频URL
        
        Args:
            csv_file: CSV文件路径
            url_column: URL所在的列名（如果为None则自动检测）
            encoding: 文件编码
            
        Returns:
            包含URL和其他信息的字典列表
        """
        logging.info(f"开始读取CSV文件: {csv_file}")
        
        video_entries = []
        
        try:
            # 尝试不同的编码
            encodings = [encoding, 'utf-8', 'gbk', 'gb2312', 'utf-8-sig']
            file_content = None
            
            for enc in encodings:
                try:
                    with open(csv_file, 'r', encoding=enc) as f:
                        file_content = f.read()
                    logging.info(f"成功使用 {enc} 编码读取文件")
                    break
                except UnicodeDecodeError:
                    continue
            
            if file_content is None:
                raise ValueError("无法使用任何编码读取文件")
            
            # 解析CSV
            csv_reader = csv.DictReader(file_content.splitlines())
            
            # 获取列名
            fieldnames = csv_reader.fieldnames
            logging.info(f"CSV列名: {fieldnames}")
            
            # 自动检测URL列
            if url_column is None:
                url_column = self._detect_url_column(fieldnames)
                logging.info(f"自动检测到URL列: {url_column}")
            
            if url_column not in fieldnames:
                raise ValueError(f"指定的URL列 '{url_column}' 不存在。可用列: {fieldnames}")
            
            # 读取所有行
            for row_num, row in enumerate(csv_reader, start=2):
                url = row.get(url_column, '').strip()
                
                if url:
                    entry = {
                        'row_number': row_num,
                        'url': url,
                        'metadata': {k: v for k, v in row.items() if k != url_column}
                    }
                    video_entries.append(entry)
            
            self.stats['total_videos'] = len(video_entries)
            logging.info(f"成功读取 {len(video_entries)} 个视频URL")
            
            return video_entries
            
        except Exception as e:
            logging.error(f"读取CSV文件失败: {e}")
            raise
    
    def _detect_url_column(self, fieldnames: List[str]) -> str:
        """
        自动检测包含URL的列名
        
        Args:
            fieldnames: CSV列名列表
            
        Returns:
            URL列名
        """
        # 常见的URL列名
        url_keywords = ['url', 'link', 'video_url', 'video_link', 'address', 
                       '链接', '地址', '视频链接', 'src', 'source']
        
        # 精确匹配
        for field in fieldnames:
            if field.lower() in url_keywords:
                return field
        
        # 模糊匹配
        for field in fieldnames:
            for keyword in url_keywords:
                if keyword in field.lower():
                    return field
        
        # 如果没有匹配，返回第一列
        logging.warning(f"无法自动检测URL列，使用第一列: {fieldnames[0]}")
        return fieldnames[0]
    
    def process_video_from_url(self, entry: Dict) -> Dict:
        """
        处理单个URL的视频
        
        Args:
            entry: 包含URL和元数据的字典
            
        Returns:
            处理结果
        """
        url = entry.get('url', '')
        row_number = entry.get('row_number', 0)
        
        if not url:
            return {
                'success': False,
                'row_number': row_number,
                'url': url,
                'error': 'URL字段缺失或为空',
                'metadata': entry.get('metadata', {})
            }
        
        video_path = None
        is_temp_file = False
        
        try:
            logging.info(f"处理第 {row_number} 行: {url}")
            
            # 对于URL视频，先下载一次，然后复用本地文件
            if self.video_processor.downloader.is_url(url):
                logging.info(f"下载视频: {url}")
                video_path = self.video_processor.downloader.download_from_url(url)
                is_temp_file = True
            else:
                video_path = url
                is_temp_file = False
            
            # 获取视频信息（使用本地路径，避免重复下载）
            video_info = self.video_processor.get_video_info(video_path)
            
            # 提取视频帧（使用本地路径，避免重复下载）
            frames = self.video_processor.extract_frames(video_path)
            if not frames:
                raise ValueError("无法从视频中提取帧")
            
            # 提取特征向量
            feature_vector = self.feature_extractor.extract_video_features(frames)
            
            # 使用锁保护 Milvus 操作（线程安全）
            with self._milvus_lock:
                # 搜索相似视频（详细日志在 milvus_client 中输出）
                similar_videos = self.milvus_client.search_similar_videos(
                    query_vector=feature_vector,
                    top_k=5,
                    score_threshold=self.similarity_threshold
                )
                
                # 插入到数据库
                video_name = video_info.get('title', url.split('/')[-1])
                video_id = self.milvus_client.insert_video_fingerprint(
                    video_path=url,
                    video_name=video_name,
                    video_duration=video_info.get('duration', 0),
                    frame_count=len(frames),
                    feature_vector=feature_vector
                )
            
            result = {
                'success': True,
                'row_number': row_number,
                'video_id': video_id,
                'url': url,
                'video_name': video_name,
                'title': video_info.get('title', ''),
                'uploader': video_info.get('uploader', ''),
                'duration': video_info.get('duration', 0),
                'view_count': video_info.get('view_count', 0),
                'similar_videos': similar_videos,
                'metadata': entry.get('metadata', {})
            }
            
            return result
            
        except Exception as e:
            logging.error(f"处理第 {row_number} 行失败 {url}: {e}")
            return {
                'success': False,
                'row_number': row_number,
                'url': url,
                'error': str(e),
                'metadata': entry.get('metadata', {})
            }
        
        finally:
            # 清理临时文件
            if is_temp_file and video_path and os.path.exists(video_path):
                try:
                    os.remove(video_path)
                    logging.debug(f"已删除临时文件: {video_path}")
                except Exception as e:
                    logging.warning(f"删除临时文件失败 {video_path}: {e}")
    
    def batch_process_urls(self, video_entries: List[Dict], max_workers: int = None) -> None:
        """
        批量处理视频URL列表（支持多进程）
        
        Args:
            video_entries: 视频URL条目列表
            max_workers: 最大工作进程数，None表示使用CPU核心数
        """
        start_time = time.time()
        
        # 自动检测CPU核心数
        if max_workers is None:
            max_workers = max(1, multiprocessing.cpu_count() - 1)  # 留一个核心给系统
        
        logging.info(f"开始批量处理 {len(video_entries)} 个视频URL（使用 {max_workers} 个线程）")
        
        # 用于存储相似视频组
        similar_groups = defaultdict(list)
        video_id_to_info = {}
        
        if max_workers == 1:
            # 单进程模式（原有逻辑）
            with tqdm(total=len(video_entries), desc="处理视频URL") as pbar:
                for entry in video_entries:
                    result = self.process_video_from_url(entry)
                    self._collect_result(result, similar_groups, video_id_to_info)
                    pbar.update(1)
        else:
            # 多线程模式（I/O密集型任务，避免Milvus序列化问题）
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # 提交所有任务
                future_to_entry = {
                    executor.submit(self.process_video_from_url, entry): entry 
                    for entry in video_entries
                }
                
                # 使用进度条
                with tqdm(total=len(video_entries), desc="处理视频URL") as pbar:
                    for future in as_completed(future_to_entry):
                        try:
                            result = future.result()
                            self._collect_result(result, similar_groups, video_id_to_info)
                        except Exception as e:
                            entry = future_to_entry[future]
                            logging.error(f"处理失败 {entry.get('url', 'Unknown')}: {e}")
                            self.stats['failed'] += 1
                        finally:
                            pbar.update(1)
        
        # 构建相似视频簇（使用基类方法）
        self._build_similarity_clusters(similar_groups, video_id_to_info)
        
        self.stats['processing_time'] = time.time() - start_time
        logging.info(f"批量处理完成，耗时: {self.stats['processing_time']:.2f}秒")
    
    def _collect_result(self, result: Dict, similar_groups: defaultdict, video_id_to_info: Dict):
        """收集处理结果（线程安全）"""
        # 使用锁保护共享资源
        with self._stats_lock:
            if result.get('success', False):
                self.stats['processed'] += 1
                video_id = result.get('video_id')
                if not video_id:
                    logging.warning(f"结果缺少video_id字段: {result.get('url', 'Unknown')}")
                    return
                
                video_id_to_info[video_id] = result
                
                # 保存视频详情
                self.stats['video_details'].append({
                    'video_id': video_id,
                    'url': result.get('url', ''),
                    'title': result.get('title', ''),
                    'uploader': result.get('uploader', ''),
                    'duration': result.get('duration', 0),
                    'view_count': result.get('view_count', 0),
                    'row_number': result.get('row_number', 0),
                    'metadata': result.get('metadata', {})
                })
                
                # 检查相似视频
                similar_videos = result.get('similar_videos', [])
                if similar_videos:
                    for similar in similar_videos:
                        similar_id = similar.get('id')
                        if similar_id and similar_id != video_id:
                            similarity = similar.get('similarity', 0)
                            if similarity >= self.similarity_threshold:
                                similar_groups[video_id].append({
                                    'id': similar_id,
                                    'name': similar.get('video_name', ''),
                                    'path': similar.get('video_path', ''),
                                    'similarity': similarity
                                })
            else:
                self.stats['failed'] += 1
                self.stats['failed_videos'].append({
                    'row_number': result.get('row_number', 0),
                    'url': result.get('url', ''),
                    'error': result.get('error', 'Unknown error'),
                    'metadata': result.get('metadata', {})
                })
    
    # 重写基类方法，自定义视频组信息格式
    def _build_group_info(self, video_ids: List[int], video_id_to_info: Dict) -> List[Dict]:
        """构建视频组信息（CSV特定格式）"""
        group = []
        for vid in video_ids:
            info = video_id_to_info.get(vid, {})
            group.append({
                'id': vid,
                'url': info.get('url', 'Unknown'),
                'title': info.get('title', ''),
                'row_number': info.get('row_number', 0)
            })
        return group
    
    # 重写基类方法
    def _get_report_title(self) -> str:
        return "CSV视频URL批处理报告"
    
    def _get_report_prefix(self) -> str:
        return "csv_video"
    
    def _format_video_info(self, index: int, video: Dict) -> List[str]:
        """格式化视频信息（CSV特定格式）"""
        return [
            f"  {index}. CSV第{video.get('row_number', '?')}行 | ID: {video.get('id', '0')}",
            f"     URL: {video.get('url', video.get('path', 'Unknown'))}"
        ]
    
    def _format_failed_video(self, index: int, failed: Dict) -> List[str]:
        """格式化失败视频信息（CSV特定格式）"""
        return [
            f"{index}. CSV第{failed.get('row_number', '?')}行",
            f"   URL: {failed.get('url', failed.get('path', 'Unknown'))}",
            f"   错误: {failed.get('error', 'Unknown error')}"
        ]
    
    def export_results_json(self, output_file: str = None) -> str:
        """导出JSON结果（扩展版本，包含视频详情）"""
        if output_file is None:
            output_file = f"csv_video_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'statistics': {
                'total_videos': self.stats['total_videos'],
                'processed': self.stats['processed'],
                'failed': self.stats['failed'],
                'duplicates_found': self.stats['duplicates_found'],
                'duplicate_rate': (self.stats['duplicates_found'] / max(1, self.stats['processed']) * 100),
                'processing_time': self.stats['processing_time'],
                'similarity_threshold': self.similarity_threshold
            },
            'video_details': self.stats['video_details'],  # CSV特有：详细信息
            'similar_groups': self.stats['similar_groups'],
            'failed_videos': self.stats['failed_videos']
        }
        
        import json
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        logging.info(f"JSON结果已保存到: {output_file}")
        return output_file
    
    def export_duplicates_report(self, output_file: str = None) -> str:
        """
        导出专门的重复视频报告
        
        Args:
            output_file: 输出文件路径
            
        Returns:
            输出文件路径
        """
        if output_file is None:
            output_file = f"duplicates_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        lines = []
        lines.append("=" * 80)
        lines.append("重复视频详细报告")
        lines.append("=" * 80)
        lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"相似度阈值: {self.similarity_threshold * 100:.0f}%")
        lines.append("")
        
        # 统计信息
        lines.append("=" * 80)
        lines.append("统计摘要")
        lines.append("=" * 80)
        lines.append(f"处理视频总数: {self.stats['processed']}")
        lines.append(f"发现重复视频数: {self.stats['duplicates_found']}")
        lines.append(f"重复视频组数: {len(self.stats['similar_groups'])}")
        lines.append(f"重复率: {(self.stats['duplicates_found'] / max(1, self.stats['processed']) * 100):.2f}%")
        lines.append("")
        
        if not self.stats['similar_groups']:
            lines.append("未发现重复视频。")
        else:
            lines.append("=" * 80)
            lines.append("重复视频组详情")
            lines.append("=" * 80)
            lines.append("")
            
            for idx, group in enumerate(self.stats['similar_groups'], 1):
                lines.append(f"【组 {idx}】包含 {len(group)} 个相似视频")
                lines.append("━" * 80)
                
                for i, video in enumerate(group, 1):
                    video_id = video.get('id', 'Unknown')
                    url = video.get('url', video.get('path', 'Unknown'))
                    title = video.get('title', '')
                    row_num = video.get('row_number', '?')
                    similarity = video.get('similarity', 0)
                    
                    # 第一个视频不显示相似度（作为参考基准）
                    if i == 1:
                        lines.append(f"  {i}. [基准] CSV第{row_num}行 | ID: {video_id}")
                    else:
                        lines.append(f"  {i}. [相似度: {similarity:.2%}] CSV第{row_num}行 | ID: {video_id}")
                    
                    if title:
                        lines.append(f"     标题: {title}")
                    lines.append(f"     URL: {url}")
                    lines.append("")
                
                lines.append("")
        
        # 建议部分
        if self.stats['similar_groups']:
            lines.append("=" * 80)
            lines.append("处理建议")
            lines.append("=" * 80)
            
            total_duplicates = sum(len(group) - 1 for group in self.stats['similar_groups'])
            
            lines.append(f"✅ 可以考虑删除的视频数量: {total_duplicates} 个")
            lines.append(f"✅ 每组保留1个，可节省 {total_duplicates} 个视频的存储空间")
            lines.append("")
            lines.append("建议操作：")
            lines.append("1. 人工审核每组的第一个视频（基准视频）")
            lines.append("2. 确认其他视频确实为重复")
            lines.append("3. 保留质量最好的版本，删除其他重复视频")
            lines.append("")
        
        lines.append("=" * 80)
        lines.append("报告结束")
        lines.append("=" * 80)
        
        # 写入文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        logging.info(f"重复视频报告已保存到: {output_file}")
        return output_file
    
    def close(self):
        """关闭资源"""
        self.milvus_client.close()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='从CSV文件读取视频URL并批量处理',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例CSV格式:

方式1 - 只有URL列:
url
https://example.com/video1.mp4
https://example.com/video2.mp4

方式2 - 包含多列信息（推荐）:
video_id,title,url,category
1,视频标题1,https://example.com/video1.mp4,娱乐
2,视频标题2,https://example.com/video2.mp4,教育

使用示例:
  # 基本用法
  python batch_process_csv_urls.py videos.csv
  
  # 指定URL列名
  python batch_process_csv_urls.py videos.csv --url-column video_url
  
  # 指定相似度阈值
  python batch_process_csv_urls.py videos.csv --threshold 0.85
  
  # 指定文件编码
  python batch_process_csv_urls.py videos.csv --encoding gbk
        """
    )
    
    parser.add_argument('csv_file', help='CSV文件路径')
    parser.add_argument('--url-column', type=str, default=None,
                       help='URL所在的列名（不指定则自动检测）')
    parser.add_argument('--threshold', type=float, default=0.90,
                       help='相似度阈值 (0-1之间，默认0.90)')
    parser.add_argument('--encoding', type=str, default='utf-8',
                       help='CSV文件编码（默认utf-8）')
    parser.add_argument('--output', type=str,
                       help='输出报告文件路径')
    parser.add_argument('--workers', type=int, default=None,
                       help='并行处理的线程数（默认自动检测CPU核心数-1）')
    
    args = parser.parse_args()
    
    # 验证CSV文件
    if not os.path.isfile(args.csv_file):
        print(f"错误: CSV文件不存在: {args.csv_file}")
        sys.exit(1)
    
    # 设置日志
    setup_batch_logging('csv_video_batch')
    
    # 创建处理器
    processor = CSVVideoProcessor(similarity_threshold=args.threshold)
    
    try:
        # 确定使用的进程数
        if args.workers is None:
            workers = max(1, multiprocessing.cpu_count() - 1)
        else:
            workers = max(1, args.workers)
        
        print("\n" + "=" * 80)
        print("CSV视频URL批处理系统")
        print("=" * 80)
        print(f"CSV文件: {args.csv_file}")
        print(f"相似度阈值: {args.threshold * 100:.0f}%")
        print(f"文件编码: {args.encoding}")
        print(f"并行线程数: {workers} {'(自动检测)' if args.workers is None else ''}")
        print(f"CPU核心数: {multiprocessing.cpu_count()}")
        print("=" * 80 + "\n")
        
        # 读取CSV文件
        video_entries = processor.read_csv_file(
            args.csv_file,
            url_column=args.url_column,
            encoding=args.encoding
        )
        
        if not video_entries:
            print("CSV文件中没有找到视频URL")
            return
        
        print(f"\n找到 {len(video_entries)} 个视频URL")
        
        # 显示前几个URL预览
        print("\n前5个URL预览:")
        for i, entry in enumerate(video_entries[:5], 1):
            url = entry.get('url', '')
            row_num = entry.get('row_number', i)
            print(f"  {i}. 第{row_num}行: {url[:80]}...")
        
        if len(video_entries) > 5:
            print(f"  ... 还有 {len(video_entries)-5} 个URL")
        
        # 确认处理
        if len(video_entries) > 20:
            confirm = input(f"\n将处理 {len(video_entries)} 个视频URL，是否继续？(y/n): ")
            if confirm.lower() != 'y':
                print("已取消")
                return
        
        # 批量处理
        print("\n开始处理...")
        processor.batch_process_urls(video_entries, max_workers=workers)
        
        # 生成报告
        print("\n正在生成报告...")
        report = processor.generate_report(args.output)
        print("\n" + report)
        
        # 导出JSON
        json_file = processor.export_results_json()
        print(f"\nJSON结果文件: {json_file}")
        
        # 导出重复视频专门报告
        if processor.stats['similar_groups']:
            duplicates_file = processor.export_duplicates_report()
            print(f"重复视频报告: {duplicates_file}")
            print(f"\n✨ 发现 {len(processor.stats['similar_groups'])} 组重复视频，详见重复视频报告")
        else:
            print(f"\n✅ 未发现重复视频")
        
    except KeyboardInterrupt:
        print("\n\n用户中断处理")
    except Exception as e:
        logging.error(f"处理失败: {e}", exc_info=True)
        print(f"\n错误: {e}")
    finally:
        processor.close()
        print("\n处理完成")


if __name__ == '__main__':
    main()

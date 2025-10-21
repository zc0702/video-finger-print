"""
批处理基类
提供批量视频处理的公共功能
"""
import json
import logging
from typing import Dict, List, Any
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


class BatchProcessingBase:
    """批处理基类，提供公共功能"""
    
    def __init__(self, similarity_threshold: float = 0.90):
        """
        初始化批处理基类
        
        Args:
            similarity_threshold: 相似度阈值
        """
        self.similarity_threshold = similarity_threshold
        self.stats = {
            'total_videos': 0,
            'processed': 0,
            'failed': 0,
            'duplicates_found': 0,
            'processing_time': 0,
            'similar_groups': [],
            'failed_videos': []
        }
    
    def _build_similarity_clusters(
        self, 
        similar_groups: Dict[int, List[Dict]], 
        video_id_to_info: Dict[int, Any]
    ) -> None:
        """
        构建相似视频簇（使用并查集算法）
        
        Args:
            similar_groups: 相似视频组字典 {video_id: [similar_videos]}
            video_id_to_info: 视频ID到信息的映射
        """
        # 并查集实现
        parent = {}
        
        def find(x):
            if x not in parent:
                parent[x] = x
            if parent[x] != x:
                parent[x] = find(parent[x])
            return parent[x]
        
        def union(x, y):
            px, py = find(x), find(y)
            if px != py:
                parent[px] = py
        
        # 合并相似视频
        for video_id, similar_list in similar_groups.items():
            for similar in similar_list:
                union(video_id, similar['id'])
        
        # 构建簇
        clusters = defaultdict(list)
        for video_id in video_id_to_info.keys():
            root = find(video_id)
            clusters[root].append(video_id)
        
        # 过滤出包含2个以上视频的簇（即有重复的）
        self.stats['similar_groups'] = []
        for root, video_ids in clusters.items():
            if len(video_ids) > 1:
                group = self._build_group_info(video_ids, video_id_to_info)
                self.stats['similar_groups'].append(group)
                self.stats['duplicates_found'] += len(video_ids) - 1
        
        logger.info(f"找到 {len(self.stats['similar_groups'])} 个相似视频组")
    
    def _build_group_info(
        self, 
        video_ids: List[int], 
        video_id_to_info: Dict[int, Any]
    ) -> List[Dict]:
        """
        构建视频组信息
        
        Args:
            video_ids: 视频ID列表
            video_id_to_info: 视频信息映射
            
        Returns:
            视频组信息列表
        """
        # 子类可以重写此方法以自定义组信息格式
        group = []
        for vid in video_ids:
            info = video_id_to_info.get(vid, {})
            group.append({
                'id': vid,
                'path': info.get('path', info.get('url', 'Unknown')),
                'name': info.get('name', 'Unknown')
            })
        return group
    
    def generate_report_header(self) -> List[str]:
        """
        生成报告头部
        
        Returns:
            报告行列表
        """
        total_processed = self.stats['processed']
        duplicates = self.stats['duplicates_found']
        duplicate_rate = (duplicates / total_processed * 100) if total_processed > 0 else 0
        
        return [
            "=" * 80,
            f"{self._get_report_title()}",
            "=" * 80,
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "=" * 80,
            "总体统计",
            "=" * 80,
            f"视频总数: {self.stats['total_videos']}",
            f"成功处理: {self.stats['processed']}",
            f"处理失败: {self.stats['failed']}",
            f"处理耗时: {self.stats['processing_time']:.2f} 秒",
            f"平均每个视频: {self.stats['processing_time']/max(1, self.stats['processed']):.2f} 秒",
            "",
            "=" * 80,
            "重复检测结果",
            "=" * 80,
            f"相似度阈值: {self.similarity_threshold * 100:.0f}%",
            f"相似视频组: {len(self.stats['similar_groups'])} 个",
            f"重复视频数: {duplicates} 个",
            f"重复率: {duplicate_rate:.2f}%",
            "",
        ]
    
    def generate_similar_groups_section(self) -> List[str]:
        """
        生成相似视频组部分
        
        Returns:
            报告行列表
        """
        if not self.stats['similar_groups']:
            return []
        
        lines = [
            "=" * 80,
            "相似视频组详情",
            "=" * 80,
            ""
        ]
        
        for i, group in enumerate(self.stats['similar_groups'], 1):
            lines.append(f"\n【组 {i}】包含 {len(group)} 个相似视频:")
            lines.append("-" * 80)
            for j, video in enumerate(group, 1):
                lines.extend(self._format_video_info(j, video))
            lines.append("")
        
        return lines
    
    def generate_failed_videos_section(self) -> List[str]:
        """
        生成失败视频部分
        
        Returns:
            报告行列表
        """
        if not self.stats['failed_videos']:
            return []
        
        lines = [
            "=" * 80,
            "处理失败的视频",
            "=" * 80,
            ""
        ]
        
        for i, failed in enumerate(self.stats['failed_videos'], 1):
            lines.extend(self._format_failed_video(i, failed))
            lines.append("")
        
        return lines
    
    def generate_report(self, output_file: str = None) -> str:
        """
        生成完整报告
        
        Args:
            output_file: 输出文件路径
            
        Returns:
            报告内容
        """
        if output_file is None:
            output_file = f"{self._get_report_prefix()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        report_lines = []
        report_lines.extend(self.generate_report_header())
        report_lines.extend(self.generate_similar_groups_section())
        report_lines.extend(self.generate_failed_videos_section())
        
        report_lines.append("=" * 80)
        report_lines.append("报告结束")
        report_lines.append("=" * 80)
        
        report_content = "\n".join(report_lines)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info(f"报告已保存到: {output_file}")
        return report_content
    
    def export_results_json(self, output_file: str = None) -> str:
        """
        导出JSON结果
        
        Args:
            output_file: 输出文件路径
            
        Returns:
            JSON文件路径
        """
        if output_file is None:
            output_file = f"{self._get_report_prefix()}_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
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
            'similar_groups': self.stats['similar_groups'],
            'failed_videos': self.stats['failed_videos']
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"JSON结果已保存到: {output_file}")
        return output_file
    
    # 以下方法由子类实现
    
    def _get_report_title(self) -> str:
        """获取报告标题（子类实现）"""
        return "视频处理报告"
    
    def _get_report_prefix(self) -> str:
        """获取报告文件前缀（子类实现）"""
        return "video_report"
    
    def _format_video_info(self, index: int, video: Dict) -> List[str]:
        """格式化视频信息（子类可重写）"""
        return [
            f"  {index}. ID: {video['id']}",
            f"     名称: {video['name']}",
            f"     路径: {video['path']}"
        ]
    
    def _format_failed_video(self, index: int, failed: Dict) -> List[str]:
        """格式化失败视频信息（子类可重写）"""
        return [
            f"{index}. {failed.get('path', 'Unknown')}",
            f"   错误: {failed.get('error', 'Unknown error')}"
        ]


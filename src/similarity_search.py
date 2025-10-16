"""
相似度搜索模块
"""
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import logging
from src.milvus_client import MilvusClient
from src.video_processor import VideoProcessor
from src.feature_extractor import FeatureExtractor
from config.config import Config

logger = logging.getLogger(__name__)

class SimilaritySearch:
    """相似度搜索器"""
    
    def __init__(self):
        self.config = Config()
        self.milvus_client = MilvusClient()
        self.video_processor = VideoProcessor()
        self.feature_extractor = FeatureExtractor()
    
    def add_video(self, video_source: str) -> int:
        """
        添加视频到数据库（支持文件路径或URL）
        
        Args:
            video_source: 视频文件路径或URL
            
        Returns:
            视频ID
        """
        try:
            # 获取视频信息
            video_info = self.video_processor.get_video_info(video_source)
            
            # 提取视频帧
            frames = self.video_processor.extract_frames(video_source)
            if not frames:
                raise ValueError("无法从视频中提取帧")
            
            # 提取特征向量
            feature_vector = self.feature_extractor.extract_video_features(frames)
            
            # 确定视频名称
            if video_info.get('source_type') == 'url':
                video_name = video_info.get('title', video_source)
                video_path = video_info.get('url', video_source)
            else:
                video_name = video_source.split('/')[-1]
                video_path = video_source
            
            # 插入到数据库
            video_id = self.milvus_client.insert_video_fingerprint(
                video_path=video_path,
                video_name=video_name,
                video_duration=video_info['duration'],
                frame_count=len(frames),
                feature_vector=feature_vector
            )
            
            logger.info(f"成功添加视频: {video_name}, ID: {video_id}")
            return video_id
        
        except Exception as e:
            logger.error(f"添加视频失败: {e}")
            raise
    
    def search_by_video(self, query_video_source: str, 
                       top_k: int = 10, 
                       similarity_threshold: float = None) -> List[Dict[str, Any]]:
        """
        根据视频文件或URL搜索相似视频
        
        Args:
            query_video_source: 查询视频路径或URL
            top_k: 返回结果数量
            similarity_threshold: 相似度阈值
            
        Returns:
            相似视频列表
        """
        try:
            # 提取查询视频的特征
            frames = self.video_processor.extract_frames(query_video_source)
            if not frames:
                raise ValueError("无法从查询视频中提取帧")
            
            query_vector = self.feature_extractor.extract_video_features(frames)
            
            # 搜索相似视频
            similar_videos = self.milvus_client.search_similar_videos(
                query_vector=query_vector,
                top_k=top_k,
                score_threshold=similarity_threshold
            )
            
            return similar_videos
        
        except Exception as e:
            logger.error(f"搜索相似视频失败: {e}")
            raise
    
    def search_by_vector(self, query_vector: np.ndarray, 
                        top_k: int = 10, 
                        similarity_threshold: float = None) -> List[Dict[str, Any]]:
        """
        根据特征向量搜索相似视频
        
        Args:
            query_vector: 查询特征向量
            top_k: 返回结果数量
            similarity_threshold: 相似度阈值
            
        Returns:
            相似视频列表
        """
        try:
            similar_videos = self.milvus_client.search_similar_videos(
                query_vector=query_vector,
                top_k=top_k,
                score_threshold=similarity_threshold
            )
            
            return similar_videos
        
        except Exception as e:
            logger.error(f"搜索相似视频失败: {e}")
            raise
    
    def batch_add_videos(self, video_paths: List[str]) -> List[int]:
        """
        批量添加视频
        
        Args:
            video_paths: 视频路径列表
            
        Returns:
            视频ID列表
        """
        video_ids = []
        failed_videos = []
        
        for video_path in video_paths:
            try:
                video_id = self.add_video(video_path)
                video_ids.append(video_id)
                logger.info(f"成功添加视频: {video_path}")
            except Exception as e:
                logger.error(f"添加视频失败 {video_path}: {e}")
                failed_videos.append(video_path)
        
        if failed_videos:
            logger.warning(f"以下视频添加失败: {failed_videos}")
        
        return video_ids
    
    def get_video_info(self, video_id: int) -> Optional[Dict[str, Any]]:
        """
        获取视频信息
        
        Args:
            video_id: 视频ID
            
        Returns:
            视频信息字典
        """
        return self.milvus_client.get_video_by_id(video_id)
    
    def delete_video(self, video_id: int) -> bool:
        """
        删除视频
        
        Args:
            video_id: 视频ID
            
        Returns:
            是否删除成功
        """
        return self.milvus_client.delete_video(video_id)
    
    def get_database_stats(self) -> Dict[str, Any]:
        """
        获取数据库统计信息
        
        Returns:
            统计信息字典
        """
        return self.milvus_client.get_collection_stats()
    
    def find_duplicate_videos(self, similarity_threshold: float = 0.95) -> List[List[Dict[str, Any]]]:
        """
        查找重复视频
        
        Args:
            similarity_threshold: 相似度阈值
            
        Returns:
            重复视频组列表
        """
        try:
            # 获取所有视频
            stats = self.get_database_stats()
            total_videos = stats.get('row_count', 0)
            
            if total_videos == 0:
                return []
            
            # 这里需要实现一个更复杂的算法来查找重复视频
            # 由于 Milvus 的限制，我们需要分批处理
            duplicate_groups = []
            processed_videos = set()
            
            # 获取所有视频的ID和特征（这里简化处理）
            # 在实际应用中，可能需要更复杂的实现
            
            logger.info(f"开始查找重复视频，阈值: {similarity_threshold}")
            return duplicate_groups
        
        except Exception as e:
            logger.error(f"查找重复视频失败: {e}")
            return []
    
    def compare_videos(self, video1_source: str, video2_source: str) -> Dict[str, Any]:
        """
        比较两个视频的相似度（支持文件路径或URL）
        
        Args:
            video1_source: 第一个视频路径或URL
            video2_source: 第二个视频路径或URL
            
        Returns:
            比较结果字典
        """
        try:
            # 提取两个视频的特征
            frames1 = self.video_processor.extract_frames(video1_source)
            frames2 = self.video_processor.extract_frames(video2_source)
            
            if not frames1 or not frames2:
                raise ValueError("无法从视频中提取帧")
            
            features1 = self.feature_extractor.extract_video_features(frames1)
            features2 = self.feature_extractor.extract_video_features(frames2)
            
            # 计算相似度
            similarity = self._calculate_similarity(features1, features2)
            
            return {
                'video1': video1_source,
                'video2': video2_source,
                'similarity': similarity,
                'frames1': len(frames1),
                'frames2': len(frames2)
            }
        
        except Exception as e:
            logger.error(f"比较视频失败: {e}")
            raise
    
    def _calculate_similarity(self, features1: np.ndarray, features2: np.ndarray) -> float:
        """
        计算两个特征向量的相似度
        
        Args:
            features1: 第一个特征向量
            features2: 第二个特征向量
            
        Returns:
            相似度分数
        """
        # 使用余弦相似度
        dot_product = np.dot(features1, features2)
        norm1 = np.linalg.norm(features1)
        norm2 = np.linalg.norm(features2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        similarity = dot_product / (norm1 * norm2)
        return float(similarity)
    
    def close(self):
        """关闭连接"""
        self.milvus_client.close()

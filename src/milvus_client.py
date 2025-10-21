"""
Milvus 客户端模块
"""
from pymilvus import connections, Collection, CollectionSchema, FieldSchema, DataType, utility
import numpy as np
from typing import List, Dict, Any, Optional
import logging
from config.config import Config

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MilvusClient:
    """Milvus 客户端"""
    
    def __init__(self):
        self.config = Config()
        self.collection = None
        self._connect()
        self._create_collection()
    
    def _connect(self):
        """连接到 Milvus 服务器"""
        try:
            # 检查是否使用 Milvus Lite（本地文件路径）
            if self.config.MILVUS_HOST.endswith('.db') or '/' in self.config.MILVUS_HOST or '\\' in self.config.MILVUS_HOST:
                # 使用 Milvus Lite（本地文件模式）
                connections.connect(
                    alias="default",
                    uri=self.config.MILVUS_HOST
                )
                logger.info(f"成功连接到 Milvus Lite: {self.config.MILVUS_HOST}")
            else:
                # 使用远程 Milvus 服务器
                connections.connect(
                    alias="default",
                    host=self.config.MILVUS_HOST,
                    port=self.config.MILVUS_PORT,
                    user=self.config.MILVUS_USER,
                    password=self.config.MILVUS_PASSWORD
                )
                logger.info("成功连接到 Milvus 服务器")
        except Exception as e:
            logger.error(f"连接 Milvus 服务器失败: {e}")
            raise
    
    def _create_collection(self):
        """创建集合"""
        try:
            # 检查集合是否已存在
            if utility.has_collection(self.config.COLLECTION_NAME):
                logger.info(f"集合 {self.config.COLLECTION_NAME} 已存在")
                self.collection = Collection(self.config.COLLECTION_NAME)
            else:
                # 定义字段模式
                fields = [
                    FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
                    FieldSchema(name="video_path", dtype=DataType.VARCHAR, max_length=500),
                    FieldSchema(name="video_name", dtype=DataType.VARCHAR, max_length=200),
                    FieldSchema(name="video_duration", dtype=DataType.FLOAT),
                    FieldSchema(name="frame_count", dtype=DataType.INT64),
                    FieldSchema(name="feature_vector", dtype=DataType.FLOAT_VECTOR, dim=self.config.DIMENSION)
                ]
                
                # 创建集合模式
                schema = CollectionSchema(
                    fields=fields,
                    description="视频指纹特征集合",
                    enable_dynamic_field=True
                )
                
                # 创建集合
                self.collection = Collection(
                    name=self.config.COLLECTION_NAME,
                    schema=schema,
                    using='default',
                    shards_num=2
                )
                
                # 创建索引
                self._create_index()
                logger.info(f"成功创建集合 {self.config.COLLECTION_NAME}")
        
        except Exception as e:
            logger.error(f"创建集合失败: {e}")
            raise
    
    def _create_index(self):
        """创建索引"""
        try:
            # 为向量字段创建索引
            index_params = {
                "metric_type": self.config.METRIC_TYPE,
                "index_type": "IVF_FLAT",
                "params": {"nlist": 1024}
            }
            
            self.collection.create_index(
                field_name="feature_vector",
                index_params=index_params
            )
            
            # Milvus Lite 不支持标量字段索引，跳过
            # 标量字段会自动支持查询，无需显式创建索引
            
            logger.info("成功创建索引")
        except Exception as e:
            logger.error(f"创建索引失败: {e}")
            raise
    
    def insert_video_fingerprint(self, video_path: str, video_name: str, 
                               video_duration: float, frame_count: int, 
                               feature_vector: np.ndarray) -> int:
        """
        插入视频指纹
        
        Args:
            video_path: 视频文件路径
            video_name: 视频名称
            video_duration: 视频时长
            frame_count: 帧数
            feature_vector: 特征向量
            
        Returns:
            插入记录的ID
        """
        try:
            # 确保特征向量维度正确
            if len(feature_vector) != self.config.DIMENSION:
                raise ValueError(f"特征向量维度不匹配，期望 {self.config.DIMENSION}，实际 {len(feature_vector)}")
            
            # 准备数据
            data = [
                [video_path],
                [video_name],
                [video_duration],
                [frame_count],
                [feature_vector.tolist()]
            ]
            
            # 插入数据
            insert_result = self.collection.insert(data)
            self.collection.flush()
            
            logger.info(f"成功插入视频指纹: {video_name}")
            return insert_result.primary_keys[0]
        
        except Exception as e:
            logger.error(f"插入视频指纹失败: {e}")
            raise
    
    def search_similar_videos(self, query_vector: np.ndarray, 
                            top_k: int = 10, 
                            score_threshold: float = None) -> List[Dict[str, Any]]:
        """
        搜索相似视频
        
        Args:
            query_vector: 查询向量
            top_k: 返回结果数量
            score_threshold: 相似度阈值
            
        Returns:
            相似视频列表
        """
        try:
            # 确保集合已加载
            if not self.collection.has_index():
                raise ValueError("集合没有索引，请先创建索引")
            
            # 加载集合到内存
            self.collection.load()
            
            # 搜索参数
            search_params = {
                "metric_type": self.config.METRIC_TYPE,
                "params": {"nprobe": 10}
            }
            
            # 执行搜索
            results = self.collection.search(
                data=[query_vector.tolist()],
                anns_field="feature_vector",
                param=search_params,
                limit=top_k,
                output_fields=["video_path", "video_name", "video_duration", "frame_count"]
            )
            
            # 处理结果
            all_videos = []  # 所有搜索结果
            similar_videos = []  # 满足阈值的相似视频
            
            for hits in results:
                for hit in hits:
                    # 计算相似度分数（L2距离转换为相似度）
                    distance = hit.distance
                    similarity = 1.0 / (1.0 + distance)  # 将距离转换为相似度
                    
                    video_info = {
                        'id': hit.id,
                        'video_path': hit.entity.get('video_path'),
                        'video_name': hit.entity.get('video_name'),
                        'video_duration': hit.entity.get('video_duration'),
                        'frame_count': hit.entity.get('frame_count'),
                        'similarity': similarity,
                        'distance': distance
                    }
                    
                    all_videos.append(video_info)
                    
                    # 应用阈值过滤
                    if score_threshold is None:
                        score_threshold = self.config.SIMILARITY_THRESHOLD
                    
                    if similarity >= score_threshold:
                        similar_videos.append(video_info)
            
            # 按相似度排序
            all_videos.sort(key=lambda x: x['similarity'], reverse=True)
            similar_videos.sort(key=lambda x: x['similarity'], reverse=True)
            
            # 详细日志：显示所有搜索结果
            if all_videos:
                logger.info(f"搜索返回 {len(all_videos)} 个结果，其中 {len(similar_videos)} 个满足阈值 {score_threshold:.0%}：")
                for idx, video in enumerate(all_videos, 1):
                    match_status = "✓" if video['similarity'] >= score_threshold else "✗"
                    video_url = video.get('video_path', 'Unknown')
                    # 截断过长的URL，只显示前80个字符
                    if len(video_url) > 80:
                        video_url = video_url[:77] + "..."
                    logger.info(f"  {match_status} {idx}. ID: {video['id']} | 相似度: {video['similarity']:.2%} | URL: {video_url}")
            else:
                logger.info(f"未找到任何相似视频")
            
            return similar_videos
        
        except Exception as e:
            logger.error(f"搜索相似视频失败: {e}")
            raise
    
    def get_video_by_id(self, video_id: int) -> Optional[Dict[str, Any]]:
        """
        根据ID获取视频信息
        
        Args:
            video_id: 视频ID
            
        Returns:
            视频信息字典
        """
        try:
            self.collection.load()
            
            results = self.collection.query(
                expr=f"id == {video_id}",
                output_fields=["video_path", "video_name", "video_duration", "frame_count"]
            )
            
            if results:
                return results[0]
            return None
        
        except Exception as e:
            logger.error(f"获取视频信息失败: {e}")
            raise
    
    def delete_video(self, video_id: int) -> bool:
        """
        删除视频记录
        
        Args:
            video_id: 视频ID
            
        Returns:
            是否删除成功
        """
        try:
            self.collection.delete(expr=f"id == {video_id}")
            self.collection.flush()
            logger.info(f"成功删除视频记录: {video_id}")
            return True
        
        except Exception as e:
            logger.error(f"删除视频记录失败: {e}")
            return False
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        获取集合统计信息
        
        Returns:
            统计信息字典
        """
        try:
            # 新版本使用 num_entities 属性
            self.collection.load()
            row_count = self.collection.num_entities
            return {
                'row_count': row_count,
                'data_size': 0  # Milvus Lite 不提供数据大小信息
            }
        except Exception as e:
            logger.error(f"获取集合统计信息失败: {e}")
            return {'row_count': 0, 'data_size': 0}
    
    def close(self):
        """关闭连接"""
        try:
            connections.disconnect("default")
            logger.info("已断开 Milvus 连接")
        except Exception as e:
            logger.error(f"断开连接失败: {e}")

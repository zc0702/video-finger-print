"""
配置文件
"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    """配置类"""
    
    # Milvus 配置
    MILVUS_HOST = os.getenv('MILVUS_HOST', 'localhost')
    MILVUS_PORT = int(os.getenv('MILVUS_PORT', '19530'))
    MILVUS_USER = os.getenv('MILVUS_USER', 'root')
    MILVUS_PASSWORD = os.getenv('MILVUS_PASSWORD', 'Milvus')
    
    # 集合配置
    COLLECTION_NAME = os.getenv('COLLECTION_NAME', 'video_fingerprints')
    DIMENSION = int(os.getenv('DIMENSION', '512'))
    METRIC_TYPE = os.getenv('METRIC_TYPE', 'L2')
    
    # 相似度阈值
    SIMILARITY_THRESHOLD = float(os.getenv('SIMILARITY_THRESHOLD', '0.8'))
    
    # 视频处理配置
    FRAME_INTERVAL = 15  # 每15帧提取一次特征（约每0.5秒1帧，30fps视频）
    MIN_FRAMES = 5       # 最少提取帧数
    MAX_FRAMES = 100     # 最大提取帧数
    IMAGE_SIZE = (224, 224)  # 图像尺寸

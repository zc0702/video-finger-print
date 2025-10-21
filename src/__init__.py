"""
视频指纹识别系统核心模块

提供视频处理、特征提取、相似度搜索等核心功能。
"""

from src.video_processor import VideoProcessor
from src.feature_extractor import FeatureExtractor
from src.milvus_client import MilvusClient
from src.similarity_search import SimilaritySearch
from src.video_downloader import VideoDownloader
from src.batch_processing_base import BatchProcessingBase
from src.logging_config import setup_logging, get_logger

__version__ = "1.0.0"
__author__ = "Video Fingerprint Team"

__all__ = [
    'VideoProcessor',
    'FeatureExtractor',
    'MilvusClient',
    'SimilaritySearch',
    'VideoDownloader',
    'BatchProcessingBase',
    'setup_logging',
    'get_logger',
]


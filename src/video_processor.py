"""
视频处理模块
"""
import cv2
import numpy as np
from typing import List, Tuple, Union
import os
from config.config import Config
from src.video_downloader import VideoDownloader

class VideoProcessor:
    """视频处理器"""
    
    def __init__(self):
        self.config = Config()
        self.downloader = VideoDownloader()
    
    def extract_frames(self, video_source: Union[str, np.ndarray]) -> List[np.ndarray]:
        """
        从视频中提取帧（支持文件路径或URL）
        
        Args:
            video_source: 视频文件路径或URL
            
        Returns:
            提取的帧列表
        """
        # 检查是否为URL
        if isinstance(video_source, str) and self.downloader.is_url(video_source):
            # 从URL下载视频
            video_path = self.downloader.download_from_url(video_source)
            temp_file = True
        else:
            # 使用本地文件路径
            video_path = video_source
            temp_file = False
        
        try:
            if not os.path.exists(video_path):
                raise FileNotFoundError(f"视频文件不存在: {video_path}")
            
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise ValueError(f"无法打开视频文件: {video_path}")
            
            frames = []
            frame_count = 0
            extracted_count = 0
            
            while cap.isOpened() and extracted_count < self.config.MAX_FRAMES:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # 每隔指定帧数提取一帧
                if frame_count % self.config.FRAME_INTERVAL == 0:
                    # 调整图像尺寸
                    frame = cv2.resize(frame, self.config.IMAGE_SIZE)
                    frames.append(frame)
                    extracted_count += 1
                
                frame_count += 1
            
            cap.release()
            return frames
        
        finally:
            # 如果是临时文件，下载完成后删除
            if temp_file and os.path.exists(video_path):
                try:
                    os.remove(video_path)
                except:
                    pass
    
    def get_video_info(self, video_source: Union[str, np.ndarray]) -> dict:
        """
        获取视频信息（支持文件路径或URL）
        
        Args:
            video_source: 视频文件路径或URL
            
        Returns:
            视频信息字典
        """
        # 检查是否为URL
        if isinstance(video_source, str) and self.downloader.is_url(video_source):
            # 从URL获取视频信息
            url_info = self.downloader.get_video_info_from_url(video_source)
            
            # 下载视频获取详细信息
            video_path = self.downloader.download_from_url(video_source)
            temp_file = True
        else:
            # 使用本地文件路径
            video_path = video_source
            temp_file = False
            url_info = {}
        
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise ValueError(f"无法打开视频文件: {video_path}")
            
            info = {
                'fps': cap.get(cv2.CAP_PROP_FPS),
                'frame_count': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
                'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                'duration': cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS)
            }
            
            # 合并URL信息
            if url_info:
                info.update({
                    'title': url_info.get('title', ''),
                    'uploader': url_info.get('uploader', ''),
                    'view_count': url_info.get('view_count', 0),
                    'url': url_info.get('url', ''),
                    'source_type': 'url'
                })
            else:
                info['source_type'] = 'file'
            
            cap.release()
            return info
        
        finally:
            # 如果是临时文件，处理完成后删除
            if temp_file and os.path.exists(video_path):
                try:
                    os.remove(video_path)
                except:
                    pass

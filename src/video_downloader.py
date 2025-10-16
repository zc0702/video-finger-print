"""
视频下载器模块 - 支持从URL下载视频
"""
import os
import tempfile
import requests
import yt_dlp
from typing import Optional, Dict, Any
import logging
from urllib.parse import urlparse
import time

logger = logging.getLogger(__name__)

class VideoDownloader:
    """视频下载器"""
    
    def __init__(self, download_dir: str = "temp_videos"):
        """
        初始化下载器
        
        Args:
            download_dir: 下载目录
        """
        self.download_dir = download_dir
        self._ensure_download_dir()
    
    def _ensure_download_dir(self):
        """确保下载目录存在"""
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)
    
    def is_url(self, path: str) -> bool:
        """
        检查是否为URL
        
        Args:
            path: 路径或URL
            
        Returns:
            是否为URL
        """
        try:
            result = urlparse(path)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    def download_from_url(self, url: str, filename: Optional[str] = None) -> str:
        """
        从URL下载视频
        
        Args:
            url: 视频URL
            filename: 保存的文件名（可选）
            
        Returns:
            下载后的文件路径
        """
        try:
            # 生成文件名
            if not filename:
                filename = self._generate_filename(url)
            
            filepath = os.path.join(self.download_dir, filename)
            
            # 使用 yt-dlp 下载视频
            ydl_opts = {
                'outtmpl': filepath,
                'format': 'best[height<=720]',  # 限制分辨率以提高处理速度
                'noplaylist': True,
                'extract_flat': False,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # 获取视频信息
                info = ydl.extract_info(url, download=False)
                title = info.get('title', 'unknown')
                duration = info.get('duration', 0)
                
                logger.info(f"开始下载视频: {title}")
                logger.info(f"视频时长: {duration}秒")
                
                # 下载视频
                ydl.download([url])
            
            # 检查文件是否下载成功
            if os.path.exists(filepath):
                logger.info(f"视频下载成功: {filepath}")
                return filepath
            else:
                raise Exception("视频下载失败，文件不存在")
        
        except Exception as e:
            logger.error(f"下载视频失败 {url}: {e}")
            raise
    
    def download_with_requests(self, url: str, filename: Optional[str] = None) -> str:
        """
        使用 requests 下载视频（适用于直接视频链接）
        
        Args:
            url: 视频URL
            filename: 保存的文件名（可选）
            
        Returns:
            下载后的文件路径
        """
        try:
            if not filename:
                filename = self._generate_filename(url)
            
            filepath = os.path.join(self.download_dir, filename)
            
            # 发送请求
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, stream=True)
            response.raise_for_status()
            
            # 获取文件大小
            total_size = int(response.headers.get('content-length', 0))
            
            # 下载文件
            with open(filepath, 'wb') as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # 显示下载进度
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            print(f"\r下载进度: {percent:.1f}%", end='', flush=True)
            
            print()  # 换行
            logger.info(f"视频下载成功: {filepath}")
            return filepath
        
        except Exception as e:
            logger.error(f"下载视频失败 {url}: {e}")
            raise
    
    def _generate_filename(self, url: str) -> str:
        """
        生成文件名
        
        Args:
            url: 视频URL
            
        Returns:
            文件名
        """
        # 从URL中提取文件名
        parsed = urlparse(url)
        filename = os.path.basename(parsed.path)
        
        # 如果没有扩展名，添加默认扩展名
        if not filename or '.' not in filename:
            filename = f"video_{int(time.time())}.mp4"
        
        # 确保文件名安全
        filename = "".join(c for c in filename if c.isalnum() or c in "._-")
        
        return filename
    
    def get_video_info_from_url(self, url: str) -> Dict[str, Any]:
        """
        获取视频信息（不下载）
        
        Args:
            url: 视频URL
            
        Returns:
            视频信息字典
        """
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                return {
                    'title': info.get('title', 'Unknown'),
                    'duration': info.get('duration', 0),
                    'uploader': info.get('uploader', 'Unknown'),
                    'view_count': info.get('view_count', 0),
                    'description': info.get('description', ''),
                    'upload_date': info.get('upload_date', ''),
                    'url': url
                }
        
        except Exception as e:
            logger.error(f"获取视频信息失败 {url}: {e}")
            return {
                'title': 'Unknown',
                'duration': 0,
                'uploader': 'Unknown',
                'view_count': 0,
                'description': '',
                'upload_date': '',
                'url': url
            }
    
    def cleanup_temp_files(self):
        """清理临时文件"""
        try:
            for file in os.listdir(self.download_dir):
                file_path = os.path.join(self.download_dir, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            logger.info("临时文件清理完成")
        except Exception as e:
            logger.error(f"清理临时文件失败: {e}")
    
    def get_temp_file_path(self, url: str) -> str:
        """
        获取临时文件路径（不下载）
        
        Args:
            url: 视频URL
            
        Returns:
            临时文件路径
        """
        filename = self._generate_filename(url)
        return os.path.join(self.download_dir, filename)

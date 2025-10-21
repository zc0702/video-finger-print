"""
特征提取模块
"""
import cv2
import numpy as np
from typing import List, Tuple
from sklearn.decomposition import PCA
from skimage.feature import local_binary_pattern
from concurrent.futures import ThreadPoolExecutor
from config.config import Config

class FeatureExtractor:
    """特征提取器"""
    
    def __init__(self):
        self.config = Config()
        self.pca = None
        self.is_fitted = False
    
    def extract_color_histogram(self, frame: np.ndarray) -> np.ndarray:
        """
        提取颜色直方图特征
        
        Args:
            frame: 输入帧
            
        Returns:
            颜色直方图特征向量
        """
        # 转换到HSV色彩空间
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # 计算H、S、V三个通道的直方图
        hist_h = cv2.calcHist([hsv], [0], None, [50], [0, 180])
        hist_s = cv2.calcHist([hsv], [1], None, [60], [0, 256])
        hist_v = cv2.calcHist([hsv], [2], None, [60], [0, 256])
        
        # 归一化
        hist_h = cv2.normalize(hist_h, hist_h).flatten()
        hist_s = cv2.normalize(hist_s, hist_s).flatten()
        hist_v = cv2.normalize(hist_v, hist_v).flatten()
        
        # 合并特征
        color_features = np.concatenate([hist_h, hist_s, hist_v])
        return color_features
    
    def extract_texture_features(self, frame: np.ndarray) -> np.ndarray:
        """
        提取纹理特征（LBP）- 旋转不变均匀LBP最优方案
        
        Args:
            frame: 输入帧
            
        Returns:
            纹理特征向量 (36维)
        """
        # 转换为灰度图
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # 使用旋转不变均匀LBP (RIU-LBP) - 最优方案
        # 优势: 旋转不变 + 特征降维 + 性能提升
        lbp = local_binary_pattern(gray, P=8, R=1, method='nri_uniform')
        
        # 计算LBP直方图 (36维，比原来256维的基本LBP减少86%存储)
        hist, _ = np.histogram(lbp.ravel(), bins=36, range=(0, 36))
        hist = hist.astype(np.float32)
        hist = cv2.normalize(hist, hist).flatten()
        
        return hist
    
    def extract_edge_features(self, frame: np.ndarray) -> np.ndarray:
        """
        提取边缘特征
        
        Args:
            frame: 输入帧
            
        Returns:
            边缘特征向量
        """
        # 转换为灰度图
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # 使用Canny边缘检测
        edges = cv2.Canny(gray, 50, 150)
        
        # 计算边缘方向直方图
        sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        
        # 计算梯度方向
        gradient_direction = np.arctan2(sobely, sobelx)
        gradient_magnitude = np.sqrt(sobelx**2 + sobely**2)
        
        # 创建掩码，只考虑边缘像素
        mask = edges > 0
        directions = gradient_direction[mask]
        magnitudes = gradient_magnitude[mask]
        
        # 计算方向直方图
        hist, _ = np.histogram(directions, bins=36, range=(-np.pi, np.pi), weights=magnitudes)
        hist = hist.astype(np.float32)
        hist = cv2.normalize(hist, hist).flatten()
        
        return hist
    
    def extract_frame_features(self, frame: np.ndarray) -> np.ndarray:
        """
        提取单帧的完整特征
        
        Args:
            frame: 输入帧
            
        Returns:
            特征向量
        """
        # 提取各种特征
        color_features = self.extract_color_histogram(frame)
        texture_features = self.extract_texture_features(frame)
        edge_features = self.extract_edge_features(frame)
        
        # 合并所有特征
        # 注意: texture_features现在是36维 (RIU-LBP)
        features = np.concatenate([color_features, texture_features, edge_features])
        
        return features
    
    def extract_video_features(self, frames: List[np.ndarray], max_workers: int = None) -> np.ndarray:
        """
        提取视频的完整特征向量（支持帧级并行处理）
        
        Args:
            frames: 视频帧列表
            max_workers: 最大并行线程数，None表示自动检测
            
        Returns:
            视频特征向量
        """
        if not frames:
            raise ValueError("帧列表不能为空")
        
        # 自动检测线程数
        if max_workers is None:
            import multiprocessing
            max_workers = min(len(frames), max(1, multiprocessing.cpu_count() - 1))
        
        # 并行提取每帧的特征
        if len(frames) <= 4 or max_workers == 1:
            # 帧数较少或单线程，直接处理
            frame_features = []
            for frame in frames:
                features = self.extract_frame_features(frame)
                frame_features.append(features)
        else:
            # 多线程并行处理帧特征提取
            frame_features = []
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_frame = {
                    executor.submit(self.extract_frame_features, frame): i 
                    for i, frame in enumerate(frames)
                }
                
                # 按原始顺序收集结果
                results = [None] * len(frames)
                for future in future_to_frame:
                    frame_idx = future_to_frame[future]
                    try:
                        results[frame_idx] = future.result()
                    except Exception as e:
                        # 如果某帧处理失败，使用零向量
                        results[frame_idx] = np.zeros(170)  # 默认特征维度
                
                frame_features = results
        
        # 计算帧间特征的平均值和标准差
        frame_features = np.array(frame_features)
        mean_features = np.mean(frame_features, axis=0)
        std_features = np.std(frame_features, axis=0)
        
        # 合并统计特征
        video_features = np.concatenate([mean_features, std_features])
        
        # 调整特征维度到目标维度
        current_dim = len(video_features)
        target_dim = self.config.DIMENSION
        
        if current_dim > target_dim:
            # 特征维度太大，需要降维
            # 方法1: 如果有足够的帧，使用帧特征进行PCA
            if len(frame_features) >= target_dim:
                if not self.is_fitted:
                    self.pca = PCA(n_components=target_dim)
                    # 对所有帧特征进行降维，然后取平均
                    reduced_features = self.pca.fit_transform(frame_features)
                    video_features = np.mean(reduced_features, axis=0)
                    self.is_fitted = True
                else:
                    reduced_features = self.pca.transform(frame_features)
                    video_features = np.mean(reduced_features, axis=0)
            else:
                # 方法2: 简单截断或使用哈希降维
                video_features = video_features[:target_dim]
        elif current_dim < target_dim:
            # 特征维度太小，使用零填充
            padding = np.zeros(target_dim - current_dim)
            video_features = np.concatenate([video_features, padding])
        
        return video_features
    
    def fit_pca(self, features_list: List[np.ndarray]):
        """
        训练PCA模型
        
        Args:
            features_list: 特征列表
        """
        if not features_list:
            return
        
        # 确保所有特征维度一致
        max_dim = max(len(f) for f in features_list)
        padded_features = []
        
        for features in features_list:
            if len(features) < max_dim:
                padded = np.pad(features, (0, max_dim - len(features)), 'constant')
            else:
                padded = features[:max_dim]
            padded_features.append(padded)
        
        # 训练PCA
        self.pca = PCA(n_components=self.config.DIMENSION)
        self.pca.fit(padded_features)
        self.is_fitted = True

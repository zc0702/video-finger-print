"""
特征提取模块
"""
import cv2
import numpy as np
from typing import List, Tuple
from sklearn.decomposition import PCA
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
        提取纹理特征（LBP）
        
        Args:
            frame: 输入帧
            
        Returns:
            纹理特征向量
        """
        # 转换为灰度图
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # 计算LBP特征
        def local_binary_pattern(image, P=8, R=1):
            """计算局部二值模式"""
            rows, cols = image.shape
            lbp = np.zeros((rows, cols), dtype=np.uint8)
            
            for i in range(R, rows - R):
                for j in range(R, cols - R):
                    center = image[i, j]
                    binary_string = ''
                    for k in range(P):
                        angle = 2 * np.pi * k / P
                        x = int(i + R * np.cos(angle))
                        y = int(j + R * np.sin(angle))
                        if x < rows and y < cols:
                            binary_string += '1' if image[x, y] >= center else '0'
                    lbp[i, j] = int(binary_string, 2)
            return lbp
        
        lbp = local_binary_pattern(gray)
        
        # 计算LBP直方图
        hist, _ = np.histogram(lbp.ravel(), bins=256, range=(0, 256))
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
        features = np.concatenate([color_features, texture_features, edge_features])
        
        return features
    
    def extract_video_features(self, frames: List[np.ndarray]) -> np.ndarray:
        """
        提取视频的完整特征向量
        
        Args:
            frames: 视频帧列表
            
        Returns:
            视频特征向量
        """
        if not frames:
            raise ValueError("帧列表不能为空")
        
        # 提取每帧的特征
        frame_features = []
        for frame in frames:
            features = self.extract_frame_features(frame)
            frame_features.append(features)
        
        # 计算帧间特征的平均值和标准差
        frame_features = np.array(frame_features)
        mean_features = np.mean(frame_features, axis=0)
        std_features = np.std(frame_features, axis=0)
        
        # 合并统计特征
        video_features = np.concatenate([mean_features, std_features])
        
        # 如果特征维度超过配置的维度，使用PCA降维
        if len(video_features) > self.config.DIMENSION:
            if not self.is_fitted:
                self.pca = PCA(n_components=self.config.DIMENSION)
                video_features = self.pca.fit_transform(video_features.reshape(1, -1)).flatten()
                self.is_fitted = True
            else:
                video_features = self.pca.transform(video_features.reshape(1, -1)).flatten()
        
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

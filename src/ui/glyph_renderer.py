"""
字形渲染 Widget

用于渲染单个字形的位图数据
"""
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPainter, QColor, QImage, QPixmap
import numpy as np
from typing import Optional
from ..models import GlyphInfo


class GlyphRenderer(QWidget):
    """字形渲染器"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.glyph: Optional[GlyphInfo] = None
        self.bpp = 4
        self.scale = 10  # 放大倍数
        self.show_grid = True
        self.setMinimumSize(100, 100)
        
    def set_glyph(self, glyph: Optional[GlyphInfo], bpp: int = 4):
        """设置要渲染的字形"""
        self.glyph = glyph
        self.bpp = bpp
        self.update()
        
    def set_scale(self, scale: int):
        """设置放大倍数"""
        self.scale = max(1, min(scale, 40))
        self.updateGeometry()
        self.update()
        
    def set_show_grid(self, show: bool):
        """设置是否显示网格"""
        self.show_grid = show
        self.update()
        
    def sizeHint(self) -> QSize:
        """推荐大小"""
        if self.glyph and self.glyph.bitmap_data is not None:
            w = self.glyph.box_w * self.scale
            h = self.glyph.box_h * self.scale
            return QSize(w + 20, h + 20)
        return QSize(200, 200)
        
    def paintEvent(self, event):
        """绘制事件"""
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(255, 255, 255))
        
        if not self.glyph or self.glyph.bitmap_data is None:
            # 显示提示信息
            painter.setPen(QColor(150, 150, 150))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "无字形数据")
            return
        
        # 计算显示位置（居中）
        bitmap = self.glyph.bitmap_data
        scaled_w = bitmap.shape[1] * self.scale
        scaled_h = bitmap.shape[0] * self.scale
        
        x_offset = (self.width() - scaled_w) // 2
        y_offset = (self.height() - scaled_h) // 2
        
        # 转换为 QImage
        qimage = self._bitmap_to_qimage(bitmap)
        if qimage:
            # 缩放显示
            scaled_pixmap = QPixmap.fromImage(qimage).scaled(
                scaled_w, scaled_h,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.FastTransformation
            )
            painter.drawPixmap(x_offset, y_offset, scaled_pixmap)
            
            # 绘制网格
            if self.show_grid and self.scale >= 4:
                self._draw_grid(painter, x_offset, y_offset, scaled_w, scaled_h, bitmap.shape)
    
    def _bitmap_to_qimage(self, bitmap: np.ndarray) -> Optional[QImage]:
        """将位图转换为 QImage"""
        try:
            height, width = bitmap.shape
            
            # 根据 BPP 计算最大值
            max_val = (1 << self.bpp) - 1
            
            # 归一化到 0-255
            normalized = (bitmap.astype(np.float32) / max_val * 255).astype(np.uint8)
            
            # 反转（黑色前景，白色背景）
            inverted = 255 - normalized
            
            # 创建灰度图像
            qimage = QImage(inverted.data, width, height, width, QImage.Format.Format_Grayscale8)
            
            # 复制数据以避免 NumPy 数组被释放
            return qimage.copy()
            
            return qimage
        except Exception as e:
            print(f"位图转换失败: {e}")
            return None
    
    def _draw_grid(self, painter: QPainter, x: int, y: int, w: int, h: int, shape: tuple):
        """绘制网格"""
        painter.setPen(QColor(200, 200, 200, 100))
        
        rows, cols = shape
        cell_w = w / cols
        cell_h = h / rows
        
        # 垂直线
        for i in range(cols + 1):
            x_pos = x + int(i * cell_w)
            painter.drawLine(x_pos, y, x_pos, y + h)
        
        # 水平线
        for i in range(rows + 1):
            y_pos = y + int(i * cell_h)
            painter.drawLine(x, y_pos, x + w, y_pos)


def qRgb(r, g, b):
    """创建 RGB 颜色值"""
    return (255 << 24) | (r << 16) | (g << 8) | b

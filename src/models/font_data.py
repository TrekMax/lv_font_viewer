"""
LVGL 字体数据模型

定义字体、字形等数据结构
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import numpy as np


@dataclass
class GlyphInfo:
    """字形信息"""
    unicode: int                    # Unicode 码点
    bitmap_index: int               # 位图数据索引
    adv_w: int                      # 前进宽度 (FP12.4 定点数)
    box_w: int                      # 边界框宽度
    box_h: int                      # 边界框高度
    ofs_x: int                      # X 偏移
    ofs_y: int                      # Y 偏移
    bitmap_data: Optional[np.ndarray] = None  # 位图数据 (解析后填充)
    
    @property
    def char(self) -> str:
        """返回对应的字符"""
        try:
            return chr(self.unicode)
        except (ValueError, OverflowError):
            return '?'
    
    @property
    def advance_width(self) -> float:
        """实际前进宽度（像素）"""
        return self.adv_w / 16.0


@dataclass
class CmapRange:
    """字符映射范围"""
    range_start: int                # 起始 Unicode
    range_length: int               # 范围长度
    glyph_id_start: int            # 起始字形 ID
    unicode_list: Optional[List[int]] = None  # Unicode 列表（稀疏格式）
    glyph_id_ofs_list: Optional[List[int]] = None  # 字形 ID 偏移列表
    list_length: int = 0
    cmap_type: str = "FORMAT0_TINY"  # 映射类型


@dataclass
class KernPair:
    """字距调整对"""
    left_glyph_id: int
    right_glyph_id: int
    value: int


@dataclass
class FontInfo:
    """字体信息"""
    # 基本信息
    font_name: str = ""
    file_path: str = ""
    file_type: str = ""  # "c" or "bin"
    
    # 字体度量
    font_size: int = 0
    line_height: int = 0
    base_line: int = 0
    bpp: int = 0  # 每像素位数 (1, 2, 4, 8)
    
    # 字形数据
    glyphs: List[GlyphInfo] = field(default_factory=list)
    glyph_bitmap: bytes = b''  # 原始位图数据
    
    # 字符映射
    cmap_ranges: List[CmapRange] = field(default_factory=list)
    
    # 字距调整
    kern_pairs: List[KernPair] = field(default_factory=list)
    kern_scale: int = 0
    
    # 其他属性
    subpx: str = "NONE"  # 子像素模式
    compression: str = "NONE"  # 压缩方式
    underline_position: int = 0
    underline_thickness: int = 0
    
    # 索引加速
    unicode_to_glyph: Dict[int, GlyphInfo] = field(default_factory=dict)
    
    def get_glyph(self, unicode_val: int) -> Optional[GlyphInfo]:
        """根据 Unicode 获取字形"""
        return self.unicode_to_glyph.get(unicode_val)
    
    def get_unicode_ranges(self) -> List[tuple]:
        """获取所有 Unicode 范围"""
        ranges = []
        for cmap in self.cmap_ranges:
            ranges.append((cmap.range_start, cmap.range_start + cmap.range_length - 1))
        return ranges
    
    def get_total_glyphs(self) -> int:
        """获取字形总数"""
        return len(self.glyphs)
    
    def build_index(self):
        """构建 Unicode 到字形的索引"""
        self.unicode_to_glyph.clear()
        for glyph in self.glyphs:
            if glyph.unicode > 0:  # 跳过保留字形
                self.unicode_to_glyph[glyph.unicode] = glyph

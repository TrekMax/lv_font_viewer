"""
BIN 文件解析器

解析 lv_font_conv 生成的二进制字体文件
"""
import struct
import numpy as np
from typing import Optional
from ..models import FontInfo, GlyphInfo, CmapRange


class BINFontParser:
    """BIN 格式字体文件解析器"""
    
    def __init__(self):
        self.data = b''
        self.offset = 0
        
    def parse(self, file_path: str) -> Optional[FontInfo]:
        """解析 BIN 字体文件"""
        try:
            with open(file_path, 'rb') as f:
                self.data = f.read()
            
            self.offset = 0
            font_info = FontInfo()
            font_info.file_path = file_path
            font_info.file_type = "bin"
            
            # BIN 文件格式（简化版本，实际格式可能更复杂）
            # 这里提供基本框架，需要根据实际 lv_font_conv 输出调整
            
            # 解析文件头
            self._parse_header(font_info)
            
            # 解析字形数据
            self._parse_glyphs(font_info)
            
            # 解析字符映射
            self._parse_cmap(font_info)
            
            # 构建索引
            font_info.build_index()
            
            return font_info
            
        except Exception as e:
            print(f"解析 BIN 文件失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _read_uint8(self) -> int:
        """读取 uint8"""
        val = struct.unpack_from('B', self.data, self.offset)[0]
        self.offset += 1
        return val
    
    def _read_uint16(self) -> int:
        """读取 uint16"""
        val = struct.unpack_from('<H', self.data, self.offset)[0]
        self.offset += 2
        return val
    
    def _read_uint32(self) -> int:
        """读取 uint32"""
        val = struct.unpack_from('<I', self.data, self.offset)[0]
        self.offset += 4
        return val
    
    def _read_int8(self) -> int:
        """读取 int8"""
        val = struct.unpack_from('b', self.data, self.offset)[0]
        self.offset += 1
        return val
    
    def _read_int16(self) -> int:
        """读取 int16"""
        val = struct.unpack_from('<h', self.data, self.offset)[0]
        self.offset += 2
        return val
    
    def _parse_header(self, font_info: FontInfo):
        """解析文件头
        
        注意: BIN 格式需要根据实际 lv_font_conv 输出调整
        这里提供一个基本框架
        """
        # 示例头部结构（需要根据实际格式调整）
        # 魔数
        magic = self._read_uint32()
        if magic != 0x464E544C:  # "LNTF" 的示例魔数
            print("警告: 文件魔数不匹配，可能不是有效的 LVGL 字体文件")
        
        # 版本
        version = self._read_uint16()
        
        # 字体大小
        font_info.font_size = self._read_uint8()
        
        # BPP
        font_info.bpp = self._read_uint8()
        
        # line_height
        font_info.line_height = self._read_uint8()
        
        # base_line
        font_info.base_line = self._read_int8()
    
    def _parse_glyphs(self, font_info: FontInfo):
        """解析字形数据"""
        # 字形数量
        glyph_count = self._read_uint16()
        
        # 读取字形描述符
        for i in range(glyph_count):
            glyph = GlyphInfo(
                unicode=self._read_uint32(),  # Unicode
                bitmap_index=self._read_uint32(),  # 位图索引
                adv_w=self._read_uint16(),  # 前进宽度
                box_w=self._read_uint8(),  # 宽度
                box_h=self._read_uint8(),  # 高度
                ofs_x=self._read_int8(),  # X 偏移
                ofs_y=self._read_int8()   # Y 偏移
            )
            font_info.glyphs.append(glyph)
        
        # 读取位图数据
        bitmap_size = self._read_uint32()
        font_info.glyph_bitmap = self.data[self.offset:self.offset + bitmap_size]
        self.offset += bitmap_size
        
        # 提取每个字形的位图
        self._extract_glyph_bitmaps(font_info)
    
    def _parse_cmap(self, font_info: FontInfo):
        """解析字符映射"""
        cmap_count = self._read_uint16()
        
        for i in range(cmap_count):
            cmap = CmapRange(
                range_start=self._read_uint32(),
                range_length=self._read_uint16(),
                glyph_id_start=self._read_uint16()
            )
            font_info.cmap_ranges.append(cmap)
    
    def _extract_glyph_bitmaps(self, font_info: FontInfo):
        """从位图数据中提取每个字形的位图"""
        if not font_info.glyph_bitmap:
            return
        
        for glyph in font_info.glyphs:
            if glyph.box_w == 0 or glyph.box_h == 0:
                continue
            
            # 计算位图大小
            pixel_count = glyph.box_w * glyph.box_h
            byte_count = self._calculate_bitmap_bytes(pixel_count, font_info.bpp)
            
            # 检查索引是否有效
            if glyph.bitmap_index + byte_count > len(font_info.glyph_bitmap):
                continue
            
            # 提取位图数据
            bitmap_bytes = font_info.glyph_bitmap[glyph.bitmap_index:glyph.bitmap_index + byte_count]
            
            # 解包位图
            glyph.bitmap_data = self._unpack_bitmap(
                bitmap_bytes, 
                glyph.box_w, 
                glyph.box_h, 
                font_info.bpp
            )
    
    def _calculate_bitmap_bytes(self, pixel_count: int, bpp: int) -> int:
        """计算位图所需字节数"""
        if bpp == 8:
            return pixel_count
        elif bpp == 4:
            return (pixel_count + 1) // 2
        elif bpp == 2:
            return (pixel_count + 3) // 4
        elif bpp == 1:
            return (pixel_count + 7) // 8
        return pixel_count
    
    def _unpack_bitmap(self, data: bytes, width: int, height: int, bpp: int) -> np.ndarray:
        """解包位图数据"""
        pixels = np.zeros((height, width), dtype=np.uint8)
        
        if bpp == 8:
            pixels = np.frombuffer(data, dtype=np.uint8).reshape(height, width)
        
        elif bpp == 4:
            pixel_idx = 0
            for byte_val in data:
                if pixel_idx >= width * height:
                    break
                pixels.flat[pixel_idx] = (byte_val >> 4) & 0x0F
                pixel_idx += 1
                if pixel_idx >= width * height:
                    break
                pixels.flat[pixel_idx] = byte_val & 0x0F
                pixel_idx += 1
        
        elif bpp == 2:
            pixel_idx = 0
            for byte_val in data:
                if pixel_idx >= width * height:
                    break
                for shift in [6, 4, 2, 0]:
                    pixels.flat[pixel_idx] = (byte_val >> shift) & 0x03
                    pixel_idx += 1
                    if pixel_idx >= width * height:
                        break
        
        elif bpp == 1:
            pixel_idx = 0
            for byte_val in data:
                if pixel_idx >= width * height:
                    break
                for bit in range(7, -1, -1):
                    pixels.flat[pixel_idx] = (byte_val >> bit) & 0x01
                    pixel_idx += 1
                    if pixel_idx >= width * height:
                        break
        
        return pixels

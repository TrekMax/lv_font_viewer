"""
C 文件解析器

解析 lv_font_conv 生成的 C 源代码文件
"""
import re
import numpy as np
from typing import Optional
from ..models import FontInfo, GlyphInfo, CmapRange


class CFontParser:
    """C 格式字体文件解析器"""
    
    def __init__(self):
        self.content = ""
        
    def parse(self, file_path: str) -> Optional[FontInfo]:
        """解析 C 字体文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.content = f.read()
            
            font_info = FontInfo()
            font_info.file_path = file_path
            font_info.file_type = "c"
            
            # 解析基本信息
            self._parse_basic_info(font_info)
            
            # 解析位图数据
            self._parse_bitmap(font_info)
            
            # 解析字形描述
            self._parse_glyph_descriptors(font_info)
            
            # 解析字符映射
            self._parse_cmap(font_info)
            
            # 解析字体头信息
            self._parse_font_header(font_info)
            
            # 构建索引
            font_info.build_index()
            
            # 提取位图数据到每个字形
            self._extract_glyph_bitmaps(font_info)
            
            return font_info
            
        except Exception as e:
            print(f"解析 C 文件失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _parse_basic_info(self, font_info: FontInfo):
        """解析基本信息"""
        # 解析字体大小
        size_match = re.search(r'Size:\s*(\d+)\s*px', self.content)
        if size_match:
            font_info.font_size = int(size_match.group(1))
        
        # 解析 BPP
        bpp_match = re.search(r'Bpp:\s*(\d+)', self.content)
        if bpp_match:
            font_info.bpp = int(bpp_match.group(1))
        
        # 解析字体名称
        name_match = re.search(r'(?:const\s+)?lv_font_t\s+(\w+)\s*=', self.content)
        if name_match:
            font_info.font_name = name_match.group(1)
    
    def _parse_bitmap(self, font_info: FontInfo):
        """解析位图数据"""
        # 查找位图数组
        bitmap_pattern = r'static\s+(?:LV_ATTRIBUTE_LARGE_CONST\s+)?const\s+uint8_t\s+glyph_bitmap\[\]\s*=\s*\{([^}]+)\}'
        match = re.search(bitmap_pattern, self.content, re.DOTALL)
        
        if match:
            bitmap_str = match.group(1)
            # 提取所有十六进制数值
            hex_values = re.findall(r'0x([0-9a-fA-F]+)', bitmap_str)
            font_info.glyph_bitmap = bytes([int(h, 16) for h in hex_values])
    
    def _parse_glyph_descriptors(self, font_info: FontInfo):
        """解析字形描述符"""
        # 查找字形描述数组的开始位置
        start_pattern = r'static\s+const\s+lv_font_fmt_txt_glyph_dsc_t\s+glyph_dsc\[\]\s*=\s*\{'
        start_match = re.search(start_pattern, self.content)
        
        if not start_match:
            return
        
        # 从开始位置查找到结束的 };
        start_pos = start_match.end()
        
        # 查找配对的右大括号
        brace_count = 1
        pos = start_pos
        while pos < len(self.content) and brace_count > 0:
            if self.content[pos] == '{':
                brace_count += 1
            elif self.content[pos] == '}':
                brace_count -= 1
            pos += 1
        
        if brace_count != 0:
            return
        
        glyph_str = self.content[start_pos:pos-1]
        
        # 解析每个字形描述
        # 格式: {.bitmap_index = 0, .adv_w = 142, .box_w = 9, .box_h = 12, .ofs_x = 0, .ofs_y = 0}
        glyph_lines = re.findall(
            r'\{\s*\.bitmap_index\s*=\s*(\d+)\s*,\s*\.adv_w\s*=\s*(\d+)\s*,\s*\.box_w\s*=\s*(\d+)\s*,\s*\.box_h\s*=\s*(\d+)\s*,\s*\.ofs_x\s*=\s*(-?\d+)\s*,\s*\.ofs_y\s*=\s*(-?\d+)\s*\}',
            glyph_str,
            re.DOTALL
        )
        
        for idx, (bitmap_idx, adv_w, box_w, box_h, ofs_x, ofs_y) in enumerate(glyph_lines):
            glyph = GlyphInfo(
                unicode=0,  # 稍后通过 cmap 填充
                bitmap_index=int(bitmap_idx),
                adv_w=int(adv_w),
                box_w=int(box_w),
                box_h=int(box_h),
                ofs_x=int(ofs_x),
                ofs_y=int(ofs_y)
            )
            font_info.glyphs.append(glyph)
    
    def _parse_cmap(self, font_info: FontInfo):
        """解析字符映射"""
        # 查找 cmap 数组
        cmap_pattern = r'static\s+const\s+lv_font_fmt_txt_cmap_t\s+cmaps\[\]\s*=\s*\{([^}]+)\}'
        match = re.search(cmap_pattern, self.content, re.DOTALL)
        
        if not match:
            return
        
        cmap_str = match.group(1)
        
        # 解析每个 cmap 范围
        # 格式: {.range_start = 48, .range_length = 10, .glyph_id_start = 1, ...}
        cmap_ranges = re.findall(
            r'\{\s*\.range_start\s*=\s*(\d+)\s*,\s*\.range_length\s*=\s*(\d+)\s*,\s*\.glyph_id_start\s*=\s*(\d+)',
            cmap_str
        )
        
        for range_start, range_len, glyph_id_start in cmap_ranges:
            cmap = CmapRange(
                range_start=int(range_start),
                range_length=int(range_len),
                glyph_id_start=int(glyph_id_start)
            )
            font_info.cmap_ranges.append(cmap)
            
            # 填充字形的 Unicode 值
            for i in range(int(range_len)):
                unicode_val = int(range_start) + i
                glyph_id = int(glyph_id_start) + i
                
                if glyph_id < len(font_info.glyphs):
                    font_info.glyphs[glyph_id].unicode = unicode_val
    
    def _parse_font_header(self, font_info: FontInfo):
        """解析字体头信息"""
        # 解析 line_height
        line_height_match = re.search(r'\.line_height\s*=\s*(\d+)', self.content)
        if line_height_match:
            font_info.line_height = int(line_height_match.group(1))
        
        # 解析 base_line
        base_line_match = re.search(r'\.base_line\s*=\s*(-?\d+)', self.content)
        if base_line_match:
            font_info.base_line = int(base_line_match.group(1))
        
        # 解析 subpx
        subpx_match = re.search(r'\.subpx\s*=\s*LV_FONT_SUBPX_(\w+)', self.content)
        if subpx_match:
            font_info.subpx = subpx_match.group(1)
    
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
            # 8-bit: 直接复制
            pixels = np.frombuffer(data, dtype=np.uint8).reshape(height, width)
        
        elif bpp == 4:
            # 4-bit: 2 像素/字节
            pixel_idx = 0
            for byte_val in data:
                if pixel_idx >= width * height:
                    break
                # 高 nibble 是第一个像素
                pixels.flat[pixel_idx] = (byte_val >> 4) & 0x0F
                pixel_idx += 1
                if pixel_idx >= width * height:
                    break
                # 低 nibble 是第二个像素
                pixels.flat[pixel_idx] = byte_val & 0x0F
                pixel_idx += 1
        
        elif bpp == 2:
            # 2-bit: 4 像素/字节
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
            # 1-bit: 8 像素/字节
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

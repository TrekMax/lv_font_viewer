"""
BIN 文件解析器

解析 lv_font_conv 生成的二进制字体文件

注意：BIN 格式解析器目前只是部分实现，可能无法正确解析所有 BIN 文件。
推荐使用 C 文件格式以获得最佳兼容性。

格式：使用区块（chunk）结构，每个区块包含：
- 4 字节：区块大小（包含自身和名称）
- 4 字节：区块名称（如 "head", "cmap", "loca", "glyf"）
- 数据内容
"""
import struct
import numpy as np
from typing import Optional, Dict
from ..models import FontInfo, GlyphInfo, CmapRange


class BINFontParser:
    """BIN 格式字体文件解析器"""
    
    def __init__(self):
        self.file_data = b''  # 完整文件数据
        self.data = b''  # 当前操作的数据（可能是区块数据）
        self.offset = 0
        self.chunks: Dict[str, bytes] = {}
        
    def parse(self, file_path: str) -> Optional[FontInfo]:
        """解析 BIN 字体文件"""
        try:
            with open(file_path, 'rb') as f:
                self.file_data = f.read()
                self.data = self.file_data  # 初始化为文件数据
            
            self.offset = 0
            font_info = FontInfo()
            font_info.file_path = file_path
            font_info.file_type = "bin"
            
            # 读取所有区块
            self._read_chunks()
            
            # 解析各个区块
            if 'head' in self.chunks:
                self._parse_head_chunk(font_info)
            
            if 'cmap' in self.chunks:
                self._parse_cmap_chunk(font_info)
            
            if 'loca' in self.chunks and 'glyf' in self.chunks:
                self._parse_glyf_chunks(font_info)
            
            # 构建索引
            font_info.build_index()
            
            return font_info
            
        except Exception as e:
            print(f"解析 BIN 文件失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _read_chunks(self):
        """读取所有区块
        
        格式：
        - uint32: chunk_size (包含自身和名称的总大小)
        - char[4]: chunk_name (4字节固定长度名称)
        - byte[]: chunk_data
        """
        self.data = self.file_data  # 确保使用文件数据
        self.offset = 0
        while self.offset < len(self.data):
            # 读取区块大小
            if self.offset + 4 > len(self.data):
                break
            chunk_size = self._read_uint32()
            
            # 读取区块名称（4个字符）
            if self.offset + 4 > len(self.data):
                break
            
            chunk_name = self.data[self.offset:self.offset + 4].decode('ascii', errors='ignore').rstrip('\x00')
            self.offset += 4
            
            # 读取区块数据
            # chunk_size 包含: 4(size字段) + 4(name字段) + data
            data_size = chunk_size - 8  # 减去大小字段和名称字段
            if data_size < 0:
                break
            if self.offset + data_size > len(self.file_data):  # 使用 file_data
                break
            
            chunk_data = self.data[self.offset:self.offset + data_size]
            self.chunks[chunk_name] = chunk_data
            self.offset += data_size
    
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
    
    def _parse_head_chunk(self, font_info: FontInfo):
        """解析 head 区块
        
        格式（基于 lv_font_conv table_head.js）:
        - uint32: version
        - uint16: tables_count
        - uint16: font_size
        - uint16: ascent
        - int16: descent
        - uint16: typo_ascent
        - int16: typo_descent
        - uint16: typo_line_gap
        - int16: min_y
        - int16: max_y
        - uint16: def_advance_width
        - uint16: kerning_scale (FP12.4)
        - uint8: index_to_loc_format
        - uint8: glyph_id_format
        - uint8: advance_width_format
        - uint8: bits_per_pixel (BPP)
        - uint8: xy_bits
        - uint8: wh_bits
        - uint8: advance_width_bits
        - uint8: compression_id
        - uint8: subpixels_mode
        - uint8: reserved
        - int16: underline_position
        - uint16: underline_thickness
        """
        data = self.chunks['head']
        self.offset = 0
        self.data = data
        
        # 版本
        version = self._read_uint32()
        
        # 表数量
        tables_count = self._read_uint16()
        
        # 字体大小
        font_info.font_size = self._read_uint16()
        
        # ascent/descent
        ascent = self._read_uint16()
        descent = self._read_int16()
        
        # typo metrics
        typo_ascent = self._read_uint16()
        typo_descent = self._read_int16()
        typo_line_gap = self._read_uint16()
        
        # y 范围
        min_y = self._read_int16()
        max_y = self._read_int16()
        
        # 默认前进宽度
        def_advance_width = self._read_uint16()
        
        # kerning scale
        kerning_scale = self._read_uint16()
        
        # 格式标志
        index_to_loc_format = self._read_uint8()
        glyph_id_format = self._read_uint8()
        advance_width_format = self._read_uint8()
        
        # BPP - 这是关键！
        font_info.bpp = self._read_uint8()
        
        # 其他位数
        xy_bits = self._read_uint8()
        wh_bits = self._read_uint8()
        advance_width_bits = self._read_uint8()
        
        # 压缩和子像素模式
        compression_id = self._read_uint8()
        subpixels_mode = self._read_uint8()
        
        # 保留字节
        reserved = self._read_uint8()
        
        # 下划线
        underline_position = self._read_int16()
        underline_thickness = self._read_uint16()
        
        # 计算 line_height 和 base_line
        # 根据 LVGL 的定义：line_height = ascent - descent
        font_info.line_height = ascent - descent
        # base_line 是从底部测量的，所以是 -descent
        font_info.base_line = -descent
    
    def _parse_cmap_chunk(self, font_info: FontInfo):
        """解析 cmap 区块
        
        cmap chunk 数据格式 (已去除外层chunk的size和label):
        - size: uint32 (内部size,冗余字段)
        - label: char[4] (内部label 'cmap',冗余)
        - count: uint32 (子表数量)
        - sub_headers: 每个16字节
          - offset: uint32 (子表数据偏移,相对于整个cmap chunk开始)
          - rangeStart: uint32 (Unicode起始)
          - rangeLen: uint16 (范围长度)
          - glyphIdOffset: uint16 (glyph ID起始)
          - total: uint16 (总数)
          - type: uint8 (格式类型: 0=FORMAT_0, 1=FORMAT_SPARSE, 2=FORMAT_0_TINY, 3=FORMAT_SPARSE_TINY)
          - reserved: uint8
        - sub_data: 子表数据
        
        注意: chunks['cmap'] 已经去掉了外层chunk的size/label,
        但内部还有一层size/label(冗余),需要跳过
        """
        data = self.chunks['cmap']
        self.offset = 0
        self.data = data
        
        if len(data) < 12:
            return
        
        # 读取内部头部 (冗余,但需要跳过)
        inner_size = self._read_uint32()  # 跳过
        inner_label = self.data[self.offset:self.offset+4]  # 跳过  
        self.offset += 4
        count = self._read_uint32()  # 子表数量
        
        # 存储 unicode -> glyph_id 映射
        unicode_to_glyph = {}
        
        # 读取所有子表头
        for i in range(count):
            if self.offset + 16 > len(data):
                break
                
            # 读取子表头 (16字节)
            sub_offset = self._read_uint32()
            range_start = self._read_uint32()
            range_len = self._read_uint16()
            glyph_id_offset = self._read_uint16()
            total = self._read_uint16()
            sub_type = self._read_uint8()
            reserved = self._read_uint8()
            
            # 根据类型解析数据
            # sub_offset 是相对于整个cmap buffer (包括内部size/label/count) 的偏移
            # chunks['cmap'] 已经去掉了外层chunk头,但保留了内部size/label/count
            # 所以 sub_offset 直接用于 chunks['cmap'] 即可
            
            if sub_type == 2:  # FORMAT_0_TINY - 无数据,glyph ID连续
                for j in range(range_len):
                    unicode_to_glyph[range_start + j] = glyph_id_offset + j
                    
            elif sub_type == 0:  # FORMAT_0 - delta数组(uint8)
                if sub_offset >= 0 and sub_offset + total <= len(data):
                    for j in range(range_len):
                        if sub_offset + j < len(data):
                            delta = data[sub_offset + j]
                            unicode_to_glyph[range_start + j] = glyph_id_offset + delta
                            
            elif sub_type == 3:  # FORMAT_SPARSE_TINY - 只有code_delta(uint16)
                codes_size = total * 2
                if sub_offset >= 0 and sub_offset + codes_size <= len(data):
                    for j in range(total):
                        pos = sub_offset + j * 2
                        if pos + 2 <= len(data):
                            code_delta = struct.unpack('<H', data[pos:pos+2])[0]
                            unicode_to_glyph[range_start + code_delta] = glyph_id_offset + j
                        
            elif sub_type == 1:  # FORMAT_SPARSE - code_delta + id_delta (都是uint16)
                codes_size = total * 2
                ids_offset = sub_offset + codes_size
                if sub_offset >= 0 and ids_offset + codes_size <= len(data):
                    for j in range(total):
                        code_pos = sub_offset + j * 2
                        id_pos = ids_offset + j * 2
                        if code_pos + 2 <= len(data) and id_pos + 2 <= len(data):
                            code_delta = struct.unpack('<H', data[code_pos:code_pos+2])[0]
                            id_delta = struct.unpack('<H', data[id_pos:id_pos+2])[0]
                            unicode_to_glyph[range_start + code_delta] = glyph_id_offset + id_delta
        
        # 保存映射
        font_info.unicode_to_glyph = unicode_to_glyph
    
    def _parse_glyf_chunks(self, font_info: FontInfo):
        """解析 loca 和 glyf 区块
        
        loca chunk 格式:
        - size: uint32
        - label: char[4] ('loca')
        - count: uint32 (glyph数量)
        - offsets: uint16[] 或 uint32[] (根据head.index_to_loc_format)
        
        glyf chunk 格式:
        - size: uint32
        - label: char[4] ('glyf')
        - 字形数据: 二进制数据按glyph ID顺序拼接
        """
        loca_data = self.chunks['loca']
        glyf_data = self.chunks['glyf']
        
        # 解析 loca（位置表）
        self.offset = 0
        self.data = loca_data
        
        if len(loca_data) < 12:
            return
            
        # 读取 loca 头部
        loca_size = self._read_uint32()
        loca_label = self.data[self.offset:self.offset+4]
        self.offset += 4
        glyph_count = self._read_uint32()  # glyph 数量
        
        # 读取偏移表
        # 注意: 这些偏移是相对于 glyf 数据开始的位置 (跳过8字节头部)
        positions = []
        # loca 可能使用 uint16 或 uint32，需要从 head 表获取
        # 暂时假设使用 uint32
        for i in range(glyph_count):
            if self.offset + 4 <= len(loca_data):
                pos = self._read_uint32()
                positions.append(pos)
            else:
                break
        
        # glyf 数据从第8字节开始 (跳过size和label)
        glyf_data_start = 8
        
        # 使用 unicode_to_glyph 映射创建字形
        if not hasattr(font_info, 'unicode_to_glyph'):
            return
            
        for unicode_val, glyph_id in font_info.unicode_to_glyph.items():
            # 检查 glyph_id 有效性
            if glyph_id >= len(positions) - 1:
                continue
                
            # 获取字形数据的位置和大小
            start_pos = positions[glyph_id]
            end_pos = positions[glyph_id + 1]
            glyph_size = end_pos - start_pos
            
            # 如果字形大小为0，创建空字形
            if glyph_size == 0:
                glyph = GlyphInfo(
                    unicode=unicode_val,
                    bitmap_index=glyf_data_start + start_pos,
                    adv_w=0,
                    box_w=0,
                    box_h=0,
                    ofs_x=0,
                    ofs_y=0
                )
                font_info.glyphs.append(glyph)
                continue
                
            # 从 glyf 数据中读取
            # 注意: positions 中的偏移已经相对于 glyf 数据开始
            try:
                self.offset = glyf_data_start + start_pos
                self.data = glyf_data
                
                # 根据 table_glyf.js compileGlyph() 的格式:
                # 1. advance_width (如果不是等宽字体)
                # 2. bbox.x (xy_bits)
                # 3. bbox.y (xy_bits)
                # 4. bbox.width (wh_bits)
                # 5. bbox.height (wh_bits)
                # 6. pixel data
                
                # 暂时读取简化数据 (假设字节对齐)
                # TODO: 完整实现位流读取
                if glyph_size >= 6:
                    # 读取字形描述符
                    adv_w = self._read_uint16()
                    box_w = self._read_uint8()
                    box_h = self._read_uint8()
                    ofs_x = self._read_int8()
                    ofs_y = self._read_int8()
                    
                    # 读取位图数据
                    bitmap_size = glyph_size - 6  # 减去描述符大小
                    bitmap_data = glyf_data[self.offset:self.offset + bitmap_size]
                    
                    glyph = GlyphInfo(
                        unicode=unicode_val,
                        bitmap_index=glyf_data_start + start_pos,
                        adv_w=adv_w,
                        box_w=box_w,
                        box_h=box_h,
                        ofs_x=ofs_x,
                        ofs_y=ofs_y
                    )
                    
                    # 解包位图
                    if box_w > 0 and box_h > 0:
                        glyph.bitmap_data = self._unpack_bitmap(
                            bitmap_data, box_w, box_h, font_info.bpp
                        )
                    
                    font_info.glyphs.append(glyph)
            except Exception as e:
                # 解析失败，跳过这个字形
                continue
        
        # 保存原始位图数据
        font_info.glyph_bitmap = glyf_data
    
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

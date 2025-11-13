#!/usr/bin/env python3
"""
测试脚本 - 验证字体解析功能
"""
import sys
import os

# 添加 src 到路径
sys.path.insert(0, os.path.dirname(__file__))

from src.parsers import CFontParser


def test_parse():
    """测试解析 C 文件"""
    # 测试文件路径
    test_file = "../web_fonts/lv_font_fangzheng_16.c"
    
    if not os.path.exists(test_file):
        print(f"测试文件不存在: {test_file}")
        return
    
    print(f"正在解析: {test_file}")
    
    # 创建解析器
    parser = CFontParser()
    
    # 解析文件
    font_info = parser.parse(test_file)
    
    if not font_info:
        print("解析失败!")
        return
    
    # 打印信息
    print("\n=== 解析成功 ===")
    print(f"字体名称: {font_info.font_name}")
    print(f"字体大小: {font_info.font_size} px")
    print(f"BPP: {font_info.bpp} bit")
    print(f"行高: {font_info.line_height} px")
    print(f"基线: {font_info.base_line} px")
    print(f"字形总数: {len(font_info.glyphs)}")
    print(f"位图大小: {len(font_info.glyph_bitmap)} bytes")
    
    # 打印前5个字形
    print("\n=== 前5个字形 ===")
    for i, glyph in enumerate(font_info.glyphs[:5]):
        print(f"{i}. U+{glyph.unicode:04X} '{glyph.char}' - {glyph.box_w}x{glyph.box_h}")
        if glyph.bitmap_data is not None:
            print(f"   位图形状: {glyph.bitmap_data.shape}")
    
    # 测试 Unicode 范围
    print("\n=== Unicode 范围 ===")
    for start, end in font_info.get_unicode_ranges():
        print(f"U+{start:04X} - U+{end:04X} ({end - start + 1} 个字符)")
    
    print("\n✓ 测试完成!")


if __name__ == '__main__':
    test_parse()

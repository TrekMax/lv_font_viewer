# LV Font Viewer

LVGL 字体文件查看器 - 用于预览和分析 lv_font_conv 生成的字体文件。

## 功能特性

- ✅ 支持 .c 和 .bin 格式的 LVGL 字体文件
- ✅ 可视化字体字形渲染
- ✅ 字符搜索和筛选
- ✅ 字体信息展示（大小、BPP、压缩方式等）
- ✅ Unicode 范围浏览
- ✅ 字形详细信息（宽度、高度、偏移量等）

## 安装

```bash
# 安装依赖
pip install -r requirements.txt
```

## 使用方法

```bash
# 启动查看器
python lv_font_viewer.py

# 或使用快捷脚本
./run.sh
```

## 支持的文件格式

### .c 文件
lv_font_conv 生成的 C 源代码文件，包含字体数据和元信息。

示例：
```bash
lv_font_conv --bpp 4 --size 16 --font font.ttf -r 0x20-0x7F --format lvgl -o font_16.c
```

### .bin 文件
lv_font_conv 生成的二进制字体文件。

示例：
```bash
lv_font_conv --bpp 4 --size 16 --font font.ttf -r 0x20-0x7F --format bin -o font_16.bin
```

## 项目结构

```
lv_font_viewer/
├── src/
│   ├── parsers/          # 字体文件解析器
│   │   ├── c_parser.py   # C 文件解析
│   │   └── bin_parser.py # BIN 文件解析
│   ├── ui/               # 用户界面
│   │   ├── main_window.py
│   │   ├── font_viewer_widget.py
│   │   └── glyph_detail_widget.py
│   └── models/           # 数据模型
│       └── font_data.py
├── lv_font_viewer.py     # 主程序入口
├── requirements.txt
└── README.md
```

## 依赖库

- PyQt6 - GUI 框架
- numpy - 数组处理
- Pillow - 图像处理

## 开发

本项目基于 PyQt6 开发，使用 Python 3.8+。

## License

MIT License

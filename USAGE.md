# LVGL Font Viewer - 使用说明

## 快速开始

### 1. 安装依赖

```bash
cd lv_font_viewer
pip install -r requirements.txt
```

### 2. 启动程序

#### 方式一：使用启动脚本（推荐）
```bash
./run.sh
```

#### 方式二：直接运行 Python
```bash
python3 lv_font_viewer.py
```

#### 方式三：打开指定字体文件
```bash
python3 lv_font_viewer.py /path/to/font_file.c
```

## 功能说明

### 1. 打开字体文件

点击 "打开字体文件" 按钮，选择以下格式的文件：
- `.c` - lv_font_conv 生成的 C 源代码文件
- `.bin` - lv_font_conv 生成的二进制文件

### 2. 浏览字符

- **字符列表**：左侧显示所有可用字符
- **格式**：`U+XXXX 字符 (w:宽度 h:高度)`
- **选择**：点击任意字符查看详情

### 3. 字形预览

- **缩放控制**：调整预览大小（1-20倍）
- **网格显示**：显示/隐藏像素网格
- **自动居中**：字形自动居中显示

### 4. 搜索字符

支持多种搜索方式：

#### Unicode 码点（十六进制）
```
U+4E00
0x4E00
```

#### Unicode 码点（十进制）
```
19968
```

#### 直接输入字符
```
中
```

### 5. 查看信息

#### 字体信息标签页
- 字体名称、文件路径
- 字体大小、BPP、行高、基线
- 字形总数、位图大小
- 子像素模式、压缩方式

#### 字形信息标签页
- Unicode 码点和字符
- 前进宽度、边界框尺寸
- X/Y 偏移量
- 位图索引和像素数

#### Unicode 范围标签页
- 起始/结束 Unicode
- 每个范围的字符数量

## 测试示例

使用项目中已有的字体文件进行测试：

```bash
# 测试 12px 字体
python3 lv_font_viewer.py ../web_fonts/lv_font_fangzheng_12.c

# 测试 14px 字体
python3 lv_font_viewer.py ../web_fonts/lv_font_fangzheng_14.c

# 测试 16px 字体
python3 lv_font_viewer.py ../web_fonts/lv_font_fangzheng_16.c
```

## 支持的 BPP 格式

- **1-bit**: 单色（黑白）
- **2-bit**: 4 级灰度
- **4-bit**: 16 级灰度
- **8-bit**: 256 级灰度

## 键盘快捷键

- `Ctrl+O` - 打开文件（计划中）
- `Ctrl+F` - 聚焦搜索框（计划中）
- `Ctrl+Q` - 退出程序（计划中）

## 已知限制

1. **BIN 文件支持**：BIN 格式解析器提供了基本框架，但需要根据实际 lv_font_conv 的 BIN 格式进行调整
2. **压缩格式**：目前仅支持未压缩的字体文件
3. **子像素渲染**：暂不支持子像素抗锯齿预览

## 故障排除

### 问题：无法启动程序

**解决方案**：
```bash
# 检查 Python 版本（需要 3.8+）
python3 --version

# 重新安装依赖
pip3 install --upgrade -r requirements.txt
```

### 问题：文件解析失败

**解决方案**：
1. 确认文件是由 lv_font_conv 生成的
2. 检查文件格式是否正确
3. 查看终端错误信息

### 问题：字形显示异常

**解决方案**：
1. 调整缩放倍数
2. 检查字体 BPP 设置
3. 确认字形数据完整性

## 进阶使用

### 批量查看多个字体

创建脚本批量打开：

```bash
#!/bin/bash
for font in ../web_fonts/*.c; do
    echo "查看: $font"
    python3 lv_font_viewer.py "$font"
    read -p "按回车继续..."
done
```

### 导出字形图片（计划功能）

```python
# 未来版本将支持
# File -> Export Glyph as PNG
```

## 贡献

欢迎提交 Issue 和 Pull Request！

## License

MIT License

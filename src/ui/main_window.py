"""
主窗口

LVGL 字体查看器主界面
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QTextEdit,
    QFileDialog, QSplitter, QGroupBox, QScrollArea,
    QListWidget, QListWidgetItem, QSpinBox, QCheckBox,
    QTabWidget, QTableWidget, QTableWidgetItem
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont
from typing import Optional
import os

from ..models import FontInfo, GlyphInfo
from ..parsers import CFontParser, BINFontParser
from .glyph_renderer import GlyphRenderer


class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        self.font_info: Optional[FontInfo] = None
        self.current_glyph: Optional[GlyphInfo] = None
        
        self.setWindowTitle("LVGL Font Viewer")
        self.setGeometry(100, 100, 1200, 800)
        
        self._init_ui()
        
    def _init_ui(self):
        """初始化UI"""
        # 中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 工具栏
        toolbar = self._create_toolbar()
        main_layout.addLayout(toolbar)
        
        # 主分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧：字符列表
        left_panel = self._create_character_list()
        splitter.addWidget(left_panel)
        
        # 中间：字形预览
        middle_panel = self._create_glyph_preview()
        splitter.addWidget(middle_panel)
        
        # 右侧：详细信息
        right_panel = self._create_info_panel()
        splitter.addWidget(right_panel)
        
        # 设置分割比例
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        splitter.setStretchFactor(2, 1)
        
        main_layout.addWidget(splitter)
        
        # 状态栏
        self.statusBar().showMessage("就绪")
        
    def _create_toolbar(self) -> QHBoxLayout:
        """创建工具栏"""
        layout = QHBoxLayout()
        
        # 打开文件按钮
        self.btn_open = QPushButton("打开字体文件")
        self.btn_open.clicked.connect(self.open_file)
        layout.addWidget(self.btn_open)
        
        # 搜索框
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索字符 (输入 Unicode 或字符)")
        self.search_input.textChanged.connect(self.search_character)
        layout.addWidget(self.search_input)
        
        layout.addStretch()
        
        return layout
        
    def _create_character_list(self) -> QWidget:
        """创建字符列表"""
        widget = QGroupBox("字符列表")
        layout = QVBoxLayout(widget)
        
        # 统计信息
        self.lbl_char_count = QLabel("字符数: 0")
        layout.addWidget(self.lbl_char_count)
        
        # 字符列表
        self.char_list = QListWidget()
        self.char_list.setFont(QFont("Monospace", 10))
        self.char_list.currentItemChanged.connect(self.on_character_selected)
        layout.addWidget(self.char_list)
        
        return widget
        
    def _create_glyph_preview(self) -> QWidget:
        """创建字形预览"""
        widget = QGroupBox("字形预览")
        layout = QVBoxLayout(widget)
        
        # 控制面板
        control_layout = QHBoxLayout()
        
        # 缩放控制
        control_layout.addWidget(QLabel("缩放:"))
        self.spin_scale = QSpinBox()
        self.spin_scale.setRange(1, 20)
        self.spin_scale.setValue(4)
        self.spin_scale.valueChanged.connect(self.on_scale_changed)
        control_layout.addWidget(self.spin_scale)
        
        # 网格开关
        self.chk_grid = QCheckBox("显示网格")
        self.chk_grid.setChecked(True)
        self.chk_grid.stateChanged.connect(self.on_grid_toggled)
        control_layout.addWidget(self.chk_grid)
        
        control_layout.addStretch()
        layout.addLayout(control_layout)
        
        # 字形渲染器
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.glyph_renderer = GlyphRenderer()
        scroll.setWidget(self.glyph_renderer)
        
        layout.addWidget(scroll)
        
        return widget
        
    def _create_info_panel(self) -> QWidget:
        """创建信息面板"""
        widget = QGroupBox("信息")
        layout = QVBoxLayout(widget)
        
        # Tab 切换
        tabs = QTabWidget()
        
        # 字体信息标签页
        font_info_widget = QTextEdit()
        font_info_widget.setReadOnly(True)
        font_info_widget.setFont(QFont("Monospace", 9))
        self.txt_font_info = font_info_widget
        tabs.addTab(font_info_widget, "字体信息")
        
        # 字形信息标签页
        glyph_info_widget = QTextEdit()
        glyph_info_widget.setReadOnly(True)
        glyph_info_widget.setFont(QFont("Monospace", 9))
        self.txt_glyph_info = glyph_info_widget
        tabs.addTab(glyph_info_widget, "字形信息")
        
        # Unicode 范围标签页
        range_table = QTableWidget()
        range_table.setColumnCount(3)
        range_table.setHorizontalHeaderLabels(["起始", "结束", "数量"])
        self.tbl_ranges = range_table
        tabs.addTab(range_table, "Unicode 范围")
        
        layout.addWidget(tabs)
        
        return widget
    
    def open_file(self):
        """打开字体文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "打开 LVGL 字体文件",
            "",
            "字体文件 (*.c *.bin);;C 文件 (*.c);;BIN 文件 (*.bin);;所有文件 (*)"
        )
        
        if not file_path:
            return
        
        self.load_font(file_path)
    
    def load_font(self, file_path: str):
        """加载字体文件"""
        try:
            self.statusBar().showMessage(f"正在加载: {file_path}")
            
            # 根据文件扩展名选择解析器
            ext = os.path.splitext(file_path)[1].lower()
            
            if ext == '.c':
                parser = CFontParser()
            elif ext == '.bin':
                parser = BINFontParser()
            else:
                self.statusBar().showMessage("不支持的文件格式")
                return
            
            # 解析文件
            font_info = parser.parse(file_path)
            
            if not font_info:
                self.statusBar().showMessage("解析失败")
                return
            
            self.font_info = font_info
            
            # 更新UI
            self.update_font_info()
            self.update_character_list()
            self.update_unicode_ranges()
            
            self.statusBar().showMessage(f"已加载: {os.path.basename(file_path)}")
            
        except Exception as e:
            self.statusBar().showMessage(f"加载失败: {e}")
            import traceback
            traceback.print_exc()
    
    def update_font_info(self):
        """更新字体信息"""
        if not self.font_info:
            return
        
        info = self.font_info
        text = f"""字体名称: {info.font_name}
文件路径: {info.file_path}
文件类型: {info.file_type.upper()}

=== 字体度量 ===
字体大小: {info.font_size} px
行高: {info.line_height} px
基线: {info.base_line} px
BPP: {info.bpp} bit

=== 统计 ===
字形总数: {info.get_total_glyphs()}
位图大小: {len(info.glyph_bitmap)} bytes

=== 其他属性 ===
子像素模式: {info.subpx}
压缩方式: {info.compression}
下划线位置: {info.underline_position}
下划线粗细: {info.underline_thickness}
"""
        self.txt_font_info.setPlainText(text)
    
    def update_character_list(self):
        """更新字符列表"""
        if not self.font_info:
            return
        
        self.char_list.clear()
        
        # 添加所有字形（跳过保留字形）
        for glyph in self.font_info.glyphs:
            if glyph.unicode > 0:
                char = glyph.char
                item_text = f"U+{glyph.unicode:04X}  {char}  (w:{glyph.box_w} h:{glyph.box_h})"
                item = QListWidgetItem(item_text)
                item.setData(Qt.ItemDataRole.UserRole, glyph)
                self.char_list.addItem(item)
        
        # 更新计数
        self.lbl_char_count.setText(f"字符数: {self.char_list.count()}")
    
    def update_unicode_ranges(self):
        """更新 Unicode 范围"""
        if not self.font_info:
            return
        
        self.tbl_ranges.setRowCount(0)
        
        ranges = self.font_info.get_unicode_ranges()
        for start, end in ranges:
            row = self.tbl_ranges.rowCount()
            self.tbl_ranges.insertRow(row)
            
            self.tbl_ranges.setItem(row, 0, QTableWidgetItem(f"U+{start:04X}"))
            self.tbl_ranges.setItem(row, 1, QTableWidgetItem(f"U+{end:04X}"))
            self.tbl_ranges.setItem(row, 2, QTableWidgetItem(str(end - start + 1)))
        
        self.tbl_ranges.resizeColumnsToContents()
    
    def on_character_selected(self, current, previous):
        """字符选择事件"""
        if not current:
            return
        
        glyph = current.data(Qt.ItemDataRole.UserRole)
        if glyph:
            self.current_glyph = glyph
            self.update_glyph_preview(glyph)
            self.update_glyph_info(glyph)
    
    def update_glyph_preview(self, glyph: GlyphInfo):
        """更新字形预览"""
        if not self.font_info:
            return
        
        self.glyph_renderer.set_glyph(glyph, self.font_info.bpp)
    
    def update_glyph_info(self, glyph: GlyphInfo):
        """更新字形信息"""
        text = f"""Unicode: U+{glyph.unicode:04X}
字符: {glyph.char}

=== 度量 ===
前进宽度: {glyph.advance_width:.1f} px ({glyph.adv_w}/16)
边界框宽度: {glyph.box_w} px
边界框高度: {glyph.box_h} px
X 偏移: {glyph.ofs_x} px
Y 偏移: {glyph.ofs_y} px

=== 位图 ===
位图索引: {glyph.bitmap_index}
像素数: {glyph.box_w * glyph.box_h}
"""
        self.txt_glyph_info.setPlainText(text)
    
    def search_character(self, text: str):
        """搜索字符"""
        if not text or not self.font_info:
            return
        
        # 尝试作为 Unicode 码点
        if text.startswith('U+') or text.startswith('0x'):
            try:
                unicode_val = int(text[2:], 16)
                self.select_character_by_unicode(unicode_val)
                return
            except ValueError:
                pass
        
        # 尝试作为十进制数字
        if text.isdigit():
            try:
                unicode_val = int(text)
                self.select_character_by_unicode(unicode_val)
                return
            except ValueError:
                pass
        
        # 作为字符
        if len(text) > 0:
            char = text[0]
            unicode_val = ord(char)
            self.select_character_by_unicode(unicode_val)
    
    def select_character_by_unicode(self, unicode_val: int):
        """根据 Unicode 选择字符"""
        for i in range(self.char_list.count()):
            item = self.char_list.item(i)
            glyph = item.data(Qt.ItemDataRole.UserRole)
            if glyph and glyph.unicode == unicode_val:
                self.char_list.setCurrentItem(item)
                self.char_list.scrollToItem(item)
                break
    
    def on_scale_changed(self, value: int):
        """缩放改变"""
        self.glyph_renderer.set_scale(value)
    
    def on_grid_toggled(self, state):
        """网格开关"""
        self.glyph_renderer.set_show_grid(state == Qt.CheckState.Checked.value)

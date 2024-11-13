# 關於本專案
* 為[簡體字轉繁體字字體](https://github.com/OOOHA/Noto-Serif-cc)專案的一個部件
* 為修改[此專案](https://github.com/ayaka14732/OpenCCFontGenerator)而來
* 功能依賴於[OpenCC](https://github.com/BYVoid/OpenCC)


# 修改內容
* 去除標點符號轉換
* 修改中文資料來源(改成直接從[OpenCC](https://github.com/BYVoid/OpenCC)專案中的字典資料取得)
* 修改 font.py 裡的 remove_glyph 以及 remove_glyph 以應對文字檔中的 GPOS 表

**GOPS表**: Glyph Positioning Table 是 OpenType 字體的一部分，用於定義字形之間的相對位置。它主要應用於字符的微調定位，例如字母間距、上下標對齊、連字以及複雜語言中的字形排列等。
GPOS 表可以幫助實現更高品質的字體排版，尤其是在東亞文字（如漢字）和某些字母系統（如阿拉伯文和印度文字）中。

# 使用方法

### 安裝[Python](https://www.python.org/)
### 安裝[OpenCC](https://github.com/BYVoid/OpenCC?tab=readme-ov-file#installation-%E5%AE%89%E8%A3%9D)
### 下載本專案
### 進入專案目錄並執行
```bash
python3 setup.py install
```
### 如果已安裝
```bash
pip uninstall openccfontgenerator
python3 setup.py install 
```
### 檢查安裝
```bash
pip list
```

# 回報問題
請[回報](https://github.com/OOOHA/OpenCCFontGenerator/issues)


---


# About this project
* A component of the [Noto-Serif-cc](https://github.com/OOOHA/Noto-Serif-cc)project
* Derived from modifying[This Project](https://github.com/ayaka14732/OpenCCFontGenerator)
* Functionality relies on[OpenCC](https://github.com/BYVoid/OpenCC)


# Modifications
* Removed punctuation conversion
* Updated Chinese word data source(now directly using dictionary data from the[OpenCC](https://github.com/BYVoid/OpenCC))
* Modified remove_glyph and remove_glyph in font.py to handle GPOS tables in text files

**GOPS Tables**: Glyph Positioning Table is a part of OpenType font, used to define the relative positioning between glyphs. 
It primarily applies to fine-tuning character positioning, such as kerning, superscript/subscript alignment, ligatures, and complex language glyph arrangements.
The GPOS table enhances the quality of font typography, especially in East Asian scripts (such as Chinese characters) and certain alphabetic systems (such as Arabic and Indic scripts).

# How to Use

### Install[Python](https://www.python.org/)
### Install[OpenCC](https://github.com/BYVoid/OpenCC?tab=readme-ov-file#installation-%E5%AE%89%E8%A3%9D)
### Downbnload this Project
### Enter the Root Folder
```bash
python3 setup.py install
```
### If Already Installed
```bash
pip uninstall openccfontgenerator
python3 setup.py install 
```
### Check Installation 
```bash
pip list
```

# Report Issues
Please [Click](https://github.com/OOOHA/OpenCCFontGenerator/issues)

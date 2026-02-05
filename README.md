# 🔧 Setup & Cài Đặt - Mogi.vn Scraper

## 📋 Yêu Cầu Hệ Thống

- macOS
- Python 3.8+
- Kết nối internet ổn định

---

## 🚀 Cài Đặt Lần Đầu

### Bước 1: Cài đặt dependencies

```bash
cd /Users/trghoangminh/Desktop/DM
pip3 install -r requirements.txt
```

### Bước 2: Cài đặt Playwright browsers

```bash
playwright install chromium
```

**Lưu ý:** Chỉ cần chạy 1 lần duy nhất!

---

## 🔄 Chạy Lại Script

### Nếu đã cài đặt rồi:

```bash
cd /Users/trghoangminh/Desktop/DM
python3 mogi_multi_scraper.py
```

### Nếu gặp lỗi "module not found":

```bash
pip3 install playwright beautifulsoup4 lxml
playwright install chromium
```

---

## 📦 File Requirements.txt

Nội dung file `requirements.txt`:

```
playwright>=1.40.0
beautifulsoup4>=4.12.0
lxml>=4.9.0
pandas>=2.0.0
```

---

## ⚡ Quick Start (Copy & Paste)

```bash
# Di chuyển vào thư mục
cd /Users/trghoangminh/Desktop/DM

# Cài đặt (chỉ lần đầu)
pip3 install -r requirements.txt
playwright install chromium

# Chạy scraper
python3 mogi_multi_scraper.py

# Sau khi xong, làm sạch dữ liệu
python3 clean_data.py
```

---

## 🐛 Xử Lý Lỗi Thường Gặp

### Lỗi: "No module named 'playwright'"

```bash
pip3 install playwright
playwright install chromium
```

### Lỗi: "No module named 'bs4'"

```bash
pip3 install beautifulsoup4 lxml
```

### Lỗi: "Executable doesn't exist"

```bash
playwright install chromium
```

### Lỗi: "Permission denied"

```bash
sudo pip3 install -r requirements.txt
```

---

## 🎯 Các Script Có Sẵn

| Script | Mô tả | Cách chạy |
|--------|-------|-----------|
| `mogi_multi_scraper.py` | Crawl nhiều danh mục (TỐT NHẤT) | `python3 mogi_multi_scraper.py` |
| `mogi_scraper.py` | Crawl đơn giản (cũ) | `python3 mogi_scraper.py` |
| `clean_data.py` | Làm sạch dữ liệu | `python3 clean_data.py` |
| `analyze_data.py` | Phân tích dữ liệu | `python3 analyze_data.py` |

---

## 📊 Workflow Hoàn Chỉnh

```bash
# 1. Setup (lần đầu)
pip3 install -r requirements.txt
playwright install chromium

# 2. Crawl dữ liệu
python3 mogi_multi_scraper.py
# Đợi 4-6 giờ...

# 3. Làm sạch
python3 clean_data.py

# 4. Phân tích
python3 analyze_data.py
```

---

## 🔍 Kiểm Tra Cài Đặt

```bash
# Kiểm tra Python version
python3 --version
# Kỳ vọng: Python 3.8+

# Kiểm tra pip
pip3 --version

# Kiểm tra Playwright
python3 -c "import playwright; print('OK')"

# Kiểm tra BeautifulSoup
python3 -c "import bs4; print('OK')"
```

---

## 💾 Backup & Restore

### Backup dữ liệu đã crawl:

```bash
cp mogi_hanoi_*_cleaned.csv ~/Desktop/backup_data.csv
```

### Xóa dữ liệu cũ để chạy lại:

```bash
rm mogi_hanoi_*.csv
```

---

## 🎓 Cho Máy Mới / Môi Trường Mới

```bash
# 1. Clone/Copy project
cd ~/Desktop
# (Copy folder DM vào đây)

# 2. Cài Python 3 (nếu chưa có)
# Download từ: https://www.python.org/downloads/

# 3. Cài dependencies
cd ~/Desktop/DM
pip3 install -r requirements.txt
playwright install chromium

# 4. Chạy
python3 mogi_multi_scraper.py
```

---

## ✅ Checklist Setup

- [ ] Python 3.8+ đã cài
- [ ] Đã chạy `pip3 install -r requirements.txt`
- [ ] Đã chạy `playwright install chromium`
- [ ] Test: `python3 -c "import playwright; print('OK')"`
- [ ] Sẵn sàng chạy scraper!

---

**Mọi thứ đã sẵn sàng! Chạy `python3 mogi_multi_scraper.py` để bắt đầu!** 🚀

"""
Mogi.vn Real Estate Scraper for Hanoi
Dự án Data Mining - Bất động sản Hà Nội

Mục đích: Thu thập dữ liệu bất động sản từ mogi.vn khu vực Hà Nội
Phương pháp: Playwright + BeautifulSoup
Ưu điểm: Mogi.vn KHÔNG có Cloudflare protection!
"""

import csv
import time
import random
from datetime import datetime
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import re

class MogiScraper:
    def __init__(self):
        self.base_url = "https://mogi.vn"
        self.hanoi_url = "https://mogi.vn/ha-noi/mua-mat-bang-cua-hang-shop"  # Mặt bằng Hà Nội
        self.data = []
        
    def random_delay(self, min_seconds=2, max_seconds=4):
        """Tạo delay ngẫu nhiên giữa các request"""
        delay = random.uniform(min_seconds, max_seconds)
        print(f"⏳ Đợi {delay:.2f} giây...")
        time.sleep(delay)
    
    def clean_text(self, text):
        """Làm sạch text"""
        if not text:
            return None
        return ' '.join(text.strip().split())
    
    def extract_price(self, price_text):
        """Trích xuất giá"""
        if not price_text:
            return None
        price_text = self.clean_text(price_text)
        # Giữ nguyên format: "5 tỷ", "500 triệu"
        return price_text
    
    def extract_area(self, area_text):
        """Trích xuất diện tích"""
        if not area_text:
            return None
        # Format: "50 m²"
        match = re.search(r'([\d.,]+)\s*m[²2]', area_text)
        if match:
            return f"{match.group(1)} m²"
        return self.clean_text(area_text)
    
    def parse_listing_page(self, html_content):
        """Parse trang danh sách để lấy links các bài đăng"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        links = []
        
        # Mogi.vn sử dụng class 'link-overlay' cho links chi tiết
        link_elements = soup.select('a.link-overlay')
        
        for elem in link_elements:
            href = elem.get('href', '')
            if href:
                # Nếu là relative URL, thêm base_url
                if href.startswith('/'):
                    full_url = self.base_url + href
                elif href.startswith('http'):
                    full_url = href
                else:
                    continue
                
                # CHỈ LẤY URLs có pattern listing thật: /quan-*/mua-*/...-id[số]
                # Loại bỏ: /gia-nha-dat, /10-buoc-mua-nha, etc.
                if re.search(r'-id\d+$', full_url) and full_url not in links:
                    links.append(full_url)
        
        print(f"✅ Tìm thấy {len(links)} bài đăng hợp lệ trên trang")
        return links
    
    def parse_detail_page(self, html_content, url):
        """Parse trang chi tiết để lấy thông tin bất động sản"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        property_data = {
            'url': url,
            'price': None,
            'area': None,
            'address': None,
            'district': None,
            'bedrooms': None,
            'bathrooms': None,
            'property_type': None,
            'posted_date': None,
            'description': None
        }
        
        # Giá
        price_elem = soup.select_one('.price')
        if price_elem:
            property_data['price'] = self.extract_price(price_elem.get_text())
        
        # Địa chỉ
        address_elem = soup.select_one('.address')
        if address_elem:
            address_text = self.clean_text(address_elem.get_text())
            property_data['address'] = address_text
            
            # Trích xuất quận từ địa chỉ
            # Format: "Đường ABC, Phường XYZ, Quận Hoàn Kiếm, Hà Nội"
            parts = address_text.split(',')
            for part in parts:
                part = part.strip()
                if 'quận' in part.lower() or 'huyện' in part.lower():
                    property_data['district'] = part
                    break
        
        # Các thông tin từ info-attr
        info_attrs = soup.select('.info-attr')
        for attr in info_attrs:
            spans = attr.find_all('span')
            if len(spans) >= 2:
                label = self.clean_text(spans[0].get_text()).lower()
                value = self.clean_text(spans[-1].get_text())
                
                if 'diện tích' in label:
                    property_data['area'] = self.extract_area(value)
                elif 'phòng ngủ' in label:
                    property_data['bedrooms'] = value
                elif 'nhà tắm' in label or 'toilet' in label:
                    property_data['bathrooms'] = value
                elif 'ngày đăng' in label:
                    property_data['posted_date'] = value
        
        # Loại hình từ breadcrumb
        breadcrumbs = soup.select('.breadcrumb li a')
        if breadcrumbs:
            # Lấy phần tử cuối cùng
            property_data['property_type'] = self.clean_text(breadcrumbs[-1].get_text())
        
        # Mô tả
        # Thử nhiều selector
        desc_selectors = ['.introduction', '.property-description', '.info-content-body']
        for selector in desc_selectors:
            desc_elem = soup.select_one(selector)
            if desc_elem:
                desc_text = self.clean_text(desc_elem.get_text())
                property_data['description'] = desc_text[:500]  # Giới hạn 500 ký tự
                break
        
        return property_data
    
    def scrape(self, max_pages=3, max_items_per_page=10, auto_save=True):
        """
        Hàm chính để crawl dữ liệu
        
        Args:
            max_pages: Số trang tối đa cần crawl
            max_items_per_page: Số bài đăng tối đa mỗi trang
            auto_save: Tự động lưu sau mỗi trang (tránh mất dữ liệu)
        """
        print("🚀 Bắt đầu crawl dữ liệu từ Mogi.vn")
        print(f"📍 Khu vực: Hà Nội")
        print(f"📄 Số trang tối đa: {max_pages}")
        print(f"💾 Auto-save: {'Bật' if auto_save else 'Tắt'}")
        print("-" * 60)
        
        with sync_playwright() as p:
            # Khởi tạo browser
            browser = p.chromium.launch(
                headless=False,  # Đặt True để chạy ngầm
                args=['--disable-blink-features=AutomationControlled']
            )
            
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080},
                locale='vi-VN',
            )
            
            page = context.new_page()
            
            # Crawl từng trang danh sách
            for page_num in range(1, max_pages + 1):
                print(f"\n📄 Đang crawl trang {page_num}/{max_pages}")
                
                # URL pagination: /ha-noi/mua-nha-dat?page=2
                if page_num == 1:
                    url = self.hanoi_url
                else:
                    url = f"{self.hanoi_url}?page={page_num}"
                
                try:
                    print(f"🌐 Đang truy cập: {url}")
                    page.goto(url, wait_until='domcontentloaded', timeout=30000)
                    
                    # Đợi listings load
                    time.sleep(2)
                    
                    # Scroll để load lazy content
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(1)
                    
                    # Lấy HTML content
                    html_content = page.content()
                    
                    # Parse để lấy links
                    listing_links = self.parse_listing_page(html_content)
                    
                    if not listing_links:
                        print("⚠️  Không tìm thấy bài đăng nào")
                        break
                    
                    # Giới hạn số bài đăng mỗi trang
                    listing_links = listing_links[:max_items_per_page]
                    
                    # Crawl từng bài đăng chi tiết
                    for idx, detail_url in enumerate(listing_links, 1):
                        print(f"\n  📌 [{idx}/{len(listing_links)}] Đang crawl: {detail_url}")
                        
                        try:
                            page.goto(detail_url, wait_until='domcontentloaded', timeout=30000)
                            time.sleep(1)
                            
                            # Scroll để load hết nội dung
                            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                            time.sleep(1)
                            
                            detail_html = page.content()
                            property_data = self.parse_detail_page(detail_html, detail_url)
                            
                            self.data.append(property_data)
                            print(f"  ✅ Đã lấy dữ liệu: {property_data['price']} - {property_data['area']}")
                            
                        except Exception as e:
                            print(f"  ❌ Lỗi khi crawl chi tiết: {e}")
                        
                        # Delay giữa các request
                        self.random_delay(2, 3)
                    
                    # Auto-save sau mỗi trang (tránh mất dữ liệu khi dừng giữa chừng)
                    if auto_save and self.data:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        temp_filename = f"mogi_hanoi_{timestamp}_temp.csv"
                        self.save_to_csv(temp_filename)
                        print(f"  💾 Đã lưu tạm {len(self.data)} bài vào: {temp_filename}")
                    
                except Exception as e:
                    print(f"❌ Lỗi khi crawl trang {page_num}: {e}")
                
                # Delay giữa các trang
                self.random_delay(3, 5)
            
            browser.close()
        
        print(f"\n{'='*60}")
        print(f"✅ Hoàn thành! Đã crawl được {len(self.data)} bài đăng")
        print(f"{'='*60}")
    
    def save_to_csv(self, filename='mogi_hanoi_data.csv'):
        """Lưu dữ liệu ra file CSV"""
        if not self.data:
            print("⚠️  Không có dữ liệu để lưu")
            return
        
        fieldnames = ['url', 'price', 'area', 'address', 'district', 'bedrooms', 
                     'bathrooms', 'property_type', 'posted_date', 'description']
        
        with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.data)
        
        print(f"💾 Đã lưu {len(self.data)} bản ghi vào file: {filename}")
        print(f"📊 Các cột: {', '.join(fieldnames)}")


def main():
    """Hàm main để chạy scraper"""
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║       MOGI.VN SCRAPER - DỰ ÁN DATA MINING HÀ NỘI       ║
    ║              ✅ KHÔNG CÓ CLOUDFLARE BLOCK!              ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    scraper = MogiScraper()
    
    # Cấu hình crawl - Mặt bằng/cửa hàng ít trùng lặp hơn
    MAX_PAGES = 30         # 30 trang cho mặt bằng
    MAX_ITEMS_PER_PAGE = 20  # 20 bài đăng mỗi trang
    # Dự kiến: ~600 bài → sau loại trùng: ~150-300 bài duy nhất (ít trùng hơn)
    
    print(f"⚙️  Cấu hình:")
    print(f"   - Số trang: {MAX_PAGES}")
    print(f"   - Số bài đăng/trang: {MAX_ITEMS_PER_PAGE}")
    print(f"   - Tổng dự kiến: ~{MAX_PAGES * MAX_ITEMS_PER_PAGE} bài đăng")
    print()
    
    # Bắt đầu crawl
    scraper.scrape(max_pages=MAX_PAGES, max_items_per_page=MAX_ITEMS_PER_PAGE)
    
    # Lưu dữ liệu
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"mogi_hanoi_{timestamp}.csv"
    scraper.save_to_csv(filename)
    
    print(f"\n✨ Hoàn tất! Kiểm tra file: {filename}")
    print(f"\n📊 Để phân tích dữ liệu, chạy:")
    print(f"   python3 analyze_data.py")


if __name__ == "__main__":
    main()

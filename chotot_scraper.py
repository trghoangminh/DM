"""
Chotot.com Real Estate Scraper for Hanoi
Dự án Data Mining - Bất động sản Hà Nội

Mục đích: Thu thập dữ liệu bất động sản từ chotot.com khu vực Hà Nội
Phương pháp: Playwright (xử lý JavaScript) + BeautifulSoup (parse HTML)
"""

import csv
import time
import random
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import re
import json

class ChoTotScraper:
    def __init__(self):
        # Chotot.com redirect sang nhatot.com cho bất động sản
        self.base_url = "https://www.nhatot.com"
        self.hanoi_url = "https://www.nhatot.com/mua-ban-bat-dong-san-ha-noi"
        self.data = []
        
    def random_delay(self, min_seconds=2, max_seconds=5):
        """Tạo delay ngẫu nhiên giữa các request để tránh bị block"""
        delay = random.uniform(min_seconds, max_seconds)
        print(f"⏳ Đợi {delay:.2f} giây...")
        time.sleep(delay)
    
    def extract_price(self, text):
        """Trích xuất giá từ text"""
        if not text:
            return None
        # Xử lý các format: "5 tỷ", "500 triệu", "5.5 tỷ"
        text = text.lower().strip()
        if 'tỷ' in text:
            number = re.findall(r'[\d.,]+', text)
            if number:
                return f"{number[0]} tỷ"
        elif 'triệu' in text:
            number = re.findall(r'[\d.,]+', text)
            if number:
                return f"{number[0]} triệu"
        elif 'thỏa thuận' in text or 'thoa thuan' in text:
            return "Thỏa thuận"
        return text
    
    def extract_area(self, text):
        """Trích xuất diện tích từ text"""
        if not text:
            return None
        # Format: "50 m²", "50m2"
        match = re.search(r'([\d.,]+)\s*m[²2]', text.lower())
        if match:
            return f"{match.group(1)} m²"
        return text
    
    def parse_listing_page(self, html_content):
        """Parse trang danh sách để lấy links các bài đăng"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Nhatot.com sử dụng links kết thúc bằng .htm cho detail pages
        # Pattern: /mua-ban-nha-dat-{district}/{id}.htm
        links = []
        
        # Tìm tất cả links có .htm (đây là detail pages)
        all_links = soup.find_all('a', href=True)
        for link in all_links:
            href = link['href']
            
            # Chỉ lấy links kết thúc bằng .htm (detail pages)
            if href.endswith('.htm'):
                # Nếu là relative URL, thêm base_url
                if href.startswith('/'):
                    full_url = self.base_url + href
                elif href.startswith('http'):
                    full_url = href
                else:
                    continue
                
                # Chỉ lấy links bất động sản Hà Nội
                if 'ha-noi' in full_url.lower() and full_url not in links:
                    links.append(full_url)
        
        print(f"✅ Tìm thấy {len(links)} bài đăng trên trang")
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
        
        # Thử tìm JSON-LD data (nhiều website dùng structured data)
        json_ld = soup.find('script', type='application/ld+json')
        if json_ld:
            try:
                data = json.loads(json_ld.string)
                if isinstance(data, dict):
                    property_data['price'] = data.get('offers', {}).get('price')
                    property_data['address'] = data.get('address', {}).get('streetAddress')
            except:
                pass
        
        # Tìm giá
        price_selectors = [
            {'class': re.compile(r'.*price.*', re.I)},
            {'class': re.compile(r'.*gia.*', re.I)},
            '[itemprop="price"]',
        ]
        for selector in price_selectors:
            if isinstance(selector, dict):
                elem = soup.find(attrs=selector)
            else:
                elem = soup.select_one(selector)
            if elem:
                property_data['price'] = self.extract_price(elem.get_text(strip=True))
                break
        
        # Tìm diện tích
        area_selectors = [
            {'class': re.compile(r'.*area.*', re.I)},
            {'class': re.compile(r'.*dien.*tich.*', re.I)},
        ]
        for selector in area_selectors:
            elem = soup.find(attrs=selector)
            if elem:
                property_data['area'] = self.extract_area(elem.get_text(strip=True))
                break
        
        # Tìm địa chỉ
        address_selectors = [
            {'class': re.compile(r'.*address.*', re.I)},
            {'class': re.compile(r'.*dia.*chi.*', re.I)},
            '[itemprop="address"]',
        ]
        for selector in address_selectors:
            if isinstance(selector, dict):
                elem = soup.find(attrs=selector)
            else:
                elem = soup.select_one(selector)
            if elem:
                property_data['address'] = elem.get_text(strip=True)
                # Trích xuất quận/huyện từ địa chỉ
                address_text = property_data['address']
                district_match = re.search(r'(Quận|Huyện)\s+([^,]+)', address_text)
                if district_match:
                    property_data['district'] = f"{district_match.group(1)} {district_match.group(2).strip()}"
                break
        
        # Tìm các thông tin khác trong bảng thông số
        # Chotot thường có bảng thông số kỹ thuật
        spec_rows = soup.find_all(['tr', 'div'], class_=re.compile(r'.*(spec|attribute|param).*', re.I))
        
        for row in spec_rows:
            text = row.get_text().lower()
            
            # Số phòng ngủ
            if 'phòng ngủ' in text or 'bedroom' in text:
                numbers = re.findall(r'\d+', text)
                if numbers:
                    property_data['bedrooms'] = numbers[0]
            
            # Số phòng tắm
            if 'phòng tắm' in text or 'toilet' in text or 'bathroom' in text:
                numbers = re.findall(r'\d+', text)
                if numbers:
                    property_data['bathrooms'] = numbers[0]
            
            # Loại hình
            if 'loại hình' in text or 'property type' in text or 'loại bds' in text:
                property_data['property_type'] = row.get_text(strip=True).split(':')[-1].strip()
        
        # Tìm ngày đăng
        date_selectors = [
            {'class': re.compile(r'.*date.*', re.I)},
            {'class': re.compile(r'.*time.*', re.I)},
            '[itemprop="datePublished"]',
        ]
        for selector in date_selectors:
            if isinstance(selector, dict):
                elem = soup.find(attrs=selector)
            else:
                elem = soup.select_one(selector)
            if elem:
                date_text = elem.get_text(strip=True)
                property_data['posted_date'] = date_text
                break
        
        # Tìm mô tả
        desc_selectors = [
            {'class': re.compile(r'.*description.*', re.I)},
            {'class': re.compile(r'.*mo.*ta.*', re.I)},
            '[itemprop="description"]',
        ]
        for selector in desc_selectors:
            if isinstance(selector, dict):
                elem = soup.find(attrs=selector)
            else:
                elem = soup.select_one(selector)
            if elem:
                property_data['description'] = elem.get_text(strip=True)[:500]  # Giới hạn 500 ký tự
                break
        
        return property_data
    
    def scrape(self, max_pages=5, max_items_per_page=20):
        """
        Hàm chính để crawl dữ liệu
        
        Args:
            max_pages: Số trang tối đa cần crawl
            max_items_per_page: Số bài đăng tối đa mỗi trang
        """
        print("🚀 Bắt đầu crawl dữ liệu từ Chotot.com")
        print(f"📍 Khu vực: Hà Nội")
        print(f"📄 Số trang tối đa: {max_pages}")
        print("-" * 60)
        
        with sync_playwright() as p:
            # Khởi tạo browser với options để tránh bị phát hiện
            browser = p.chromium.launch(
                headless=False,  # Đặt True để chạy ngầm, False để xem quá trình
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                ]
            )
            
            # Tạo context với user agent giống người dùng thật
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080},
                locale='vi-VN',
            )
            
            page = context.new_page()
            
            # Crawl từng trang danh sách
            for page_num in range(1, max_pages + 1):
                print(f"\n📄 Đang crawl trang {page_num}/{max_pages}")
                
                # URL có thể có pagination: ?page=1, ?page=2, etc.
                if page_num == 1:
                    url = self.hanoi_url
                else:
                    url = f"{self.hanoi_url}?page={page_num}"
                
                try:
                    # Truy cập trang danh sách
                    print(f"🌐 Đang truy cập: {url}")
                    page.goto(url, wait_until='networkidle', timeout=30000)
                    
                    # Scroll để load lazy content
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(2)
                    
                    # Lấy HTML content
                    html_content = page.content()
                    
                    # Parse để lấy links
                    listing_links = self.parse_listing_page(html_content)
                    
                    if not listing_links:
                        print("⚠️  Không tìm thấy bài đăng nào, có thể đã hết trang hoặc cần cập nhật selector")
                        break
                    
                    # Giới hạn số bài đăng mỗi trang
                    listing_links = listing_links[:max_items_per_page]
                    
                    # Crawl từng bài đăng chi tiết
                    for idx, detail_url in enumerate(listing_links, 1):
                        print(f"\n  📌 [{idx}/{len(listing_links)}] Đang crawl: {detail_url}")
                        
                        try:
                            page.goto(detail_url, wait_until='networkidle', timeout=30000)
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
                        self.random_delay(2, 4)
                    
                except Exception as e:
                    print(f"❌ Lỗi khi crawl trang {page_num}: {e}")
                
                # Delay giữa các trang
                self.random_delay(3, 6)
            
            browser.close()
        
        print(f"\n{'='*60}")
        print(f"✅ Hoàn thành! Đã crawl được {len(self.data)} bài đăng")
        print(f"{'='*60}")
    
    def save_to_csv(self, filename='chotot_hanoi_data.csv'):
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
    ║     CHOTOT.COM SCRAPER - DỰ ÁN DATA MINING HÀ NỘI      ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    scraper = ChoTotScraper()
    
    # Cấu hình crawl
    MAX_PAGES = 3          # Số trang cần crawl (bắt đầu với 3 trang để test)
    MAX_ITEMS_PER_PAGE = 10  # Số bài đăng mỗi trang (bắt đầu với 10 để test)
    
    print(f"⚙️  Cấu hình:")
    print(f"   - Số trang: {MAX_PAGES}")
    print(f"   - Số bài đăng/trang: {MAX_ITEMS_PER_PAGE}")
    print(f"   - Tổng dự kiến: ~{MAX_PAGES * MAX_ITEMS_PER_PAGE} bài đăng")
    print()
    
    # Bắt đầu crawl
    scraper.scrape(max_pages=MAX_PAGES, max_items_per_page=MAX_ITEMS_PER_PAGE)
    
    # Lưu dữ liệu
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"chotot_hanoi_{timestamp}.csv"
    scraper.save_to_csv(filename)
    
    print(f"\n✨ Hoàn tất! Kiểm tra file: {filename}")


if __name__ == "__main__":
    main()

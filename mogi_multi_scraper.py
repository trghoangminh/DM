#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mogi.vn Multi-Category Scraper - Tránh trùng lặp bằng cách crawl nhiều danh mục
"""

import time
import random
import re
from datetime import datetime
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import csv

class MogiMultiCategoryScraper:
    def __init__(self):
        self.base_url = "https://mogi.vn"
        
        # CHIẾN LƯỢC: Crawl nhiều loại hình BĐS khác nhau
        self.categories = [
            "/ha-noi/mua-can-ho",                    # Căn hộ
            "/ha-noi/mua-nha-rieng",                 # Nhà riêng
            "/ha-noi/mua-nha-mat-tien-pho",          # Nhà mặt phố
            "/ha-noi/mua-nha-biet-thu-lien-ke",      # Biệt thự
            "/ha-noi/mua-dat-nen-du-an",             # Đất nền
            "/ha-noi/mua-mat-bang-cua-hang-shop",    # Mặt bằng
        ]
        
        self.data = []
        self.seen_urls = set()  # Track URLs đã crawl để tránh trùng
        
    def random_delay(self, min_seconds=2, max_seconds=4):
        delay = random.uniform(min_seconds, max_seconds)
        print(f"⏳ Đợi {delay:.2f} giây...")
        time.sleep(delay)
    
    def clean_text(self, text):
        if not text:
            return None
        return ' '.join(text.split()).strip()
    
    def extract_price(self, price_text):
        if not price_text:
            return None
        price_text = self.clean_text(price_text)
        return price_text
    
    def extract_area(self, area_text):
        if not area_text:
            return None
        area_text = self.clean_text(area_text)
        return area_text
    
    def parse_listing_page(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        links = []
        link_elements = soup.select('a.link-overlay')
        
        for elem in link_elements:
            href = elem.get('href', '')
            if href:
                if href.startswith('/'):
                    full_url = self.base_url + href
                elif href.startswith('http'):
                    full_url = href
                else:
                    continue
                
                # Chỉ lấy URLs hợp lệ và chưa crawl
                if re.search(r'-id\d+$', full_url) and full_url not in self.seen_urls:
                    links.append(full_url)
                    self.seen_urls.add(full_url)  # Đánh dấu đã thấy
        
        return links
    
    def parse_detail_page(self, html_content, url):
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
            
            # Trích xuất quận
            parts = address_text.split(',')
            for part in parts:
                part = part.strip()
                if 'quận' in part.lower() or 'huyện' in part.lower():
                    property_data['district'] = part
                    break
        
        # Thông tin từ info-attr
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
        
        # Loại hình
        breadcrumbs = soup.select('.breadcrumb li a')
        if breadcrumbs:
            property_data['property_type'] = self.clean_text(breadcrumbs[-1].get_text())
        
        # Mô tả
        desc_selectors = ['.introduction', '.property-description', '.info-content-body']
        for selector in desc_selectors:
            desc_elem = soup.select_one(selector)
            if desc_elem:
                desc_text = self.clean_text(desc_elem.get_text())
                property_data['description'] = desc_text[:500]
                break
        
        return property_data
    
    def scrape_category(self, category_url, max_pages=5, max_items_per_page=20):
        """Crawl một danh mục cụ thể"""
        print(f"\n{'='*60}")
        print(f"📂 Đang crawl danh mục: {category_url}")
        print(f"{'='*60}")
        
        category_data = []
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                viewport={'width': 1920, 'height': 1080},
                locale='vi-VN',
            )
            page = context.new_page()
            
            for page_num in range(1, max_pages + 1):
                print(f"\n📄 Trang {page_num}/{max_pages}")
                
                if page_num == 1:
                    url = self.base_url + category_url
                else:
                    url = f"{self.base_url}{category_url}?page={page_num}"
                
                try:
                    page.goto(url, wait_until='domcontentloaded', timeout=30000)
                    time.sleep(2)
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(1)
                    
                    html_content = page.content()
                    listing_links = self.parse_listing_page(html_content)
                    
                    if not listing_links:
                        print("⚠️  Không có bài mới")
                        break
                    
                    print(f"✅ Tìm thấy {len(listing_links)} bài MỚI (chưa crawl)")
                    
                    listing_links = listing_links[:max_items_per_page]
                    
                    for idx, detail_url in enumerate(listing_links, 1):
                        print(f"  📌 [{idx}/{len(listing_links)}] {detail_url}")
                        
                        try:
                            page.goto(detail_url, wait_until='domcontentloaded', timeout=30000)
                            time.sleep(1)
                            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                            time.sleep(1)
                            
                            detail_html = page.content()
                            property_data = self.parse_detail_page(detail_html, detail_url)
                            
                            category_data.append(property_data)
                            self.data.append(property_data)
                            print(f"  ✅ {property_data['price']} - {property_data['area']}")
                            
                        except Exception as e:
                            print(f"  ❌ Lỗi: {e}")
                        
                        self.random_delay(2, 3)
                    
                except Exception as e:
                    print(f"❌ Lỗi trang {page_num}: {e}")
                
                self.random_delay(3, 5)
            
            browser.close()
        
        print(f"\n✅ Danh mục này: {len(category_data)} bài")
        return category_data
    
    def save_to_csv(self, filename=None):
        if not self.data:
            print("⚠️  Không có dữ liệu để lưu")
            return
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"mogi_hanoi_multicategory_{timestamp}.csv"
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['url', 'price', 'area', 'address', 'district', 
                         'bedrooms', 'bathrooms', 'property_type', 'posted_date', 'description']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.data)
        
        print(f"\n💾 Đã lưu {len(self.data)} bản ghi vào: {filename}")
        return filename

def main():
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║    MOGI.VN MULTI-CATEGORY SCRAPER - TRÁNH TRÙNG LẶP    ║
    ║         Crawl nhiều danh mục để lấy dữ liệu đa dạng      ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    scraper = MogiMultiCategoryScraper()
    
    # CẤU HÌNH TỐI ĐA - LẤY NHIỀU DỮ LIỆU NHẤT
    PAGES_PER_CATEGORY = 50  # 50 trang/danh mục (tối đa)
    ITEMS_PER_PAGE = 20      # 20 bài/trang
    
    print(f"⚙️  CẤU HÌNH TỐI ĐA:")
    print(f"   - Số danh mục: {len(scraper.categories)}")
    print(f"   - Số trang/danh mục: {PAGES_PER_CATEGORY}")
    print(f"   - Số bài/trang: {ITEMS_PER_PAGE}")
    print(f"   - Dự kiến: ~{len(scraper.categories) * PAGES_PER_CATEGORY * 20} bài")
    print(f"   - Kỳ vọng sau loại trùng: 500-1000 bài duy nhất")
    print(f"   - Thời gian ước tính: 4-6 giờ")
    print(f"\n💡 Khuyến nghị: Chạy qua đêm!")
    
    # Crawl từng danh mục
    for category in scraper.categories:
        scraper.scrape_category(category, max_pages=PAGES_PER_CATEGORY, max_items_per_page=ITEMS_PER_PAGE)
    
    # Lưu kết quả
    filename = scraper.save_to_csv()
    
    print(f"\n{'='*60}")
    print(f"✅ HOÀN THÀNH!")
    print(f"   - Tổng số bài: {len(scraper.data)}")
    print(f"   - Số URLs duy nhất: {len(scraper.seen_urls)}")
    print(f"   - File: {filename}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()

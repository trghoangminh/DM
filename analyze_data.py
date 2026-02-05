"""
Script demo để đọc và phân tích dữ liệu đã crawl
Sử dụng Pandas để xử lý file CSV
"""

import pandas as pd
import glob
import os

def analyze_data():
    """Phân tích dữ liệu bất động sản đã crawl"""
    
    # Tìm file CSV mới nhất
    csv_files = glob.glob('chotot_hanoi_*.csv')
    
    if not csv_files:
        print("❌ Không tìm thấy file CSV nào. Hãy chạy chotot_scraper.py trước.")
        return
    
    # Lấy file mới nhất
    latest_file = max(csv_files, key=os.path.getctime)
    print(f"📂 Đang đọc file: {latest_file}")
    print("-" * 60)
    
    # Đọc CSV
    df = pd.read_csv(latest_file)
    
    # Thông tin cơ bản
    print("\n📊 THÔNG TIN TỔNG QUAN")
    print(f"Tổng số bài đăng: {len(df)}")
    print(f"Số cột: {len(df.columns)}")
    print(f"\nCác cột: {', '.join(df.columns.tolist())}")
    
    # Hiển thị 5 dòng đầu
    print("\n📋 5 BÀI ĐĂNG ĐẦU TIÊN:")
    print(df.head())
    
    # Thống kê dữ liệu thiếu
    print("\n⚠️  THỐNG KÊ DỮ LIỆU THIẾU:")
    missing = df.isnull().sum()
    missing_percent = (missing / len(df)) * 100
    missing_df = pd.DataFrame({
        'Số lượng thiếu': missing,
        'Phần trăm (%)': missing_percent.round(2)
    })
    print(missing_df[missing_df['Số lượng thiếu'] > 0])
    
    # Thống kê theo quận/huyện
    if 'district' in df.columns:
        print("\n📍 THỐNG KÊ THEO QUẬN/HUYỆN:")
        district_counts = df['district'].value_counts().head(10)
        print(district_counts)
    
    # Thống kê loại hình BĐS
    if 'property_type' in df.columns:
        print("\n🏠 THỐNG KÊ THEO LOẠI HÌNH:")
        property_counts = df['property_type'].value_counts()
        print(property_counts)
    
    # Thống kê số phòng ngủ
    if 'bedrooms' in df.columns:
        print("\n🛏️  THỐNG KÊ SỐ PHÒNG NGỦ:")
        bedroom_counts = df['bedrooms'].value_counts().sort_index()
        print(bedroom_counts)
    
    # Lưu thống kê ra file
    stats_file = latest_file.replace('.csv', '_statistics.txt')
    with open(stats_file, 'w', encoding='utf-8') as f:
        f.write(f"THỐNG KÊ DỮ LIỆU: {latest_file}\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Tổng số bài đăng: {len(df)}\n")
        f.write(f"Số cột: {len(df.columns)}\n\n")
        f.write("Dữ liệu thiếu:\n")
        f.write(missing_df.to_string())
    
    print(f"\n💾 Đã lưu thống kê vào: {stats_file}")
    
    return df


def clean_price_data(df):
    """
    Làm sạch dữ liệu giá - chuyển về số (đơn vị: triệu VNĐ)
    VD: "5 tỷ" -> 5000, "500 triệu" -> 500
    """
    def convert_price(price_str):
        if pd.isna(price_str):
            return None
        
        price_str = str(price_str).lower()
        
        # Thỏa thuận
        if 'thỏa thuận' in price_str or 'thoa thuan' in price_str:
            return None
        
        # Tỷ
        if 'tỷ' in price_str:
            import re
            numbers = re.findall(r'[\d.,]+', price_str)
            if numbers:
                value = float(numbers[0].replace(',', '.'))
                return value * 1000  # Chuyển về triệu
        
        # Triệu
        if 'triệu' in price_str:
            import re
            numbers = re.findall(r'[\d.,]+', price_str)
            if numbers:
                value = float(numbers[0].replace(',', '.'))
                return value
        
        return None
    
    df['price_million'] = df['price'].apply(convert_price)
    return df


def clean_area_data(df):
    """
    Làm sạch dữ liệu diện tích - chuyển về số (đơn vị: m²)
    VD: "50 m²" -> 50.0
    """
    def convert_area(area_str):
        if pd.isna(area_str):
            return None
        
        import re
        area_str = str(area_str)
        match = re.search(r'([\d.,]+)', area_str)
        if match:
            return float(match.group(1).replace(',', '.'))
        return None
    
    df['area_m2'] = df['area'].apply(convert_area)
    return df


def main():
    """Hàm chính"""
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║         PHÂN TÍCH DỮ LIỆU BẤT ĐỘNG SẢN HÀ NỘI          ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    # Đọc và phân tích
    df = analyze_data()
    
    if df is not None:
        # Làm sạch dữ liệu
        print("\n🧹 ĐANG LÀM SẠCH DỮ LIỆU...")
        df = clean_price_data(df)
        df = clean_area_data(df)
        
        # Thống kê sau khi làm sạch
        if 'price_million' in df.columns:
            valid_prices = df['price_million'].dropna()
            if len(valid_prices) > 0:
                print("\n💰 THỐNG KÊ GIÁ (đơn vị: triệu VNĐ):")
                print(f"   - Giá trung bình: {valid_prices.mean():,.0f} triệu")
                print(f"   - Giá thấp nhất: {valid_prices.min():,.0f} triệu")
                print(f"   - Giá cao nhất: {valid_prices.max():,.0f} triệu")
                print(f"   - Giá trung vị: {valid_prices.median():,.0f} triệu")
        
        if 'area_m2' in df.columns:
            valid_areas = df['area_m2'].dropna()
            if len(valid_areas) > 0:
                print("\n📐 THỐNG KÊ DIỆN TÍCH (đơn vị: m²):")
                print(f"   - Diện tích trung bình: {valid_areas.mean():,.1f} m²")
                print(f"   - Diện tích nhỏ nhất: {valid_areas.min():,.1f} m²")
                print(f"   - Diện tích lớn nhất: {valid_areas.max():,.1f} m²")
                print(f"   - Diện tích trung vị: {valid_areas.median():,.1f} m²")
        
        # Tính giá/m² nếu có đủ dữ liệu
        if 'price_million' in df.columns and 'area_m2' in df.columns:
            df['price_per_m2'] = df['price_million'] / df['area_m2']
            valid_price_per_m2 = df['price_per_m2'].dropna()
            
            if len(valid_price_per_m2) > 0:
                print("\n💵 THỐNG KÊ GIÁ/M² (đơn vị: triệu VNĐ/m²):")
                print(f"   - Trung bình: {valid_price_per_m2.mean():,.2f} triệu/m²")
                print(f"   - Thấp nhất: {valid_price_per_m2.min():,.2f} triệu/m²")
                print(f"   - Cao nhất: {valid_price_per_m2.max():,.2f} triệu/m²")
                print(f"   - Trung vị: {valid_price_per_m2.median():,.2f} triệu/m²")
        
        print("\n✅ Hoàn tất phân tích!")


if __name__ == "__main__":
    # Cài đặt pandas nếu chưa có
    try:
        import pandas as pd
    except ImportError:
        print("❌ Chưa cài đặt pandas. Đang cài đặt...")
        import subprocess
        subprocess.check_call(['pip', 'install', 'pandas'])
        import pandas as pd
    
    main()

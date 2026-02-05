"""
Script làm sạch dữ liệu CSV - Loại bỏ trùng lặp và dữ liệu rác
"""

import pandas as pd
import sys

def clean_csv(input_file):
    """Làm sạch file CSV"""
    print(f"📂 Đang đọc file: {input_file}")
    
    # Đọc CSV
    df = pd.read_csv(input_file)
    print(f"📊 Tổng số dòng ban đầu: {len(df)}")
    
    # 1. Loại bỏ dòng có URL trùng lặp
    print("\n🔍 Loại bỏ URL trùng lặp...")
    before = len(df)
    df = df.drop_duplicates(subset=['url'], keep='first')
    after = len(df)
    print(f"   ✅ Đã xóa {before - after} dòng trùng")
    
    # 2. Loại bỏ dòng không có giá (dữ liệu rác)
    print("\n🔍 Loại bỏ dòng không có giá...")
    before = len(df)
    df = df[df['price'].notna()]
    after = len(df)
    print(f"   ✅ Đã xóa {before - after} dòng thiếu giá")
    
    # 3. Loại bỏ dòng không có diện tích
    print("\n🔍 Loại bỏ dòng không có diện tích...")
    before = len(df)
    df = df[df['area'].notna()]
    after = len(df)
    print(f"   ✅ Đã xóa {before - after} dòng thiếu diện tích")
    
    # 4. Loại bỏ các URL không phải listing (như /gia-nha-dat, /10-buoc-mua-nha)
    print("\n🔍 Loại bỏ URL không phải listing...")
    before = len(df)
    # Chỉ giữ URLs có pattern: /quan-*/mua-*/...-id*
    df = df[df['url'].str.contains(r'-id\d+$', na=False)]
    after = len(df)
    print(f"   ✅ Đã xóa {before - after} URL không hợp lệ")
    
    # 5. Reset index
    df = df.reset_index(drop=True)
    
    print(f"\n{'='*60}")
    print(f"✅ Kết quả: {len(df)} bài đăng duy nhất và hợp lệ")
    print(f"{'='*60}")
    
    # Lưu file mới
    output_file = input_file.replace('.csv', '_cleaned.csv')
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"\n💾 Đã lưu file sạch: {output_file}")
    
    # Hiển thị thống kê
    print(f"\n📊 THỐNG KÊ DỮ LIỆU SAU KHI LÀM SẠCH:")
    print(f"   - Tổng số bài đăng: {len(df)}")
    print(f"   - Số bài có đầy đủ giá + diện tích: {len(df)}")
    
    # Thống kê theo quận
    if 'district' in df.columns:
        print(f"\n📍 Phân bố theo quận:")
        district_counts = df['district'].value_counts()
        for district, count in district_counts.items():
            print(f"   - {district}: {count} bài")
    
    return output_file


if __name__ == "__main__":
    # Tìm file CSV mới nhất
    import glob
    import os
    
    csv_files = glob.glob('mogi_hanoi_*.csv')
    
    if not csv_files:
        print("❌ Không tìm thấy file CSV nào")
        sys.exit(1)
    
    # Loại bỏ file _cleaned.csv
    csv_files = [f for f in csv_files if '_cleaned' not in f]
    
    if not csv_files:
        print("❌ Không tìm thấy file CSV gốc")
        sys.exit(1)
    
    # Lấy file mới nhất
    latest_file = max(csv_files, key=os.path.getctime)
    
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║           LÀM SẠCH DỮ LIỆU - LOẠI BỎ TRÙNG LẶP         ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    cleaned_file = clean_csv(latest_file)
    
    # XÓA CÁC FILE THỪA
    print(f"\n🧹 Đang dọn dẹp các file thừa...")
    
    # 1. Xóa tất cả file _temp.csv
    temp_files = glob.glob('mogi_hanoi_*_temp.csv')
    if temp_files:
        for f in temp_files:
            try:
                os.remove(f)
                print(f"   ✅ Đã xóa: {f}")
            except:
                pass
        print(f"   💾 Đã xóa {len(temp_files)} file temp")
    
    # 2. Xóa các file _cleaned.csv cũ (giữ lại file mới nhất)
    old_cleaned = glob.glob('mogi_hanoi_*_cleaned.csv')
    old_cleaned = [f for f in old_cleaned if f != cleaned_file]
    if old_cleaned:
        for f in old_cleaned:
            try:
                os.remove(f)
                print(f"   ✅ Đã xóa file cũ: {f}")
            except:
                pass
        print(f"   💾 Đã xóa {len(old_cleaned)} file cleaned cũ")
    
    # 3. Xóa file CSV gốc (không phải cleaned)
    raw_files = glob.glob('mogi_hanoi_*.csv')
    raw_files = [f for f in raw_files if '_cleaned' not in f and '_temp' not in f]
    if raw_files:
        for f in raw_files:
            try:
                os.remove(f)
                print(f"   ✅ Đã xóa file gốc: {f}")
            except:
                pass
        print(f"   💾 Đã xóa {len(raw_files)} file gốc")
    
    print(f"\n✨ Hoàn tất! Chỉ còn file: {cleaned_file}")
    print(f"\n📊 Để phân tích dữ liệu sạch:")
    print(f"   import pandas as pd")
    print(f"   df = pd.read_csv('{cleaned_file}')")

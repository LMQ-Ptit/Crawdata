import json
import re

def extract_product_id(url):
    """Trích xuất ID sản phẩm từ URL Lazada"""
    # Tìm kiếm mẫu "i{số}-s" trong URL
    match = re.search(r'i(\d+)-s', url)
    if match:
        return match.group(1)  # Trả về ID sản phẩm
    return url  # Nếu không tìm thấy, trả về URL gốc

def deduplicate_product_links(input_file="product_links.json", output_file="product_links.json"):
    """Đọc file JSON, loại bỏ URL trùng lặp, và lưu lại"""
    try:
        # Đọc file JSON
        with open(input_file, 'r', encoding='utf-8') as f:
            product_links = json.load(f)
        
        # Đếm số lượng URL ban đầu
        original_count = len(product_links)
        print(f"Số lượng URL ban đầu: {original_count}")
        
        # Tạo dictionary để lưu URL theo ID sản phẩm
        unique_products = {}
        for url in product_links:
            product_id = extract_product_id(url)
            unique_products[product_id] = url
        
        # Lấy danh sách URL duy nhất
        unique_urls = list(unique_products.values())
        
        # Sắp xếp URL để đảm bảo kết quả ổn định
        unique_urls.sort()
        
        # Đếm số lượng URL sau khi loại bỏ trùng lặp
        unique_count = len(unique_urls)
        print(f"Số lượng URL sau khi loại bỏ trùng lặp: {unique_count}")
        print(f"Đã loại bỏ {original_count - unique_count} URL trùng lặp")
        
        # Ghi lại vào file JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(unique_urls, f, indent=2, ensure_ascii=False)
        
        print(f"Đã lưu danh sách URL không trùng lặp vào file {output_file}")
        
    except Exception as e:
        print(f"Lỗi: {e}")

if __name__ == "__main__":
    deduplicate_product_links()
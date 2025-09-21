from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options
import time
import json
import csv
import os

def setup_driver():
    """Thiết lập và trả về driver Selenium với các tùy chọn để giảm khả năng bị phát hiện"""
    chrome_options = Options()
    
    # Thêm user-agent để giả lập người dùng thực
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'
    chrome_options.add_argument(f'user-agent={user_agent}')
    
    # Vô hiệu hóa các thuộc tính có thể được sử dụng để phát hiện automation
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Thêm tùy chọn để tránh bị phát hiện là bot
    chrome_options.add_argument('--disable-infobars')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--no-sandbox')
    
    # Khởi tạo driver với các tùy chọn đã thiết lập
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    # Ghi đè các thuộc tính JavaScript để tránh phát hiện Selenium
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def count_stars(item_middle):
    """Đếm số sao từ thẻ div.container-star.review-star"""
    try:
        # Tìm container chứa các sao - Sửa CSS selector
        container_star = item_middle.find_element(By.CSS_SELECTOR, "div.container-star.review-star")
        
        # Tìm tất cả các thẻ img có class="star" (không phải start)
        star_imgs = container_star.find_elements(By.CSS_SELECTOR, "img.star")
        
        # Đếm số lượng sao (img có src đúng)
        star_count = 0
        star_src = "TB19ZvEgfDH8KJjy1XcXXcpdXXa-64-64.png"  # Dùng một phần URL để tìm
        
        for img in star_imgs:
            src = img.get_attribute("src")
            if src and star_src in src:
                star_count += 1
        
        return star_count
    except NoSuchElementException:
        # Giữ nguyên phần code phụ trợ này
        try:
            star_imgs = item_middle.find_elements(By.TAG_NAME, "img")
            star_count = 0
            star_src = "TB19ZvEgfDH8KJjy1XcXXcpdXXa-64-64.png"
            
            for img in star_imgs:
                src = img.get_attribute("src")
                if src and star_src in src:
                    star_count += 1
                    
            return star_count
        except:
            pass
        
        return 0    
    try:
        # Tìm container chứa các sao
        container_star = item_middle.find_element(By.CSS_SELECTOR, "div.")
        
        # Tìm tất cả các thẻ img có class="start"
        star_imgs = container_star.find_elements(By.CSS_SELECTOR, "img.start")
        
        # Đếm số lượng sao (img có src đúng)
        star_count = 0
        star_src = "https://img.lazcdn.com/g/tps/tfs/TB19ZvEgfDH8KJjy1XcXXcpdXXa-64-64.png"
        
        for img in star_imgs:
            if img.get_attribute("src") == star_src:
                star_count += 1
        
        return star_count
    except NoSuchElementException:
        # Thử cách khác: tìm tất cả img trong item_middle
        try:
            star_imgs = item_middle.find_elements(By.TAG_NAME, "img")
            star_count = 0
            star_src = "TB19ZvEgfDH8KJjy1XcXXcpdXXa-64-64.png"  # Chỉ tìm một phần của URL
            
            for img in star_imgs:
                src = img.get_attribute("src")
                if src and star_src in src:
                    star_count += 1
                    
            return star_count
        except:
            pass
        
        return 0

def get_review_content(item_content):
    """Lấy nội dung bình luận từ thẻ div.item-content-main-content-reviews-item"""
    try:
        review_content = item_content.find_element(By.CSS_SELECTOR, "div.item-content-main-content-reviews-item")
        return review_content.text.strip()
    except NoSuchElementException:
        # Nếu không tìm thấy thẻ cụ thể, lấy toàn bộ nội dung của item_content
        return item_content.text.strip()

def save_to_csv(reviews, filename="reviews.csv"):
    """Lưu danh sách bình luận vào file CSV với mode append"""
    # Kiểm tra xem file đã tồn tại chưa để quyết định có viết header hay không
    file_exists = os.path.exists(filename)
    
    # Tìm STT mới nhất trong file hiện có
    start_stt = 1
    if file_exists:
        try:
            with open(filename, 'r', encoding='utf-8', newline='') as f:
                # Đếm số dòng (trừ header)
                lines = sum(1 for line in f) - 1
                if lines > 0:
                    start_stt = lines + 1
        except:
            pass
    
    with open(filename, 'a', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        
        # Chỉ viết header nếu file chưa tồn tại
        if not file_exists:
            writer.writerow(["STT", "Nội dung bình luận", "Số sao"])
        
        # Viết dữ liệu
        for i, review in enumerate(reviews):
            writer.writerow([start_stt + i, review["content"], review["stars"]])
    
    print(f"Đã lưu {len(reviews)} bình luận vào file {filename}")

def crawl_lazada_reviews():
    """Hàm cào bình luận từ trang sản phẩm Lazada cụ thể"""
    # URL sản phẩm Lazada
    url = "https://www.lazada.vn/products/pdp-i1576166750-s14059010693.html"
    
    driver = setup_driver()
    reviews_data = []
    
    try:
        print(f"Đang truy cập URL: {url}")
        driver.get(url)
        
        # Đợi trang tải
        time.sleep(3)
        
        # Cuộn xuống để tìm phần bình luận
        print("Cuộn trang để tìm phần bình luận...")
        
        # Cuộn từ từ 5 lần để đảm bảo tải tất cả nội dung
        for i in range(5):
            driver.execute_script(f"window.scrollBy(0, 600)")
            time.sleep(0.5)
        
        # Tìm thẻ div có class="mod-reviews"
        print("Đang tìm thẻ div có class='mod-reviews'...")
        
        try:
            # Đợi tối đa 10 giây cho div mod-reviews xuất hiện
            reviews_div = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.mod-reviews"))
            )
            print("Đã tìm thấy thẻ div.mod-reviews!")
            
            # Tìm tất cả các thẻ div có class="item" trong mod-reviews
            items = reviews_div.find_elements(By.CSS_SELECTOR, "div.item")
            print(f"Tìm thấy {len(items)} bình luận")
            
            # Thu thập thông tin từ mỗi item (mỗi bình luận)
            reviews = []
            for i, item in enumerate(items):
                review_data = {}
                
                # Tìm thẻ div có class="item-middle" để đếm số sao
                try:
                    item_middle = item.find_element(By.CSS_SELECTOR, "div.item-middle")
                    stars = count_stars(item_middle)
                    review_data["stars"] = stars
                    print(f"Bình luận #{i+1} - Số sao: {stars}")
                except NoSuchElementException:
                    review_data["stars"] = 0
                    print(f"Bình luận #{i+1} - Không tìm thấy thẻ để đếm sao")
                
                # Tìm thẻ div có class="item-content" để lấy nội dung bình luận
                try:
                    item_content = item.find_element(By.CSS_SELECTOR, "div.item-content")
                    content = get_review_content(item_content)
                    review_data["content"] = content
                    print(f"Bình luận #{i+1} - Nội dung: {content[:50]}..." if len(content) > 50 else f"Bình luận #{i+1} - Nội dung: {content}")
                except NoSuchElementException:
                    review_data["content"] = "Không có nội dung bình luận"
                    print(f"Bình luận #{i+1} - Không tìm thấy nội dung bình luận")
                
                # Thêm vào danh sách reviews
                reviews.append(review_data)
            
            # Lưu reviews vào file CSV
            if reviews:
                save_to_csv(reviews, "reviews.csv")
                
        except TimeoutException:
            print("Không tìm thấy thẻ div có class='mod-reviews'")
            
            # Lưu source code trang để debug
            with open("page_source.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            print("Đã lưu source code trang vào file page_source.html")
        
    except Exception as e:
        print(f"Lỗi: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Đóng driver
        driver.quit()
        print("Đã đóng trình duyệt")
        
        return reviews_data

if __name__ == "__main__":
    crawl_lazada_reviews()
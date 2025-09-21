from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from selenium.webdriver.chrome.options import Options
import time
import csv

def count_stars(item_middle):
    """Đếm số sao đánh giá dựa trên src của img.star"""
    try:
        # Tìm tất cả thẻ img có class=star
        star_imgs = item_middle.find_elements(By.CSS_SELECTOR, "img.star")
        
        # Đếm số lượng sao (img có src phù hợp)
        star_count = 0
        star_src = "https://img.lazcdn.com/g/tps/tfs/TB19ZvEgfDH8KJjy1XcXXcpdXXa-64-64.png"
        
        for img in star_imgs:
            src = img.get_attribute("src")
            if src == star_src:
                star_count += 1
        
        return star_count
    except:
        return 0

def get_review_content(item_content):
    """Lấy nội dung bình luận từ thẻ div.item-content-main-content-reviews-item"""
    try:
        # Tìm thẻ div có class=item-content-main-content-reviews-item
        content_div = item_content.find_element(By.CSS_SELECTOR, "div.item-content-main-content-reviews-item")
        return content_div.text.strip()
    except NoSuchElementException:
        # Nếu không tìm thấy thẻ cụ thể, thử lấy toàn bộ nội dung của item-content
        try:
            return item_content.text.strip()
        except:
            return "Không có nội dung bình luận"
    except:
        return "Không có nội dung bình luận"

def setup_driver():
    """Thiết lập và trả về driver Selenium với tối ưu tốc độ"""
    chrome_options = Options()
    
    # Thêm user-agent để giả lập người dùng thực
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'
    chrome_options.add_argument(f'user-agent={user_agent}')
    
    # Vô hiệu hóa các thuộc tính có thể được sử dụng để phát hiện automation
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Thêm tùy chọn để tối ưu tốc độ
    chrome_options.add_argument('--disable-infobars')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-extensions')
    
    # Tắt tải hình ảnh để tăng tốc độ
    prefs = {"profile.managed_default_content_settings.images": 2}
    chrome_options.add_experimental_option("prefs", prefs)
    
    # Khởi tạo driver với các tùy chọn đã thiết lập
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    # Đặt timeout ngắn hơn
    driver.set_page_load_timeout(15)
    driver.implicitly_wait(1)
    
    # Ghi đè các thuộc tính JavaScript để tránh phát hiện Selenium
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def crawl_lazada_reviews():
    """Hàm cào bình luận từ trang sản phẩm Lazada với chức năng phân trang"""
    # URL sản phẩm Lazada
    url = "https://www.lazada.vn/products/pdp-i1576166750-s14059010693.html"
    
    driver = setup_driver()
    all_reviews = []  # Lưu tất cả bình luận
    current_page = 1
    max_pages = 30  # Giới hạn số trang tối đa để tránh vòng lặp vô hạn
    has_next_page = True
    
    try:
        print(f"Đang truy cập URL: {url}")
        driver.get(url)
        
        # Đợi ngắn để trang tải
        time.sleep(0.5)
        
        # Bắt đầu quá trình cào dữ liệu
        while has_next_page and current_page <= max_pages:
            print(f"\n--- Đang cào dữ liệu từ trang {current_page} ---")
            
            
            
            # Tìm thẻ div có class="mod-reviews"
            try:
                # Đợi tối đa 5 giây cho div mod-reviews xuất hiện (giảm từ 10s xuống 5s)
                reviews_div = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.mod-reviews"))
                )
                
                # Tìm tất cả các thẻ div có class="item" trong mod-reviews
                items = reviews_div.find_elements(By.CSS_SELECTOR, "div.item")
                print(f"Tìm thấy {len(items)} bình luận ở trang {current_page}")
                
                # Thu thập thông tin từ mỗi item (mỗi bình luận)
                page_reviews = []
                for i, item in enumerate(items):
                    review_data = {"page": current_page, "review_index": i+1}
                    
                    # Tìm thẻ div có class="item-middle" để đếm sao
                    try:
                        item_middle = item.find_element(By.CSS_SELECTOR, "div.item-middle")
                        star_count = count_stars(item_middle)
                        review_data["stars"] = star_count
                    except NoSuchElementException:
                        review_data["stars"] = 0
                    
                    # Tìm thẻ div có class="item-content" để lấy nội dung bình luận
                    try:
                        item_content = item.find_element(By.CSS_SELECTOR, "div.item-content")
                        review_content = get_review_content(item_content)
                        review_data["content"] = review_content
                    except NoSuchElementException:
                        review_data["content"] = "Không tìm thấy nội dung bình luận"
                
                    # Thêm vào danh sách kết quả
                    page_reviews.append(review_data)
                
                # Thêm bình luận của trang này vào danh sách tổng
                all_reviews.extend(page_reviews)
                    
                # Kiểm tra nút phân trang tiếp theo
                # Thử nhiều selector khác nhau để tìm nút "Next Page"
                next_button = None
                selectors = [
                    "button.iweb-pagination-item-link[title='Next Page']",
                    "li.iweb-pagination-next:not(.iweb-pagination-disabled) button",
                    "button[title*='Next'], button[aria-label*='Next']",
                    "[class*='next']:not([class*='disabled'])",
                    "//li[contains(@class, 'next') and not(contains(@class, 'disabled'))]/button"
                ]
                
                # Thử từng selector
                for selector in selectors:
                    try:
                        if selector.startswith("//"):
                            elements = driver.find_elements(By.XPATH, selector)
                        else:
                            elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        
                        if elements and len(elements) > 0:
                            next_button = elements[0]
                            break
                    except:
                        continue
                
                # Kiểm tra nếu tìm thấy nút Next
                if next_button:
                    # Kiểm tra xem nút có bị disabled không (kiểm tra nhiều thuộc tính)
                    parent_li = None
                    try:
                        parent_li = next_button.find_element(By.XPATH, "..")  # Phần tử cha
                    except:
                        pass
                        
                    is_disabled = False
                    
                    # Kiểm tra nhiều điều kiện có thể xác định nút disabled
                    if (next_button.get_attribute("disabled") or 
                        "disabled" in (next_button.get_attribute("class") or "") or
                        (parent_li and "disabled" in (parent_li.get_attribute("class") or "")) or
                        (parent_li and parent_li.get_attribute("aria-disabled") == "true")):
                        is_disabled = True
                        
                    if not is_disabled:
                        # Cuộn đến nút
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
                        time.sleep(0.2)  # Giảm từ 2s xuống 0.2s
                        
                        # Thử click bằng JavaScript
                        try:
                            driver.execute_script("arguments[0].click();", next_button)
                            current_page += 1
                            time.sleep(0.8)  # Giảm từ 3s xuống 0.8s
                        except Exception as e:
                            has_next_page = False
                    else:
                        has_next_page = False
                else:
                    # Nếu không tìm thấy nút Next, thử tìm các số trang trực tiếp
                    try:
                        page_buttons = driver.find_elements(By.XPATH, "//button[contains(@class, 'iweb-pagination-item') and not(contains(@class, 'iweb-pagination-disabled'))]")
                        
                        # Tìm nút với số trang cao hơn trang hiện tại
                        next_page_button = None
                        for button in page_buttons:
                            button_text = button.text.strip()
                            if button_text.isdigit() and int(button_text) > current_page:
                                next_page_button = button
                                break
                                
                        if next_page_button:
                            driver.execute_script("arguments[0].click();", next_page_button)
                            current_page = int(next_page_button.text)
                            time.sleep(0.8)  # Giảm từ 3s xuống 0.8s
                        else:
                            has_next_page = False
                    except:
                        has_next_page = False
                    
            except TimeoutException:
                print("Không tìm thấy thẻ div có class='mod-reviews' ở trang này")
                has_next_page = False
                    
            except Exception as e:
                print(f"Lỗi khi xử lý trang {current_page}: {e}")
                has_next_page = False        

        print(f"\n--- Hoàn thành việc cào dữ liệu từ {current_page} trang ---")
        print(f"Tổng số bình luận đã cào được: {len(all_reviews)}")
        
        # Phân loại bình luận theo số sao
        low_reviews = []    # 1-2 sao
        medium_reviews = [] # 3 sao
        high_reviews = []   # 4-5 sao
        
        # Tạo STT mới cho từng danh sách
        low_count = medium_count = high_count = 1
        
        for review in all_reviews:
            stars = review.get("stars", 0)
            content = review.get("content", "Không có nội dung")
            
            if stars <= 2:
                low_reviews.append([low_count, content, stars])
                low_count += 1
            elif stars == 3:
                medium_reviews.append([medium_count, content, stars])
                medium_count += 1
            else:  # stars >= 4
                high_reviews.append([high_count, content, stars])
                high_count += 1
        
        # Lưu vào ba file CSV riêng biệt
        def save_reviews_to_csv(filename, reviews, category):
            with open(filename, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                # Viết header
                writer.writerow(["STT", "Nội dung bình luận", "Số sao"])
                
                # Viết dữ liệu
                writer.writerows(reviews)
            
            print(f"Đã lưu {len(reviews)} bình luận {category} vào file {filename}")
        
        # Lưu các file CSV
        save_reviews_to_csv("low.csv", low_reviews, "tiêu cực (1-2 sao)")
        save_reviews_to_csv("medium.csv", medium_reviews, "trung bình (3 sao)")
        save_reviews_to_csv("high.csv", high_reviews, "tích cực (4-5 sao)")
        
        # Hiển thị thống kê
        print(f"\nThống kê bình luận:")
        print(f"- Bình luận tiêu cực (1-2 sao): {len(low_reviews)}")
        print(f"- Bình luận trung bình (3 sao): {len(medium_reviews)}")
        print(f"- Bình luận tích cực (4-5 sao): {len(high_reviews)}")
        
    except Exception as e:
        print(f"Lỗi: {e}")
        
    finally:
        # Đóng driver
        driver.quit()
        print("Đã đóng trình duyệt")
        
        return all_reviews

if __name__ == "__main__":
    crawl_lazada_reviews()
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.chrome.options import Options
import time
import csv
import os
import random


def setup_driver(headless=False):  # Mặc định không dùng headless để dễ giải quyết captcha
    """Thiết lập và trả về driver Selenium với các tùy chọn để giảm khả năng bị phát hiện"""
    chrome_options = Options()
    
    # Thêm nhiều user-agent để giả lập người dùng thực
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15'
    ]
    chrome_options.add_argument(f'user-agent={random.choice(user_agents)}')
    
    # Vô hiệu hóa các thuộc tính có thể được sử dụng để phát hiện automation
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Thêm tùy chọn để tránh bị phát hiện là bot
    chrome_options.add_argument('--disable-infobars')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--no-sandbox')
    
    # Thêm các tùy chọn để giảm khả năng hiển thị captcha
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-popup-blocking')
    
    # Thêm tùy chọn headless nếu được yêu cầu
    if headless:
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--window-size=1920,1080')
    
    # Thiết lập các tùy chọn để giả lập profile người dùng thực
    prefs = {
        "profile.default_content_setting_values.notifications": 2,
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False
    }
    chrome_options.add_experimental_option("prefs", prefs)
    
    # Khởi tạo driver với các tùy chọn đã thiết lập
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    # Ghi đè các thuộc tính JavaScript để tránh phát hiện Selenium
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
    driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['vi-VN', 'vi', 'en-US', 'en']})")
    
    # Thiết lập kích thước cửa sổ ngẫu nhiên để giống người dùng thực
    if not headless:
        width = random.randint(1050, 1200)
        height = random.randint(800, 900)
        driver.set_window_size(width, height)
    
    return driver

def check_and_handle_captcha(driver):
    """Kiểm tra sự xuất hiện của captcha và xử lý"""
    captcha_indicators = [
        "//div[contains(@class, 'g-recaptcha')]",
        "//iframe[contains(@src, 'recaptcha')]",
        "//div[contains(@class, 'captcha')]",
        "//input[@name='captcha']",
        "//img[contains(@src, 'captcha')]"
    ]
    
    for indicator in captcha_indicators:
        elements = driver.find_elements(By.XPATH, indicator)
        if elements:
            print("\n--- CAPTCHA DETECTED! ---")
            print("Vui lòng giải captcha trong cửa sổ trình duyệt.")
            print("Sau khi giải xong, chương trình sẽ tự động tiếp tục sau 30 giây.")
            
            # Chờ người dùng giải captcha
            time.sleep(30)
            
            # Kiểm tra xem đã giải captcha thành công chưa
            if any(driver.find_elements(By.XPATH, indicator) for indicator in captcha_indicators):
                print("Có vẻ captcha chưa được giải quyết. Thử lại...")
                return False
            else:
                print("Đã giải captcha thành công! Tiếp tục cào dữ liệu...")
                return True
    
    return True  # Không có captcha

def count_stars(item_middle):
    """Đếm số sao từ thẻ div.container-star.review-star"""
    try:
        # Tìm container chứa các sao
        container_star = item_middle.find_element(By.CSS_SELECTOR, "div.container-star.review-star")
        
        # Tìm tất cả các thẻ img có class="star" (không phải "start")
        star_imgs = container_star.find_elements(By.CSS_SELECTOR, "img.star")
        
        # Đếm số lượng sao (img có src đúng)
        star_count = 0
        star_src = "TB19ZvEgfDH8KJjy1XcXXcpdXXa-64-64.png"
        
        for img in star_imgs:
            src = img.get_attribute("src")
            if src and star_src in src:
                star_count += 1
        
        return star_count
    except NoSuchElementException:
        # Thử cách khác: tìm tất cả img trong item_middle
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

def get_review_content(item_content):
    """Lấy nội dung bình luận từ thẻ div.item-content-main-content-reviews-item"""
    try:
        review_content = item_content.find_element(By.CSS_SELECTOR, "div.item-content-main-content-reviews-item")
        return review_content.text.strip()
    except NoSuchElementException:
        # Nếu không tìm thấy thẻ cụ thể, lấy toàn bộ nội dung của item_content
        return item_content.text.strip()

def save_reviews_to_files(reviews):
    """Lưu danh sách bình luận vào 3 file CSV dựa theo số sao"""
    # Phân loại bình luận
    low_reviews = []    # 1-2 sao
    medium_reviews = [] # 3 sao
    high_reviews = []   # 4-5 sao
    
    # Đếm số dòng hiện có trong mỗi file để tiếp tục STT
    def get_current_count(filename):
        if not os.path.exists(filename):
            return 0
        
        with open(filename, 'r', encoding='utf-8', newline='') as f:
            return sum(1 for _ in f) - 1  # Trừ header
    
    low_start = get_current_count("low.csv") + 1
    medium_start = get_current_count("medium.csv") + 1
    high_start = get_current_count("high.csv") + 1
    
    # Phân loại bình luận dựa trên số sao
    for review in reviews:
        stars = review["stars"]
        content = review["content"]
        
        if stars <= 2:  # 1-2 sao
            low_reviews.append([low_start, content, stars])
            low_start += 1
        elif stars == 3:  # 3 sao
            medium_reviews.append([medium_start, content, stars])
            medium_start += 1
        else:  # 4-5 sao
            high_reviews.append([high_start, content, stars])
            high_start += 1
    
    # Lưu vào từng file tương ứng
    save_to_csv(low_reviews, "low.csv")
    save_to_csv(medium_reviews, "medium.csv")
    save_to_csv(high_reviews, "high.csv")
    
    # In thống kê
    print("\nThống kê bình luận:")
    print(f"- Bình luận tiêu cực (1-2 sao): {len(low_reviews)}")
    print(f"- Bình luận trung bình (3 sao): {len(medium_reviews)}")
    print(f"- Bình luận tích cực (4-5 sao): {len(high_reviews)}")

def save_to_csv(reviews, filename):
    """Lưu danh sách bình luận vào file CSV với mode append"""
    if not reviews:
        return  # Không có gì để lưu
    
    # Kiểm tra xem file đã tồn tại chưa để quyết định có viết header hay không
    file_exists = os.path.exists(filename)
    
    with open(filename, 'a', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        
        # Chỉ viết header nếu file chưa tồn tại
        if not file_exists:
            writer.writerow(["STT", "Nội dung bình luận", "Số sao"])
        
        # Viết dữ liệu
        writer.writerows(reviews)
    
    print(f"Đã lưu {len(reviews)} bình luận vào file {filename}")

def simulate_human_behavior(driver):
    """Mô phỏng hành vi người dùng thực để tránh bị phát hiện là bot"""
    # Di chuyển chuột ngẫu nhiên (không hoạt động trong headless)
    try:
        webdriver.ActionChains(driver).move_by_offset(
            random.randint(-100, 100), 
            random.randint(-100, 100)
        ).perform()
    except:
        pass
    
    # Cuộn trang với tốc độ ngẫu nhiên
    scroll_amount = random.randint(100, 300)
    driver.execute_script(f"window.scrollBy(0, {scroll_amount})")
    
    # Thêm delay ngẫu nhiên
    time.sleep(random.uniform(1.5, 2.5))

def crawl_lazada_reviews(url="https://www.lazada.vn/products/pdp-i1576166750-s14059010693.html", max_pages=10, headless=False):
    """
    Hàm cào bình luận từ nhiều trang của sản phẩm Lazada
    
    Args:
        url (str): URL sản phẩm cần cào dữ liệu
        max_pages (int): Số trang tối đa cần cào
        headless (bool): Có chạy ở chế độ headless hay không
    """
    driver = setup_driver(headless=headless)
    all_reviews = []
    current_page = 1
    has_next_page = True
    
    try:
        print(f"Đang truy cập URL: {url}")
        driver.get(url)
        
        # Đợi trang tải và kiểm tra captcha
        time.sleep(random.uniform(3, 5))
        
        if not check_and_handle_captcha(driver):
            print("Không thể xử lý captcha. Thoát chương trình.")
            driver.quit()
            return []
        
        # Cào nhiều trang bình luận
        while has_next_page and current_page <= max_pages:
            print(f"\n--- Đang cào dữ liệu từ trang {current_page}/{max_pages} ---")
            
            # Mô phỏng hành vi người dùng
            simulate_human_behavior(driver)
            
            # Cuộn xuống để tìm phần bình luận
            print("Cuộn trang để tìm phần bình luận...")
            for i in range(3):  # Giảm số lần cuộn xuống 3
                driver.execute_script(f"window.scrollBy(0, {random.randint(500, 700)})")
                time.sleep(random.uniform(1.5, 2.5))
            
            # Tìm thẻ div có class="mod-reviews"
            print("Đang tìm thẻ div có class='mod-reviews'...")
            
            try:
                # Đợi tối đa 10 giây cho div mod-reviews xuất hiện
                reviews_div = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.mod-reviews"))
                )
                print(f"Đã tìm thấy thẻ div.mod-reviews ở trang {current_page}!")
                
                # Kiểm tra captcha trước khi tiếp tục
                if not check_and_handle_captcha(driver):
                    print("Không thể xử lý captcha. Thử trang tiếp theo.")
                    current_page += 1
                    continue
                
                # Tìm tất cả các thẻ div có class="item" trong mod-reviews
                items = reviews_div.find_elements(By.CSS_SELECTOR, "div.item")
                print(f"Tìm thấy {len(items)} bình luận ở trang {current_page}")
                
                # Thu thập thông tin từ mỗi item (mỗi bình luận)
                page_reviews = []
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
                    page_reviews.append(review_data)
                
                # Thêm các bình luận của trang hiện tại vào danh sách tổng
                all_reviews.extend(page_reviews)
                
                # Lưu bình luận của trang hiện tại vào các file CSV phân loại theo số sao
                save_reviews_to_files(page_reviews)
                
                # Tìm nút Next Page để chuyển trang
                try:
                    # Mô phỏng hành vi người dùng trước khi tìm nút Next
                    simulate_human_behavior(driver)
                    
                    # Thử nhiều selector để tìm nút Next Page
                    next_button = None
                    selectors = [
                        "button.iweb-pagination-item-link[title='Next Page']",
                        "li.iweb-pagination-next:not(.iweb-pagination-disabled) button",
                        "//li[contains(@class, 'pagination-next') and not(contains(@class, 'disabled'))]//button",
                        "//button[contains(@title, 'Next') or contains(@aria-label, 'Next')]"
                    ]
                    
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
                    
                    # Kiểm tra nút Next Page có tồn tại và không bị disabled
                    if next_button and next_button.is_displayed():
                        # Kiểm tra thuộc tính disabled
                        disabled = next_button.get_attribute("disabled") == "true"
                        
                        # Kiểm tra class của phần tử cha có chứa "disabled" không
                        parent_disabled = False
                        try:
                            parent = next_button.find_element(By.XPATH, "./..")
                            parent_class = parent.get_attribute("class") or ""
                            parent_disabled = "disabled" in parent_class
                        except:
                            pass
                        
                        if disabled or parent_disabled:
                            print("Nút Next Page đã bị disabled. Đã đến trang cuối cùng.")
                            has_next_page = False
                        else:
                            # Cuộn đến nút để đảm bảo nó có thể được nhìn thấy
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
                            time.sleep(random.uniform(1.5, 2.5))
                            
                            try:
                                # Thêm delay ngẫu nhiên trước khi click
                                time.sleep(random.uniform(1.5, 2.5))

                                # Thử click thông thường
                                next_button.click()
                            except:
                                # Nếu không được, thử click bằng JavaScript
                                driver.execute_script("arguments[0].click();", next_button)
                            
                            print(f"Đã chuyển sang trang {current_page + 1}")
                            current_page += 1
                            
                            # Đợi trang mới tải với thời gian ngẫu nhiên
                            time.sleep(random.uniform(2, 3))
                            
                            # Kiểm tra captcha sau khi chuyển trang
                            check_and_handle_captcha(driver)
                    else:
                        print("Không tìm thấy nút Next Page hoặc nút không hiển thị. Đã đến trang cuối cùng.")
                        has_next_page = False
                        
                except Exception as e:
                    print(f"Lỗi khi tìm nút Next Page: {e}")
                    has_next_page = False
                    
            except TimeoutException:
                print(f"Không tìm thấy thẻ div có class='mod-reviews' ở trang {current_page}")
                has_next_page = False
                
            except Exception as e:
                print(f"Lỗi khi xử lý trang {current_page}: {e}")
                has_next_page = False
                
        # In thông tin tổng kết
        print(f"\n--- Hoàn thành việc cào dữ liệu từ {current_page} trang ---")
        print(f"Tổng số bình luận đã cào được: {len(all_reviews)}")
        
    except Exception as e:
        print(f"Lỗi: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Đóng driver
        driver.quit()
        print("Đã đóng trình duyệt")
        
        return all_reviews

if __name__ == "__main__":
    # Cào bình luận từ URL sản phẩm (tối đa 10 trang)
    url = "https://www.lazada.vn/products/pdp-i1576166750-s14059010693.html"
    crawl_lazada_reviews(url, max_pages=1, headless=False)  # Không dùng headless để dễ xử lý captcha
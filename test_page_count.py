from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
import time
import random
from selenium.common.exceptions import TimeoutException
def setup_simple_driver():
    """Thiết lập trình duyệt Chrome đơn giản"""
    options = Options()
    options.add_argument('--start-maximized')
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def find_total_pages(driver):
    """Tìm tổng số trang dựa trên thẻ li.iweb-pagination-total-text"""
    try:
        # Đợi cho thẻ li có class=iweb-pagination-total-text xuất hiện
        wait = WebDriverWait(driver, 10)
        pagination_info = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "li.iweb-pagination-total-text"))
        )
        
        # Lấy text từ thẻ li này (vd: "1-5 / 23")
        page_info_text = pagination_info.text.strip()
        print(f"Thông tin phân trang: '{page_info_text}'")
        
        # Tách chuỗi để lấy số cuối cùng (số trang)
        # Kiểu thông tin có thể là "1-5 / 23" hoặc tương tự
        parts = page_info_text.split()
        last_part = parts[-1]  # Lấy phần tử cuối cùng
        
        # Nếu phần cuối có dấu "/", tách lấy phần sau dấu "/"
        if '/' in last_part:
            total_pages = last_part.split('/')[-1].strip()
        else:
            total_pages = last_part
            
        # Chuyển đổi chuỗi thành số
        if total_pages.isdigit():
            return int(total_pages)
        else:
            print(f"    ! Không thể chuyển '{total_pages}' thành số")
            return 1
            
    except NoSuchElementException:
        print("    ! Không tìm thấy thẻ li.iweb-pagination-total-text")
        return 1
    except TimeoutException:
        print("    ! Hết thời gian chờ khi tìm thẻ li.iweb-pagination-total-text")
        return 1
    except Exception as e:
        print(f"    ! Lỗi khi xác định số trang: {e}")
        return 1
def test_new_page_counter():
    """Test hàm tìm số trang mới"""
    driver = setup_simple_driver()
    
    try:
        print(f"Truy cập URL: https://www.lazada.vn/products/pdp-i1576166750-s14059010693.html")
        driver.get("https://www.lazada.vn/products/pdp-i1576166750-s14059010693.html")
        time.sleep(5)  # Đợi trang tải
        
        print("Cuộn xuống để tìm phân trang...")
        # Cuộn nhiều lần để đảm bảo thấy phân trang
        for i in range(10):
            driver.execute_script(f"window.scrollBy(0, 300)")
            time.sleep(0.5)
        
        # Đợi thêm để trang tải hoàn tất
        time.sleep(2)
        
        # Tìm tổng số trang
        total_pages = find_total_pages(driver)
        print(f"\nTổng số trang sản phẩm: {total_pages}")
        
        input("\nNhấn Enter để đóng trình duyệt...")
    finally:
        driver.quit()
        print("Đã đóng trình duyệt")

if __name__ == "__main__":
    test_new_page_counter()
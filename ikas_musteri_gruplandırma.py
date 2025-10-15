import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, TimeoutException, ElementClickInterceptedException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# WebDriver'ı başlatma ve ayarlamalar
service = Service()
driver = webdriver.Chrome(service=service)
driver.maximize_window()

# Siteye gitme
driver.get("https://kinzi.myikas.com/admin/customer")
time.sleep(3)

# Kullanıcı adı ve şifre ile giriş
try:
    email_input = driver.find_element(By.NAME, "email")
    password_input = driver.find_element(By.NAME, "password")

    email_input.send_keys("omer.dalgin@kinzi.com.tr")
    password_input.send_keys("musluk123")
    password_input.send_keys(Keys.ENTER)
    time.sleep(40)
    print("Başlıyoruz.")
except NoSuchElementException:
    print("Giriş elementleri bulunamadı. Lütfen kontrol edin.")
    driver.quit()
    exit()

def safe_click(driver, element):
    """Elementi görünür hale getirip güvenli şekilde tıklamayı dener."""
    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        time.sleep(1)
        element.click()
        return True
    except Exception as e:
        print(f"Tıklama başarısız oldu, tekrar deneniyor... Hata: {e}")
        return False


def process_customers_by_text():
    """Doğrudan 'Sipariş Yok' metnini içeren müşteri satırlarını işleme alır."""
    while True:
        try:
            wait = WebDriverWait(driver, 15)
            main_div = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.sc-iaUyqC.jmoEFF')))

            # 'Sipariş Yok' metnini içeren span elementlerini bul
            order_spans = main_div.find_elements(By.XPATH, ".//span[contains(text(), 'Sipariş Yok')]")
            
            if not order_spans:
                print("Bu sayfada 'Sipariş Yok' müşterisi bulunamadı.")

            for i in range(len(order_spans)):
                try:
                    current_row = wait.until(EC.presence_of_element_located(
                        (By.XPATH, f"(//span[contains(text(), 'Sipariş Yok')]/ancestor::div[contains(@class, 'data-table-row')])[{i+1}]")
                    ))

                    # Önce scrollIntoView ile görünür yapmayı dene
                    if not safe_click(driver, current_row):
                        # Olmazsa sayfayı aşağı kaydır ve tekrar dene
                        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        time.sleep(2)
                        if not safe_click(driver, current_row):
                            print("Bu satır tıklanamadı, geçiliyor.")
                            continue

                    time.sleep(3)  # müşteri sayfası yüklenmesini bekle

                    # Düzenle butonuna tıkla
                    edit_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[normalize-space()='Düzenle']")))
                    edit_button.click()
                    time.sleep(3)

                    # Etiket alanına tıkla
                    tag_input_div = wait.until(EC.element_to_be_clickable((By.XPATH, "/html[1]/body[1]/div[7]//form[1]//div[4]//div[2]//div[1]//div[1]//div[1]//div[2]//div[1]//div[1]//div[1]//div[1]/div[1]")))
                    tag_input_div.click()
                    time.sleep(2)

                    try:
                        popup_element = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(text(),'%20 Kullanacak olanlar')]")))
                        popup_element.click()
                        time.sleep(1)
                    except TimeoutException:
                        print("'%20 Kullanacak olanlar' etiketi bulunamadı, muhtemelen zaten ekli.")

                    # Kaydet
                    save_button = driver.find_element(By.XPATH, "//span[normalize-space()='Kaydet']")
                    save_button.click()
                    time.sleep(3)

                    # Geri dön
                    back_to_page = driver.find_element(By.XPATH, "//button[@class='ant-btn css-p6moeu ant-btn-default ant-btn-sm sc-fFeiMQ fffOCj']//*[name()='svg']")
                    back_to_page.click()
                    time.sleep(3)

                except (NoSuchElementException, StaleElementReferenceException) as e:
                    print(f"Müşteri satırı bulunamadı veya stale oldu: {e}")
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)
                    continue

            # Sonraki sayfa
            try:
                next_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//li[@title='Önceki Sayfa']//span[contains(text(),'Sonraki')]")))
                if "disabled" in next_button.get_attribute("class"):
                    print("Son sayfaya ulaşıldı. Otomasyon tamamlandı.")
                    break
                else:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
                    next_button.click()
                    time.sleep(5)
            except Exception:
                print("Sonraki sayfa butonu bulunamadı. Otomasyon tamamlandı.")
                break

        except Exception as e:
            print(f"Genel hata oluştu: {e}. Otomasyon sonlanıyor.")
            break

process_customers_by_text()
driver.quit()
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from typing import List, Dict

max_clicks = 300  # 무한루프 방지

class FoodspringCrawler:
    """Foodspring 셀러 페이지 크롤러"""
    
    def __init__(self, delay: float = 2.0, headless: bool = False):
        """
        Args:
            delay: 각 상품 클릭 사이의 딜레이(초)
            headless: 브라우저를 백그라운드에서 실행할지 여부
        """
        self.delay = delay
        self.headless = headless
        self.driver = None
        
    def setup_driver(self):
        """웹드라이버 설정"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1280,800')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
        
    def close_driver(self):
        """웹드라이버 종료"""
        if self.driver:
            self.driver.quit()
            
    def get_product_links(self, url: str) -> List[str]:
        """상품 목록 페이지에서 모든 상품 링크 가져오기"""
        print(f"상품 목록 페이지 로딩: {url}")
        self.driver.get(url)
        time.sleep(3)  # 페이지 로딩 대기
        
        product_links = []
        
        try:
            # 더보기 버튼을 클릭해서 모든 상품 로드
            self._click_load_more_button()
            
            # 상품 링크 찾기 (여러 선택자 시도)
            selectors = [
                "a[href*='/product/']",
                "a[href*='/goods/']",
                ".product-item a",
                ".product-card a",
                "div[class*='product'] a",
            ]
            
            for selector in selectors:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    for element in elements:
                        href = element.get_attribute('href')
                        if href and href not in product_links:
                            product_links.append(href)
                    break
            
            print(f"총 {len(product_links)}개의 상품 링크 발견")
            return product_links
            
        except Exception as e:
            print(f"상품 링크 가져오기 오류: {str(e)}")
            return []
    
    def _click_load_more_button(self):
        """더보기 버튼을 클릭해서 모든 상품 로드"""
        print("더보기 버튼 확인 중...")
        
        # 더보기 버튼 선택자들
        more_button_selectors = [
            "button:contains('더보기')",
            "button:contains('더 보기')",
            "button:contains('MORE')",
            "button:contains('more')",
            "a:contains('더보기')",
            "a:contains('더 보기')",
            "button[class*='more']",
            "button[class*='load']",
            "a[class*='more']",
            "a[class*='load']",
            "div[class*='more']",
            "//button[contains(text(), '더보기')]",
            "//button[contains(text(), '더 보기')]",
            "//button[contains(text(), 'MORE')]",
            "//button[contains(text(), 'more')]",
            "//a[contains(text(), '더보기')]",
            "//a[contains(text(), '더 보기')]",
        ]
        
        click_count = 0
        
        
        while click_count < max_clicks:
            button_found = False
            
            # 페이지 하단으로 스크롤
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            
            # 여러 선택자로 더보기 버튼 찾기
            for selector in more_button_selectors:
                try:
                    if selector.startswith("//"):
                        # XPath 선택자
                        button = self.driver.find_element(By.XPATH, selector)
                    else:
                        # CSS 선택자
                        button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    
                    # 버튼이 보이는지 확인
                    if button.is_displayed() and button.is_enabled():
                        # 버튼이 화면에 보이도록 스크롤
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                        time.sleep(0.5)
                        
                        # 클릭
                        try:
                            button.click()
                        except:
                            # JavaScript로 클릭 시도
                            self.driver.execute_script("arguments[0].click();", button)
                        
                        click_count += 1
                        button_found = True
                        print(f"✓ 더보기 버튼 클릭 ({click_count}회)")
                        time.sleep(2)  # 새 상품 로딩 대기
                        break
                        
                except:
                    continue
            
            if not button_found:
                # 더보기 버튼을 찾지 못하면 종료
                break
        
        if click_count > 0:
            print(f"더보기 버튼 총 {click_count}회 클릭 완료")
        else:
            print("더보기 버튼을 찾을 수 없거나 이미 모든 상품이 로드됨")
    
    def get_product_details(self, product_url: str) -> Dict:
        """개별 상품 페이지에서 상세 정보 추출"""
        print(f"\n상품 페이지 크롤링: {product_url}")
        
        try:
            self.driver.get(product_url)
            time.sleep(self.delay)
            
            product_data = {
                '상품URL': product_url,
                '상품명': '',
                '가격': '',
                '메인이미지': '',
                '상세이미지': []
            }
            
            # 상품명 추출
            name_selectors = [
                "h3[class*='title-b-18']"
            ]
            
            for selector in name_selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if element.text.strip():
                        product_data['상품명'] = element.text.strip()
                        break
                except:
                    continue
            
            # 가격 추출
            price_selectors = [
                "strong[class*='title-b-24']"
            ]
            
            for selector in price_selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if element.text.strip():
                        product_data['가격'] = element.text.strip()
                        break
                except:
                    continue
            
            # 메인 이미지 추출
            main_image_selectors = [
                "div[class*='min-w-0'] img"
            ]
            
            for selector in main_image_selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    src = element.get_attribute('src')
                    if src:
                        product_data['메인이미지'] = src
                        break
                except:
                    continue
            
            # 상세 이미지들 추출
            detail_image_selectors = [
                "#goods-header-style-inner p img",
            ]
            
            detail_images = []
            for selector in detail_image_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for img in elements:
                        src = img.get_attribute('src')
                        if src and src not in detail_images:
                            detail_images.append(src)
                except:
                    continue
            
            product_data['상세이미지'] = ', '.join(detail_images) if detail_images else ''
            
            print(f"✓ 상품명: {product_data['상품명']}")
            print(f"✓ 가격: {product_data['가격']}")
            print(f"✓ 메인이미지: {'있음' if product_data['메인이미지'] else '없음'}")
            print(f"✓ 상세이미지: {len(detail_images)}개")
            
            return product_data
            
        except Exception as e:
            print(f"상품 상세 정보 추출 오류: {str(e)}")
            return None
    
    def crawl(self, seller_url: str) -> pd.DataFrame:
        """전체 크롤링 프로세스"""
        print("=" * 60)
        print("Foodspring 크롤러 시작")
        print(f"딜레이: {self.delay}초")
        print("=" * 60)
        
        try:
            # 드라이버 설정
            self.setup_driver()
            
            # 상품 링크 수집
            product_links = self.get_product_links(seller_url)
            
            if not product_links:
                print("상품 링크를 찾을 수 없습니다.")
                return pd.DataFrame()
            
            # 각 상품 정보 수집
            products_data = []
            
            for idx, link in enumerate(product_links, 1):
                print(f"\n[{idx}/{len(product_links)}] 상품 크롤링 중...")
                product_data = self.get_product_details(link)
                
                if product_data:
                    products_data.append(product_data)
                
                # 마지막 상품이 아니면 딜레이
                if idx < len(product_links):
                    time.sleep(self.delay)
            
            # DataFrame 생성
            df = pd.DataFrame(products_data)
            
            print("\n" + "=" * 60)
            print(f"크롤링 완료! 총 {len(df)}개 상품 수집")
            print("=" * 60)
            
            return df
            
        except Exception as e:
            print(f"크롤링 중 오류 발생: {str(e)}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()
        
        finally:
            self.close_driver()
    
    def save_to_excel(self, df: pd.DataFrame, filename: str = "products.xlsx"):
        """DataFrame을 엑셀 파일로 저장"""
        if df.empty:
            print("저장할 데이터가 없습니다.")
            return
        
        try:
            output_path = f"{filename}"
            df.to_excel(output_path, index=False, engine='openpyxl')
            print(f"\n엑셀 파일 저장 완료: {filename}")
            print(f"저장 경로: {output_path}")
            return output_path
        except Exception as e:
            print(f"엑셀 저장 중 오류: {str(e)}")
            return None


def main():
    """메인 실행 함수"""
    # 설정
    SELLER_URL = "https://www.foodspring.co.kr/seller/3359"
    DELAY = 0.1  # 상품 클릭 사이의 딜레이(초)
    HEADLESS = False  # True로 설정하면 브라우저 창이 안 보임
    
    # 크롤러 생성
    crawler = FoodspringCrawler(delay=DELAY, headless=HEADLESS)
    
    # 크롤링 실행
    df = crawler.crawl(SELLER_URL)
    
    # 엑셀로 저장
    if not df.empty:
        crawler.save_to_excel(df, "foodspring_products.xlsx")
        print("\n데이터 미리보기:")
        print(df.head())
    

if __name__ == "__main__":
    main()

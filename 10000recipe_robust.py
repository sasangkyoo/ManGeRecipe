import requests
import time
import random
import logging
import csv
import json
import os
from datetime import datetime
from bs4 import BeautifulSoup
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import ssl
from typing import Optional, Dict, List
import urllib3

# SSL 경고 무시
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class RobustCrawlerConfig:
    """안정적인 크롤러 설정"""
    def __init__(self):
        # 기본 설정
        self.BASE_URL = "https://www.10000recipe.com"
        self.LIST_URL = f"{self.BASE_URL}/recipe/list.html?order=date&page="
        self.MAX_PAGES = 10  # 테스트용으로 줄임
        self.MAX_RETRIES = 5
        self.TIMEOUT = 30
        
        # 지연 시간 (봇 감지 방지)
        self.MIN_DELAY = 5
        self.MAX_DELAY = 15
        self.RETRY_DELAY_MIN = 10
        self.RETRY_DELAY_MAX = 30
        
        # 세션 설정
        self.SESSION_TIMEOUT = 60
        self.MAX_SESSIONS = 3
        
        # 헤더 설정 (봇 감지 방지)
        self.USER_AGENTS = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'
        ]

def setup_logging():
    """로깅 설정"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"crawler_robust_{timestamp}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

class RobustRecipeCrawler:
    """안정적인 레시피 크롤러"""
    
    def __init__(self):
        self.config = RobustCrawlerConfig()
        self.logger = setup_logging()
        self.session_pool = []
        self._init_session_pool()
        
    def _init_session_pool(self):
        """세션 풀 초기화"""
        for i in range(self.config.MAX_SESSIONS):
            session = self._create_robust_session()
            self.session_pool.append(session)
        self.logger.info(f"{self.config.MAX_SESSIONS}개의 세션을 초기화했습니다.")
    
    def _create_robust_session(self) -> requests.Session:
        """안정적인 세션 생성"""
        session = requests.Session()
        
        # 재시도 전략 설정
        retry_strategy = Retry(
            total=self.config.MAX_RETRIES,
            status_forcelist=[429, 500, 502, 503, 504],
            backoff_factor=1
        )
        
        # SSL 설정
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # SSL 검증 비활성화 (문제 해결을 위해)
        session.verify = False
        
        # 기본 헤더 설정
        session.headers.update({
            'User-Agent': random.choice(self.config.USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        return session
    
    def get_session(self):
        """세션 풀에서 세션 가져오기"""
        if self.session_pool:
            return self.session_pool.pop()
        return self._create_robust_session()
    
    def return_session(self, session):
        """세션을 풀에 반환"""
        if len(self.session_pool) < self.config.MAX_SESSIONS:
            self.session_pool.append(session)
    
    def safe_request(self, url: str, max_retries: int = None) -> Optional[requests.Response]:
        """안전한 요청 처리"""
        if max_retries is None:
            max_retries = self.config.MAX_RETRIES
            
        session = self.get_session()
        
        for attempt in range(max_retries):
            try:
                # 랜덤 지연
                delay = random.uniform(self.config.MIN_DELAY, self.config.MAX_DELAY)
                time.sleep(delay)
                
                # User-Agent 랜덤 변경
                session.headers['User-Agent'] = random.choice(self.config.USER_AGENTS)
                
                self.logger.info(f"요청 시도 {attempt + 1}/{max_retries}: {url}")
                
                response = session.get(
                    url, 
                    timeout=self.config.TIMEOUT,
                    allow_redirects=True
                )
                
                if response.status_code == 200:
                    self.logger.info(f"요청 성공: {url}")
                    return response
                else:
                    self.logger.warning(f"HTTP {response.status_code}: {url}")
                    
            except requests.exceptions.SSLError as e:
                self.logger.warning(f"SSL 오류 (시도 {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    self.logger.error(f"SSL 오류로 인한 최종 실패: {url}")
                    
            except requests.exceptions.ConnectionError as e:
                self.logger.warning(f"연결 오류 (시도 {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    self.logger.error(f"연결 오류로 인한 최종 실패: {url}")
                    
            except requests.exceptions.Timeout as e:
                self.logger.warning(f"타임아웃 (시도 {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    self.logger.error(f"타임아웃으로 인한 최종 실패: {url}")
                    
            except Exception as e:
                self.logger.warning(f"예상치 못한 오류 (시도 {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    self.logger.error(f"예상치 못한 오류로 인한 최종 실패: {url}")
            
            # 재시도 전 지연
            if attempt < max_retries - 1:
                retry_delay = random.uniform(self.config.RETRY_DELAY_MIN, self.config.RETRY_DELAY_MAX)
                self.logger.info(f"{retry_delay:.1f}초 후 재시도...")
                time.sleep(retry_delay)
        
        self.return_session(session)
        return None
    
    def extract_recipe_list(self, page_num: int) -> List[Dict]:
        """레시피 목록 추출"""
        url = f"{self.config.LIST_URL}{page_num}"
        response = self.safe_request(url)
        
        if not response:
            return []
        
        soup = BeautifulSoup(response.content, 'html.parser')
        recipes = []
        
        try:
            recipe_items = soup.select('div.common_sp_thumb')
            
            for item in recipe_items:
                try:
                    # 레시피 ID 추출
                    link_elem = item.select_one('a.common_sp_link')
                    if not link_elem:
                        continue
                    
                    href = link_elem.get('href', '')
                    recipe_id = href.split('/')[-1] if href else '정보 없음'
                    
                    # 제목 추출
                    title_elem = item.select_one('h3.common_sp_caption_tit')
                    title = title_elem.get_text(strip=True) if title_elem else '제목 없음'
                    
                    # 작성자 추출
                    author_elem = item.select_one('p.common_sp_caption_rv_name')
                    author = author_elem.get_text(strip=True) if author_elem else '작성자 없음'
                    
                    # 조회수 추출
                    view_elem = item.select_one('span.common_sp_caption_rv_cnt')
                    view = view_elem.get_text(strip=True) if view_elem else '0'
                    
                    # 이미지 URL 추출
                    img_elem = item.select_one('img.common_sp_caption_img')
                    image_url = img_elem.get('src', '') if img_elem else ''
                    
                    recipe_data = {
                        'ID': recipe_id,
                        'Title': title,
                        'Author': author,
                        'View': view,
                        'Image': image_url
                    }
                    
                    recipes.append(recipe_data)
                    
                except Exception as e:
                    self.logger.warning(f"레시피 항목 파싱 오류: {e}")
                    continue
            
            self.logger.info(f"페이지 {page_num}에서 {len(recipes)}개 레시피 수집")
            
        except Exception as e:
            self.logger.error(f"페이지 {page_num} 파싱 오류: {e}")
        
        return recipes
    
    def extract_recipe_detail(self, recipe_id: str) -> Optional[Dict]:
        """레시피 상세 정보 추출"""
        url = f"{self.config.BASE_URL}/recipe/{recipe_id}"
        response = self.safe_request(url)
        
        if not response:
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        try:
            # 인분 수 추출
            serving_elem = soup.select_one('span.view2_summary_info1')
            serving = serving_elem.get_text(strip=True) if serving_elem else '정보 없음'
            
            # 조리 시간 추출
            time_elem = soup.select_one('span.view2_summary_info2')
            preparation_time = time_elem.get_text(strip=True) if time_elem else '정보 없음'
            
            # 난이도 추출
            difficulty_elem = soup.select_one('span.view2_summary_info3')
            difficulty = difficulty_elem.get_text(strip=True) if difficulty_elem else '정보 없음'
            
            # 재료 추출
            ingredient_elem = soup.select_one('div.ready_ingre3')
            ingredient = ingredient_elem.get_text(strip=True) if ingredient_elem else '재료 없음'
            
            # 양념 추출
            condiment_elem = soup.select_one('div.ready_ingre2')
            condiment = condiment_elem.get_text(strip=True) if condiment_elem else '양념 없음'
            
            detail_data = {
                'ID': recipe_id,
                'Serving': serving,
                'Preparation_Time': preparation_time,
                'Difficulty': difficulty,
                'Ingredient': ingredient,
                'Condiment': condiment
            }
            
            return detail_data
            
        except Exception as e:
            self.logger.error(f"레시피 {recipe_id} 상세 정보 파싱 오류: {e}")
            return None
    
    def save_to_csv(self, filename: str, fieldnames: List[str], data: List[Dict]):
        """CSV 파일로 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename_with_timestamp = f"{filename}_{timestamp}.csv"
        
        with open(filename_with_timestamp, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        
        self.logger.info(f"데이터가 {filename_with_timestamp}에 저장되었습니다.")
        return filename_with_timestamp
    
    def save_to_json(self, filename: str, data: List[Dict]):
        """JSON 파일로 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename_with_timestamp = f"{filename}_{timestamp}.json"
        
        with open(filename_with_timestamp, 'w', encoding='utf-8') as jsonfile:
            json.dump(data, jsonfile, ensure_ascii=False, indent=2)
        
        self.logger.info(f"데이터가 {filename_with_timestamp}에 저장되었습니다.")
        return filename_with_timestamp
    
    def run(self):
        """크롤링 실행"""
        self.logger.info("안정적인 크롤링 시작")
        
        all_recipes = []
        successful_details = 0
        
        # 1단계: 레시피 목록 수집
        self.logger.info("1단계: 레시피 목록 수집 시작")
        
        for page in range(1, self.config.MAX_PAGES + 1):
            self.logger.info(f"페이지 {page} 처리 중...")
            recipes = self.extract_recipe_list(page)
            
            if recipes:
                all_recipes.extend(recipes)
                self.logger.info(f"페이지 {page}에서 {len(recipes)}개 레시피 수집")
            else:
                self.logger.warning(f"페이지 {page}에서 레시피를 수집하지 못했습니다.")
                # 연속 실패 시 중단
                if page > 1:
                    self.logger.warning("연속 실패로 인해 크롤링을 중단합니다.")
                    break
        
        self.logger.info(f"총 {len(all_recipes)}개의 레시피 정보 수집 완료")
        
        # 2단계: 레시피 상세 정보 수집
        self.logger.info("2단계: 레시피 상세 정보 수집 시작")
        
        recipe_details = []
        for i, recipe in enumerate(all_recipes, 1):
            recipe_id = recipe['ID']
            self.logger.info(f"상세 정보 수집 중 ({i}/{len(all_recipes)}): {recipe_id}")
            
            detail = self.extract_recipe_detail(recipe_id)
            if detail:
                recipe_details.append(detail)
                successful_details += 1
                self.logger.info(f"레시피 {recipe_id} 상세 정보 수집 성공")
            else:
                self.logger.warning(f"레시피 {recipe_id} 상세 정보 수집 실패")
            
            # 진행률 표시
            if i % 10 == 0:
                self.logger.info(f"진행률: {i}/{len(all_recipes)} ({i/len(all_recipes)*100:.1f}%)")
        
        # 3단계: 데이터 저장
        self.logger.info("3단계: 데이터 저장")
        
        # 레시피 목록 저장
        if all_recipes:
            food_fieldnames = ['ID', 'Title', 'Author', 'View', 'Image']
            food_filename = self.save_to_csv('food_data', food_fieldnames, all_recipes)
            self.save_to_json('food_data', all_recipes)
        
        # 레시피 상세 정보 저장
        if recipe_details:
            recipe_fieldnames = ['ID', 'Serving', 'Preparation_Time', 'Difficulty', 'Ingredient', 'Condiment']
            recipe_filename = self.save_to_csv('recipe_data', recipe_fieldnames, recipe_details)
            self.save_to_json('recipe_data', recipe_details)
        
        # 최종 결과
        self.logger.info("=" * 50)
        self.logger.info("크롤링 완료!")
        self.logger.info(f"총 레시피 수: {len(all_recipes)}개")
        self.logger.info(f"상세 정보 수집 성공: {successful_details}개")
        self.logger.info(f"성공률: {successful_details/len(all_recipes)*100:.1f}%" if all_recipes else "0%")
        self.logger.info("=" * 50)

def main():
    """메인 함수"""
    crawler = RobustRecipeCrawler()
    crawler.run()

if __name__ == "__main__":
    main() 
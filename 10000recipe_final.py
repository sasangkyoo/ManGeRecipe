import requests
import csv
import time
import random
import json
from bs4 import BeautifulSoup
import logging
from datetime import datetime
import os
from typing import Dict, List, Optional
import re

# 설정 클래스
class CrawlerConfig:
    def __init__(self):
        self.HEADERS = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        self.BASE_URL = "https://www.10000recipe.com"
        self.RECIPE_LIST_URL = f"{self.BASE_URL}/recipe/list.html?order=date&page="
        self.RECIPE_DETAIL_URL = f"{self.BASE_URL}/recipe/"
        self.MAX_PAGES = 25
        self.MAX_RETRIES = 3
        self.TIMEOUT = 15
        self.MIN_DELAY = 3
        self.MAX_DELAY = 7
        self.RETRY_DELAY_MIN = 5
        self.RETRY_DELAY_MAX = 10

# 로깅 설정
def setup_logging():
    """로깅 설정"""
    log_filename = f"crawler_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

class RecipeCrawler:
    def __init__(self):
        self.config = CrawlerConfig()
        self.logger = setup_logging()
        self.food_data = []
        self.recipe_data = []
        self.session = requests.Session()
        self.session.headers.update(self.config.HEADERS)
        
    def safe_request(self, url: str, max_retries: int = None) -> Optional[requests.Response]:
        """안전한 HTTP 요청 함수"""
        if max_retries is None:
            max_retries = self.config.MAX_RETRIES
            
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, timeout=self.config.TIMEOUT)
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"요청 실패 (시도 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(random.uniform(self.config.RETRY_DELAY_MIN, self.config.RETRY_DELAY_MAX))
                else:
                    self.logger.error(f"최대 재시도 횟수 초과: {url}")
                    return None
        return None

    def validate_data(self, data_dict: Dict, required_fields: List[str]) -> bool:
        """데이터 유효성 검증"""
        for field in required_fields:
            if field not in data_dict or not data_dict[field] or data_dict[field] in ['정보 없음', '제목 없음', '저자 없음']:
                return False
        return True

    def clean_text(self, text: str) -> str:
        """텍스트 정리"""
        if not text:
            return ""
        # 불필요한 공백 제거
        text = re.sub(r'\s+', ' ', text.strip())
        # 특수문자 정리
        text = text.replace('\n', ' ').replace('\r', ' ')
        return text

    def extract_recipe_list(self, page_num: int) -> List[Dict]:
        """레시피 목록 추출"""
        url = self.config.RECIPE_LIST_URL + str(page_num)
        self.logger.info(f"페이지 {page_num} 처리 중... URL: {url}")
        
        response = self.safe_request(url)
        if not response:
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        food_items = soup.select('li.common_sp_list_li')
        
        if not food_items:
            self.logger.warning(f"페이지 {page_num}에서 레시피를 찾을 수 없습니다.")
            return []
        
        recipes = []
        for item in food_items:
            try:
                # CSS 선택자로 데이터 추출
                id_tag = item.select_one('a.common_sp_link')
                title_tag = item.select_one('div.common_sp_caption_tit')
                author_tag = item.select_one('div.common_sp_caption_rv_name')
                view_tag = item.select_one('div.common_sp_caption_rv span.common_sp_caption_buyer')
                img_tag = item.select_one('img[src*="/cache/recipe"]')
                
                # 데이터 정리
                recipe_id = id_tag['href'].replace('/recipe/', '') if id_tag and 'href' in id_tag.attrs else ''
                title = self.clean_text(title_tag.get_text()) if title_tag else ''
                author = self.clean_text(author_tag.get_text()) if author_tag else ''
                view = self.clean_text(view_tag.get_text().replace('조회수', '')) if view_tag else ''
                img = img_tag['src'] if img_tag and 'src' in img_tag.attrs else ''
                
                recipe = {
                    'ID': recipe_id,
                    'Title': title,
                    'Author': author,
                    'View': view,
                    'Image': img
                }
                
                # 데이터 검증
                if self.validate_data(recipe, ['ID', 'Title']):
                    recipes.append(recipe)
                
            except Exception as e:
                self.logger.error(f"개별 아이템 처리 중 오류: {e}")
                continue
        
        self.logger.info(f"페이지 {page_num}에서 {len(recipes)}개 레시피 수집")
        return recipes

    def extract_recipe_detail(self, recipe_id: str) -> Optional[Dict]:
        """레시피 상세 정보 추출"""
        url = self.config.RECIPE_DETAIL_URL + str(recipe_id)
        
        response = self.safe_request(url)
        if not response:
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        try:
            # 기본 정보 추출
            serv_tag = soup.select_one('span.view2_summary_info1')
            prep_tag = soup.select_one('span.view2_summary_info2')
            diff_tag = soup.select_one('span.view2_summary_info3')
            
            serving = self.clean_text(serv_tag.get_text().replace('인분', '')) if serv_tag else ''
            prep_time = self.clean_text(prep_tag.get_text().replace('이내', '')) if prep_tag else ''
            difficulty = self.clean_text(diff_tag.get_text()) if diff_tag else ''
            
            # 재료 정보 추출
            ingredient_text, condiment_text = self.extract_ingredients(soup)
            
            recipe_detail = {
                'ID': recipe_id,
                'Serving': serving,
                'Preparation_Time': prep_time,
                'Difficulty': difficulty,
                'Ingredient': ingredient_text,
                'Condiment': condiment_text
            }
            
            return recipe_detail
            
        except Exception as e:
            self.logger.error(f"레시피 {recipe_id} 상세 정보 추출 중 오류: {e}")
            return None

    def extract_ingredients(self, soup: BeautifulSoup) -> tuple:
        """재료 정보 추출"""
        ingredient_text = '재료 없음'
        condiment_text = '양념 없음'
        
        ingred_items = soup.select('div.ready_ingre3 ul')
        
        if not ingred_items:
            # 대체 방법으로 재료 추출
            title_tag = soup.select_one('div.cont_ingre dl dt')
            ingredient_tag = soup.select_one('div.cont_ingre dl dd')
            
            if title_tag and ingredient_tag:
                title = self.clean_text(title_tag.get_text())
                ingredient = self.clean_text(ingredient_tag.get_text())
                ingredient_text = f"{title}: {ingredient}"
        else:
            for item in ingred_items:
                title_tag = item.select_one('b.ready_ingre3_tt')
                title = self.clean_text(title_tag.get_text()) if title_tag else ''
                
                ingredient_tags = item.select('li div.ingre_list_name a')
                ingredients = [self.clean_text(tag.contents[0]) for tag in ingredient_tags if tag.contents]
                joined_ingredients = ', '.join(ingredients) if ingredients else '재료 없음'
                
                if '재료' in title or '레시피' in title:
                    ingredient_text = f"{title}: {joined_ingredients}"
                elif '양념' in title:
                    condiment_text = f"{title}: {joined_ingredients}"
        
        return ingredient_text, condiment_text

    def save_to_csv(self, filename: str, fieldnames: List[str], data: List[Dict]):
        """CSV 파일로 저장"""
        try:
            with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
            
            self.logger.info(f"'{filename}' 파일이 성공적으로 저장되었습니다. ({len(data)}개 레코드)")
            
        except Exception as e:
            self.logger.error(f"'{filename}' 파일 저장 중 오류: {e}")

    def save_to_json(self, filename: str, data: List[Dict]):
        """JSON 파일로 저장"""
        try:
            with open(filename, 'w', encoding='utf-8') as jsonfile:
                json.dump(data, jsonfile, ensure_ascii=False, indent=2)
            
            self.logger.info(f"'{filename}' 파일이 성공적으로 저장되었습니다. ({len(data)}개 레코드)")
            
        except Exception as e:
            self.logger.error(f"'{filename}' 파일 저장 중 오류: {e}")

    def run(self):
        """크롤링 실행"""
        start_time = datetime.now()
        self.logger.info("크롤링 시작")
        
        try:
            # 1단계: 레시피 목록 수집
            for page in range(1, self.config.MAX_PAGES + 1):
                recipes = self.extract_recipe_list(page)
                self.food_data.extend(recipes)
                
                # 지연
                time.sleep(random.uniform(self.config.MIN_DELAY, self.config.MAX_DELAY))
            
            self.logger.info(f"총 {len(self.food_data)}개의 레시피 정보 수집 완료")
            
            # 2단계: 레시피 상세 정보 수집
            for idx, food in enumerate(self.food_data):
                self.logger.info(f"레시피 상세 정보 처리 중... ({idx+1}/{len(self.food_data)})")
                
                recipe_detail = self.extract_recipe_detail(food['ID'])
                if recipe_detail:
                    self.recipe_data.append(recipe_detail)
                
                # 지연
                time.sleep(random.uniform(self.config.MIN_DELAY, self.config.MAX_DELAY))
            
            self.logger.info(f"총 {len(self.recipe_data)}개의 레시피 상세 정보 수집 완료")
            
            # 3단계: 파일 저장
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # CSV 저장
            self.save_to_csv(
                f'food_data_{timestamp}.csv', 
                ['ID', 'Title', 'Author', 'View', 'Image'], 
                self.food_data
            )
            self.save_to_csv(
                f'recipe_data_{timestamp}.csv', 
                ['ID', 'Serving', 'Preparation_Time', 'Difficulty', 'Ingredient', 'Condiment'], 
                self.recipe_data
            )
            
            # JSON 저장 (백업용)
            self.save_to_json(f'food_data_{timestamp}.json', self.food_data)
            self.save_to_json(f'recipe_data_{timestamp}.json', self.recipe_data)
            
            # 통계 정보
            end_time = datetime.now()
            duration = end_time - start_time
            
            self.logger.info(f"크롤링 완료!")
            self.logger.info(f"총 소요 시간: {duration}")
            self.logger.info(f"수집된 레시피 수: {len(self.food_data)}")
            self.logger.info(f"상세 정보 수집 성공률: {len(self.recipe_data)/len(self.food_data)*100:.1f}%")
            
        except Exception as e:
            self.logger.error(f"크롤링 중 치명적 오류 발생: {e}")
            raise

def main():
    """메인 함수"""
    crawler = RecipeCrawler()
    crawler.run()

if __name__ == "__main__":
    main() 
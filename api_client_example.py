import requests
import json
from typing import Dict, List, Optional
import time

class RecipeAPIClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def _make_request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None) -> Dict:
        """API 요청 수행"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url, params=params)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data)
            else:
                raise ValueError(f"지원하지 않는 HTTP 메서드: {method}")
            
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            print(f"API 요청 오류: {e}")
            return None
    
    def get_server_info(self) -> Dict:
        """서버 정보 조회"""
        return self._make_request("GET", "/")
    
    def get_recipes(self, page: int = 1, per_page: int = 20) -> List[Dict]:
        """모든 레시피 조회"""
        params = {"page": page, "per_page": per_page}
        return self._make_request("GET", "/recipes", params=params)
    
    def get_recipe_by_id(self, recipe_id: str) -> Optional[Dict]:
        """ID로 레시피 조회"""
        return self._make_request("GET", f"/recipes/{recipe_id}")
    
    def search_recipes(self, 
                      query: str = "", 
                      author: str = "", 
                      difficulty: str = "",
                      max_time: int = None,
                      page: int = 1, 
                      per_page: int = 20) -> Dict:
        """레시피 검색"""
        params = {
            "q": query,
            "author": author,
            "difficulty": difficulty,
            "page": page,
            "per_page": per_page
        }
        if max_time:
            params["max_time"] = max_time
        
        return self._make_request("GET", "/search", params=params)
    
    def get_statistics(self) -> Dict:
        """통계 정보 조회"""
        return self._make_request("GET", "/statistics")
    
    def get_random_recipes(self, count: int = 10) -> List[Dict]:
        """랜덤 레시피 조회"""
        params = {"count": count}
        return self._make_request("GET", "/random", params=params)
    
    def get_recipes_by_difficulty(self, difficulty: str) -> List[Dict]:
        """난이도별 레시피 조회"""
        return self._make_request("GET", f"/difficulty/{difficulty}")
    
    def health_check(self) -> Dict:
        """헬스 체크"""
        return self._make_request("GET", "/health")

def print_separator(title: str):
    """구분선 출력"""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def main():
    """API 클라이언트 테스트"""
    client = RecipeAPIClient()
    
    print("🍳 만개의레시피 API 클라이언트 테스트")
    print("API 서버가 실행 중인지 확인하세요: http://localhost:8000")
    
    # 1. 서버 정보 조회
    print_separator("1. 서버 정보 조회")
    server_info = client.get_server_info()
    if server_info:
        print(json.dumps(server_info, ensure_ascii=False, indent=2))
    
    # 2. 헬스 체크
    print_separator("2. 헬스 체크")
    health = client.health_check()
    if health:
        print(json.dumps(health, ensure_ascii=False, indent=2))
    
    # 3. 통계 정보 조회
    print_separator("3. 통계 정보 조회")
    stats = client.get_statistics()
    if stats:
        print(f"총 레시피 수: {stats['total_recipes']:,}개")
        print(f"총 작성자 수: {stats['total_authors']:,}명")
        print(f"난이도 분포: {stats['difficulty_distribution']}")
        print(f"조리 시간 분포: {stats['cooking_time_distribution']}")
        print(f"상위 재료 (상위 5개): {dict(list(stats['top_ingredients'].items())[:5])}")
        print(f"상위 작성자 (상위 5명): {dict(list(stats['top_authors'].items())[:5])}")
    
    # 4. 레시피 목록 조회 (첫 페이지)
    print_separator("4. 레시피 목록 조회 (첫 페이지)")
    recipes = client.get_recipes(page=1, per_page=5)
    if recipes:
        print(f"총 {len(recipes)}개 레시피:")
        for i, recipe in enumerate(recipes, 1):
            print(f"{i}. {recipe['Title']} (작성자: {recipe['Author']})")
    
    # 5. 검색 기능 테스트
    print_separator("5. 검색 기능 테스트")
    
    # 제목 검색
    search_results = client.search_recipes(query="김치", per_page=3)
    if search_results:
        print(f"김치 검색 결과: {search_results['total_count']}개")
        for i, recipe in enumerate(search_results['recipes'], 1):
            print(f"{i}. {recipe['Title']}")
    
    # 난이도 검색
    easy_recipes = client.search_recipes(difficulty="아무나", per_page=3)
    if easy_recipes:
        print(f"\n쉬운 레시피: {easy_recipes['total_count']}개")
        for i, recipe in enumerate(easy_recipes['recipes'], 1):
            print(f"{i}. {recipe['Title']} (조리시간: {recipe['Preparation_Time']})")
    
    # 6. 랜덤 레시피 조회
    print_separator("6. 랜덤 레시피 조회")
    random_recipes = client.get_random_recipes(count=3)
    if random_recipes:
        print("랜덤 추천 레시피:")
        for i, recipe in enumerate(random_recipes, 1):
            print(f"{i}. {recipe['Title']} (난이도: {recipe['Difficulty']})")
    
    # 7. 특정 레시피 상세 조회
    print_separator("7. 특정 레시피 상세 조회")
    if recipes:
        first_recipe_id = recipes[0]['ID']
        recipe_detail = client.get_recipe_by_id(first_recipe_id)
        if recipe_detail:
            print(f"레시피 ID: {recipe_detail['ID']}")
            print(f"제목: {recipe_detail['Title']}")
            print(f"작성자: {recipe_detail['Author']}")
            print(f"인분: {recipe_detail['Serving']}")
            print(f"조리시간: {recipe_detail['Preparation_Time']}")
            print(f"난이도: {recipe_detail['Difficulty']}")
            print(f"재료: {recipe_detail['Ingredient'][:100]}...")
            print(f"양념: {recipe_detail['Condiment'][:100]}...")
    
    # 8. 난이도별 레시피 조회
    print_separator("8. 난이도별 레시피 조회")
    difficulty_recipes = client.get_recipes_by_difficulty("초급")
    if difficulty_recipes:
        print(f"초급 레시피: {len(difficulty_recipes)}개")
        for i, recipe in enumerate(difficulty_recipes[:3], 1):
            print(f"{i}. {recipe['Title']} (조리시간: {recipe['Preparation_Time']})")

def interactive_search():
    """대화형 검색"""
    client = RecipeAPIClient()
    
    print("\n🔍 대화형 레시피 검색")
    print("종료하려면 'quit'를 입력하세요.")
    
    while True:
        print("\n" + "-"*40)
        query = input("검색어를 입력하세요: ").strip()
        
        if query.lower() == 'quit':
            break
        
        if not query:
            print("검색어를 입력해주세요.")
            continue
        
        # 검색 실행
        results = client.search_recipes(query=query, per_page=10)
        
        if results and results['recipes']:
            print(f"\n검색 결과: {results['total_count']}개")
            print(f"페이지: {results['page']}/{results['total_count'] // results['per_page'] + 1}")
            
            for i, recipe in enumerate(results['recipes'], 1):
                print(f"\n{i}. {recipe['Title']}")
                print(f"   작성자: {recipe['Author']}")
                print(f"   조리시간: {recipe['Preparation_Time']}")
                print(f"   난이도: {recipe['Difficulty']}")
                print(f"   재료: {recipe['Ingredient'][:80]}...")
        else:
            print("검색 결과가 없습니다.")

if __name__ == "__main__":
    try:
        # 기본 테스트 실행
        main()
        
        # 대화형 검색 (선택사항)
        print("\n" + "="*60)
        choice = input("대화형 검색을 시작하시겠습니까? (y/n): ").strip().lower()
        if choice == 'y':
            interactive_search()
        
        print("\n✅ API 클라이언트 테스트 완료!")
        
    except KeyboardInterrupt:
        print("\n\n👋 프로그램을 종료합니다.")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        print("API 서버가 실행 중인지 확인해주세요.") 
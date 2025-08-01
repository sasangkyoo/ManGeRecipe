from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import pandas as pd
import json
import glob
import os
from datetime import datetime
import uvicorn
from collections import Counter
import re

# FastAPI 앱 생성
app = FastAPI(
    title="만개의레시피 API 서버",
    description="10000recipe.com에서 수집한 레시피 데이터를 제공하는 REST API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic 모델
class RecipeBasic(BaseModel):
    ID: str
    Title: str
    Author: str
    View: str
    Image: str

class RecipeDetail(BaseModel):
    ID: str
    Serving: str
    Preparation_Time: str
    Difficulty: str
    Ingredient: str
    Condiment: str

class RecipeFull(BaseModel):
    ID: str
    Title: str
    Author: str
    View: str
    Image: str
    Serving: str
    Preparation_Time: str
    Difficulty: str
    Ingredient: str
    Condiment: str

class SearchResponse(BaseModel):
    total_count: int
    recipes: List[RecipeFull]
    page: int
    per_page: int

class StatisticsResponse(BaseModel):
    total_recipes: int
    total_authors: int
    difficulty_distribution: Dict[str, int]
    cooking_time_distribution: Dict[str, int]
    top_ingredients: Dict[str, int]
    top_authors: Dict[str, int]

# 데이터 로더 클래스
class RecipeDataLoader:
    def __init__(self):
        self.food_df = None
        self.recipe_df = None
        self.merged_df = None
        self.last_loaded = None
        self.load_latest_data()
    
    def load_latest_data(self):
        """최신 CSV 파일 로드"""
        try:
            # 최신 파일 찾기
            food_files = glob.glob("food_data*.csv")
            recipe_files = glob.glob("recipe_data*.csv")
            
            if not food_files or not recipe_files:
                raise FileNotFoundError("CSV 파일을 찾을 수 없습니다.")
            
            latest_food_file = max(food_files)
            latest_recipe_file = max(recipe_files)
            
            # 파일 수정 시간 확인
            food_mtime = os.path.getmtime(latest_food_file)
            recipe_mtime = os.path.getmtime(latest_recipe_file)
            
            if (self.last_loaded is None or 
                food_mtime > self.last_loaded or 
                recipe_mtime > self.last_loaded):
                
                self.food_df = pd.read_csv(latest_food_file, encoding='utf-8-sig')
                self.recipe_df = pd.read_csv(latest_recipe_file, encoding='utf-8-sig')
                self.merged_df = pd.merge(self.food_df, self.recipe_df, on='ID', how='inner')
                self.last_loaded = max(food_mtime, recipe_mtime)
                
                print(f"데이터 로드 완료: {len(self.merged_df)}개 레시피")
        
        except Exception as e:
            print(f"데이터 로드 오류: {e}")
            raise
    
    def get_recipe_by_id(self, recipe_id: str) -> Optional[Dict]:
        """ID로 레시피 조회"""
        self.load_latest_data()
        recipe = self.merged_df[self.merged_df['ID'] == recipe_id]
        if not recipe.empty:
            return recipe.iloc[0].to_dict()
        return None
    
    def search_recipes(self, 
                      query: str = "", 
                      author: str = "", 
                      difficulty: str = "",
                      max_time: int = None,
                      page: int = 1, 
                      per_page: int = 20) -> Dict:
        """레시피 검색"""
        self.load_latest_data()
        
        # 필터링
        filtered_df = self.merged_df.copy()
        
        if query:
            filtered_df = filtered_df[
                filtered_df['Title'].str.contains(query, case=False, na=False) |
                filtered_df['Ingredient'].str.contains(query, case=False, na=False)
            ]
        
        if author:
            filtered_df = filtered_df[
                filtered_df['Author'].str.contains(author, case=False, na=False)
            ]
        
        if difficulty:
            filtered_df = filtered_df[
                filtered_df['Difficulty'] == difficulty
            ]
        
        if max_time:
            # 조리 시간 필터링 (분 단위)
            time_pattern = r'(\d+)분'
            filtered_df['time_minutes'] = filtered_df['Preparation_Time'].str.extract(time_pattern).astype(float)
            filtered_df = filtered_df[filtered_df['time_minutes'] <= max_time]
        
        # 페이징
        total_count = len(filtered_df)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        
        paginated_df = filtered_df.iloc[start_idx:end_idx]
        
        return {
            'total_count': total_count,
            'recipes': paginated_df.to_dict('records'),
            'page': page,
            'per_page': per_page
        }
    
    def get_statistics(self) -> Dict:
        """통계 정보 조회"""
        self.load_latest_data()
        
        # 기본 통계
        total_recipes = len(self.merged_df)
        total_authors = self.merged_df['Author'].nunique()
        
        # 난이도 분포
        difficulty_dist = self.merged_df['Difficulty'].value_counts().to_dict()
        
        # 조리 시간 분포
        time_pattern = r'(\d+)분'
        cooking_times = []
        for time_text in self.merged_df['Preparation_Time']:
            if '분' in str(time_text):
                match = re.search(time_pattern, str(time_text))
                if match:
                    cooking_times.append(int(match.group(1)))
        
        time_dist = {
            '15분 이하': len([t for t in cooking_times if t <= 15]),
            '15-30분': len([t for t in cooking_times if 15 < t <= 30]),
            '30-60분': len([t for t in cooking_times if 30 < t <= 60]),
            '60분 이상': len([t for t in cooking_times if t > 60])
        }
        
        # 상위 재료
        ingredients = []
        for ingredient_text in self.merged_df['Ingredient']:
            if '재료 없음' not in ingredient_text:
                matches = re.findall(r'[가-힣]+', ingredient_text)
                ingredients.extend(matches)
        
        top_ingredients = dict(Counter(ingredients).most_common(10))
        
        # 상위 작성자
        top_authors = self.merged_df['Author'].value_counts().head(10).to_dict()
        
        return {
            'total_recipes': total_recipes,
            'total_authors': total_authors,
            'difficulty_distribution': difficulty_dist,
            'cooking_time_distribution': time_dist,
            'top_ingredients': top_ingredients,
            'top_authors': top_authors
        }
    
    def get_random_recipes(self, count: int = 10) -> List[Dict]:
        """랜덤 레시피 조회"""
        self.load_latest_data()
        return self.merged_df.sample(min(count, len(self.merged_df))).to_dict('records')
    
    def get_recipes_by_difficulty(self, difficulty: str) -> List[Dict]:
        """난이도별 레시피 조회"""
        self.load_latest_data()
        filtered_df = self.merged_df[self.merged_df['Difficulty'] == difficulty]
        return filtered_df.to_dict('records')

# 데이터 로더 인스턴스
data_loader = RecipeDataLoader()

# 의존성 함수
def get_data_loader() -> RecipeDataLoader:
    return data_loader

# API 엔드포인트들

@app.get("/", response_class=JSONResponse)
async def root():
    """API 루트 엔드포인트"""
    return {
        "message": "만개의레시피 API 서버에 오신 것을 환영합니다!",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "recipes": "/recipes",
            "recipe_by_id": "/recipes/{recipe_id}",
            "search": "/search",
            "statistics": "/statistics",
            "random": "/random",
            "by_difficulty": "/difficulty/{difficulty}"
        }
    }

@app.get("/recipes", response_model=List[RecipeFull])
async def get_recipes(
    page: int = Query(1, ge=1, description="페이지 번호"),
    per_page: int = Query(20, ge=1, le=100, description="페이지당 레시피 수"),
    loader: RecipeDataLoader = Depends(get_data_loader)
):
    """모든 레시피 조회 (페이징 지원)"""
    try:
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        
        recipes = loader.merged_df.iloc[start_idx:end_idx].to_dict('records')
        return recipes
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"데이터 조회 오류: {str(e)}")

@app.get("/recipes/{recipe_id}", response_model=RecipeFull)
async def get_recipe_by_id(
    recipe_id: str,
    loader: RecipeDataLoader = Depends(get_data_loader)
):
    """ID로 특정 레시피 조회"""
    recipe = loader.get_recipe_by_id(recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail=f"레시피 ID {recipe_id}를 찾을 수 없습니다.")
    return recipe

@app.get("/search", response_model=SearchResponse)
async def search_recipes(
    q: str = Query("", description="검색어 (제목, 재료)"),
    author: str = Query("", description="작성자"),
    difficulty: str = Query("", description="난이도"),
    max_time: Optional[int] = Query(None, ge=1, description="최대 조리 시간 (분)"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    per_page: int = Query(20, ge=1, le=100, description="페이지당 레시피 수"),
    loader: RecipeDataLoader = Depends(get_data_loader)
):
    """레시피 검색"""
    try:
        result = loader.search_recipes(
            query=q,
            author=author,
            difficulty=difficulty,
            max_time=max_time,
            page=page,
            per_page=per_page
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"검색 오류: {str(e)}")

@app.get("/statistics", response_model=StatisticsResponse)
async def get_statistics(
    loader: RecipeDataLoader = Depends(get_data_loader)
):
    """통계 정보 조회"""
    try:
        return loader.get_statistics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"통계 조회 오류: {str(e)}")

@app.get("/random", response_model=List[RecipeFull])
async def get_random_recipes(
    count: int = Query(10, ge=1, le=50, description="랜덤 레시피 수"),
    loader: RecipeDataLoader = Depends(get_data_loader)
):
    """랜덤 레시피 조회"""
    try:
        return loader.get_random_recipes(count)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"랜덤 레시피 조회 오류: {str(e)}")

@app.get("/difficulty/{difficulty}", response_model=List[RecipeFull])
async def get_recipes_by_difficulty(
    difficulty: str,
    loader: RecipeDataLoader = Depends(get_data_loader)
):
    """난이도별 레시피 조회"""
    try:
        recipes = loader.get_recipes_by_difficulty(difficulty)
        if not recipes:
            raise HTTPException(status_code=404, detail=f"난이도 '{difficulty}'의 레시피를 찾을 수 없습니다.")
        return recipes
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"난이도별 레시피 조회 오류: {str(e)}")

@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/download/csv")
async def download_csv():
    """최신 CSV 파일 다운로드"""
    try:
        food_files = glob.glob("food_data*.csv")
        recipe_files = glob.glob("recipe_data*.csv")
        
        if not food_files or not recipe_files:
            raise HTTPException(status_code=404, detail="CSV 파일을 찾을 수 없습니다.")
        
        latest_food_file = max(food_files)
        return FileResponse(
            latest_food_file,
            media_type='text/csv',
            filename=f"recipes_{datetime.now().strftime('%Y%m%d')}.csv"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파일 다운로드 오류: {str(e)}")

# 에러 핸들러
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": "요청한 리소스를 찾을 수 없습니다."}
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": "서버 내부 오류가 발생했습니다."}
    )

if __name__ == "__main__":
    print("🚀 만개의레시피 API 서버를 시작합니다...")
    print("📖 API 문서: http://localhost:8000/docs")
    print("🔍 ReDoc 문서: http://localhost:8000/redoc")
    print("🌐 API 루트: http://localhost:8000/")
    
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 
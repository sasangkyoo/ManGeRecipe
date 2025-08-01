import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
import re
from typing import Dict, List, Tuple
import json

class RecipeDataAnalyzer:
    def __init__(self, food_data_file: str, recipe_data_file: str):
        """데이터 분석기 초기화"""
        self.food_df = pd.read_csv(food_data_file, encoding='utf-8-sig')
        self.recipe_df = pd.read_csv(recipe_data_file, encoding='utf-8-sig')
        self.merged_df = pd.merge(self.food_df, self.recipe_df, on='ID', how='inner')
        
    def basic_statistics(self) -> Dict:
        """기본 통계 정보"""
        stats = {
            '총 레시피 수': len(self.food_df),
            '상세 정보 수집 성공률': len(self.recipe_df) / len(self.food_df) * 100,
            '고유 작성자 수': self.food_df['Author'].nunique(),
            '평균 조회수': self.food_df['View'].str.extract(r'(\d+)').astype(float).mean(),
            '난이도별 분포': self.recipe_df['Difficulty'].value_counts().to_dict(),
            '인분별 분포': self.recipe_df['Serving'].value_counts().head(10).to_dict()
        }
        return stats
    
    def extract_ingredients(self) -> List[str]:
        """재료 목록 추출"""
        ingredients = []
        for ingredient_text in self.recipe_df['Ingredient']:
            if '재료 없음' not in ingredient_text:
                # 재료 텍스트에서 실제 재료명만 추출
                matches = re.findall(r'[가-힣]+', ingredient_text)
                ingredients.extend(matches)
        return ingredients
    
    def analyze_ingredients(self) -> Dict:
        """재료 분석"""
        ingredients = self.extract_ingredients()
        ingredient_counts = Counter(ingredients)
        
        return {
            '총 재료 종류': len(ingredient_counts),
            '가장 많이 사용된 재료 (상위 10개)': dict(ingredient_counts.most_common(10)),
            '재료별 사용 빈도': dict(ingredient_counts)
        }
    
    def analyze_cooking_time(self) -> Dict:
        """조리 시간 분석"""
        # 조리 시간을 분 단위로 변환
        time_pattern = r'(\d+)분'
        cooking_times = []
        
        for time_text in self.recipe_df['Preparation_Time']:
            if '분' in str(time_text):
                match = re.search(time_pattern, str(time_text))
                if match:
                    cooking_times.append(int(match.group(1)))
        
        if cooking_times:
            return {
                '평균 조리 시간': sum(cooking_times) / len(cooking_times),
                '최소 조리 시간': min(cooking_times),
                '최대 조리 시간': max(cooking_times),
                '조리 시간 분포': {
                    '15분 이하': len([t for t in cooking_times if t <= 15]),
                    '15-30분': len([t for t in cooking_times if 15 < t <= 30]),
                    '30-60분': len([t for t in cooking_times if 30 < t <= 60]),
                    '60분 이상': len([t for t in cooking_times if t > 60])
                }
            }
        return {}
    
    def analyze_difficulty(self) -> Dict:
        """난이도 분석"""
        difficulty_counts = self.recipe_df['Difficulty'].value_counts()
        return {
            '난이도별 분포': difficulty_counts.to_dict(),
            '가장 많은 난이도': difficulty_counts.index[0] if len(difficulty_counts) > 0 else None
        }
    
    def analyze_authors(self) -> Dict:
        """작성자 분석"""
        author_counts = self.food_df['Author'].value_counts()
        return {
            '총 작성자 수': len(author_counts),
            '가장 활발한 작성자 (상위 10명)': author_counts.head(10).to_dict(),
            '평균 레시피 수': len(self.food_df) / len(author_counts)
        }
    
    def generate_report(self) -> str:
        """분석 리포트 생성"""
        report = []
        report.append("=" * 50)
        report.append("레시피 데이터 분석 리포트")
        report.append("=" * 50)
        
        # 기본 통계
        stats = self.basic_statistics()
        report.append(f"\n📊 기본 통계")
        report.append(f"총 레시피 수: {stats['총 레시피 수']:,}개")
        report.append(f"상세 정보 수집 성공률: {stats['상세 정보 수집 성공률']:.1f}%")
        report.append(f"고유 작성자 수: {stats['고유 작성자 수']:,}명")
        
        # 난이도 분석
        difficulty_analysis = self.analyze_difficulty()
        report.append(f"\n🎯 난이도 분석")
        for difficulty, count in difficulty_analysis['난이도별 분포'].items():
            report.append(f"{difficulty}: {count}개")
        
        # 조리 시간 분석
        time_analysis = self.analyze_cooking_time()
        if time_analysis:
            report.append(f"\n⏰ 조리 시간 분석")
            report.append(f"평균 조리 시간: {time_analysis['평균 조리 시간']:.1f}분")
            for time_range, count in time_analysis['조리 시간 분포'].items():
                report.append(f"{time_range}: {count}개")
        
        # 재료 분석
        ingredient_analysis = self.analyze_ingredients()
        report.append(f"\n🥕 재료 분석")
        report.append(f"총 재료 종류: {ingredient_analysis['총 재료 종류']}개")
        report.append("가장 많이 사용된 재료 (상위 5개):")
        for ingredient, count in list(ingredient_analysis['가장 많이 사용된 재료 (상위 10개)'].items())[:5]:
            report.append(f"  - {ingredient}: {count}회")
        
        # 작성자 분석
        author_analysis = self.analyze_authors()
        report.append(f"\n👨‍🍳 작성자 분석")
        report.append(f"총 작성자 수: {author_analysis['총 작성자 수']}명")
        report.append(f"평균 레시피 수: {author_analysis['평균 레시피 수']:.1f}개")
        report.append("가장 활발한 작성자 (상위 5명):")
        for author, count in list(author_analysis['가장 활발한 작성자 (상위 10명)'].items())[:5]:
            report.append(f"  - {author}: {count}개")
        
        report.append("\n" + "=" * 50)
        return "\n".join(report)
    
    def save_analysis(self, filename: str = "analysis_report.txt"):
        """분석 결과를 파일로 저장"""
        report = self.generate_report()
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"분석 리포트가 '{filename}'에 저장되었습니다.")
    
    def create_visualizations(self):
        """시각화 생성"""
        # 한글 폰트 설정
        plt.rcParams['font.family'] = 'Malgun Gothic'
        
        # 1. 난이도 분포
        plt.figure(figsize=(10, 6))
        difficulty_counts = self.recipe_df['Difficulty'].value_counts()
        plt.pie(difficulty_counts.values, labels=difficulty_counts.index, autopct='%1.1f%%')
        plt.title('레시피 난이도 분포')
        plt.savefig('difficulty_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 2. 조리 시간 분포
        time_pattern = r'(\d+)분'
        cooking_times = []
        for time_text in self.recipe_df['Preparation_Time']:
            if '분' in str(time_text):
                match = re.search(time_pattern, str(time_text))
                if match:
                    cooking_times.append(int(match.group(1)))
        
        if cooking_times:
            plt.figure(figsize=(10, 6))
            plt.hist(cooking_times, bins=20, edgecolor='black')
            plt.xlabel('조리 시간 (분)')
            plt.ylabel('레시피 수')
            plt.title('조리 시간 분포')
            plt.savefig('cooking_time_distribution.png', dpi=300, bbox_inches='tight')
            plt.close()
        
        # 3. 상위 재료 사용 빈도
        ingredients = self.extract_ingredients()
        ingredient_counts = Counter(ingredients)
        top_ingredients = dict(ingredient_counts.most_common(10))
        
        plt.figure(figsize=(12, 8))
        plt.barh(list(top_ingredients.keys()), list(top_ingredients.values()))
        plt.xlabel('사용 빈도')
        plt.title('가장 많이 사용된 재료 (상위 10개)')
        plt.gca().invert_yaxis()
        plt.savefig('top_ingredients.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print("시각화 파일들이 생성되었습니다:")
        print("- difficulty_distribution.png")
        print("- cooking_time_distribution.png")
        print("- top_ingredients.png")

def main():
    """메인 함수"""
    try:
        # 가장 최근 CSV 파일 찾기
        import glob
        food_files = glob.glob("food_data_*.csv")
        recipe_files = glob.glob("recipe_data_*.csv")
        
        if not food_files or not recipe_files:
            print("CSV 파일을 찾을 수 없습니다. 먼저 크롤링을 실행해주세요.")
            return
        
        # 가장 최근 파일 선택
        latest_food_file = max(food_files)
        latest_recipe_file = max(recipe_files)
        
        print(f"분석할 파일: {latest_food_file}, {latest_recipe_file}")
        
        # 분석 실행
        analyzer = RecipeDataAnalyzer(latest_food_file, latest_recipe_file)
        
        # 리포트 생성 및 저장
        analyzer.save_analysis()
        
        # 시각화 생성
        analyzer.create_visualizations()
        
        # 콘솔에 리포트 출력
        print("\n" + analyzer.generate_report())
        
    except Exception as e:
        print(f"분석 중 오류 발생: {e}")

if __name__ == "__main__":
    main() 
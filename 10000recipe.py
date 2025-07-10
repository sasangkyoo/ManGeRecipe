import requests
import csv
import time
import random
from bs4 import BeautifulSoup

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0"
}
recipe_url = "https://www.10000recipe.com/recipe/list.html?order=date&page="
url = "https://www.10000recipe.com/recipe/"
food_data = []
recipe_data = []

try:
# 음식 긁어 오기
    for i in range(25):
        response = requests.get(recipe_url+str(i+1), headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        food_items = soup.select('li.common_sp_list_li')

        if not food_items:
            print("경고: 레시피를 찾을 수 없습니다. CSS 선택자를 다시 확인하세요.")

        for item in food_items:
            id_tag = item.select_one('a.common_sp_link')
            title_tag = item.select_one('div.common_sp_caption_tit')
            author_tag = item.select_one('div.common_sp_caption_rv_name')
            view_tag = item.select_one('div.common_sp_caption_rv span.common_sp_caption_buyer')
            img_tag = item.select_one('img[src*="/cache/recipe"]')

            id = id_tag['href'].replace('/recipe/', '') if id_tag and 'href' in id_tag.attrs else '아이디 정보 없음'
            title = title_tag.get_text(strip=True) if title_tag else '제목 없음'
            author = author_tag.get_text(strip=True) if author_tag else '저자 없음'
            view = view_tag.get_text().replace('조회수', '').strip() if view_tag else '뷰 정보 없음'
            img = img_tag['src'] if img_tag and 'src' in img_tag.attrs else '이미지 정보 없음'

            # 추출된 데이터를 딕셔너리 형태로 저장
            food_data.append({
                'ID': id,
                'Title': title,
                'Author': author,
                'View': view,
                'Image': img
            })

        time.sleep(random.uniform(3, 5))

    # 추출된 상위 5개 레시피 정보 출력
    print("\n--- 추출된 레시피 정보 (상위 5개) ---")
    for food in food_data[:5]:
        print(food)
    print(f"\n총 {len(food_data)}개의 레시피 정보 추출 완료.")

    #레시피 긁어 오기
    for food in food_data:
        response = requests.get(url + str(food['ID']), headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        serv_tag = soup.select_one('span.view2_summary_info1')
        prep_tag = soup.select_one('span.view2_summary_info2')
        diff_tag = soup.select_one('span.view2_summary_info3')
        ingred_items = soup.select('div.ready_ingre3 ul')


        id = food['ID']
        serving = serv_tag.get_text(strip=True).replace('인분', '').strip() if serv_tag else '인분 정보 없음'
        prep_time = prep_tag.get_text(strip=True).replace('이내', '').strip() if prep_tag else '소요 시간 정보 없음'
        difficulty = diff_tag.get_text(strip=True) if diff_tag else '난이도 없음'

        ingredient_text = '재료 없음'
        condiment_text = '양념 없음'

        if not ingred_items:
            title_tag = soup.select_one('div.cont_ingre dl dt')
            title = title_tag.get_text(strip=True) if title_tag else '제목 없음'

            ingredient_tag = soup.select_one('div.cont_ingre dl dd')
            ingredient = ingredient_tag.get_text(strip=True) if ingredient_tag else '재료 없음'
            ingredient_text = f"{title}: {ingredient}"
        else:
            for item in ingred_items:
                title_tag = item.select_one('b.ready_ingre3_tt')
                title = title_tag.get_text(strip=True) if title_tag else '제목 없음'

                ingredient_tags = item.select('li div.ingre_list_name a')
                ingredients = [tag.contents[0].strip() for tag in ingredient_tags if tag.contents]
                joined_ingredients = ', '.join(ingredients) if ingredients else '재료 없음'

                if '재료' in title or '레시피' in title:
                    ingredient_text = f"{title}: {joined_ingredients}"
                elif '양념' in title:
                    condiment_text = f"{title}: {joined_ingredients}"

        # 추출된 데이터를 딕셔너리 형태로 저장
        recipe_data.append({
            'ID': id,
            'Serving': serving,
            'Preparation_Time': prep_time,
            'Difficulty': difficulty,
            'Ingredient': ingredient_text,
            'Condiment': condiment_text
        })

        time.sleep(random.uniform(3, 5))

    print("\n--- 추출된 레시피 세부 정보 (상위 5개) ---")
    for recipe in recipe_data[:5]:
        print(recipe)
    print(f"\n총 {len(recipe_data)}개의 레시피 정보 추출 완료.")

except requests.exceptions.HTTPError as e:
    print(f"HTTP 오류 발생: {e}")
    print(f"상태 코드: {e.response.status_code}")
except requests.exceptions.ConnectionError as e:
    print(f"네트워크 연결 오류: {e}")
except requests.exceptions.Timeout as e:
    print(f"요청 타임아웃: {e}")
except requests.exceptions.RequestException as e:
    print(f"그 외 요청 오류: {e}")
except Exception as e:
    print(f"데이터 추출 중 오류 발생: {e}")

csv_list = [
    ('food_data.csv', ['ID', 'Title', 'Author', 'View', 'Image'], food_data),
    ('recipe_data.csv', ['ID', 'Serving', 'Preparation_Time', 'Difficulty', 'Ingredient', 'Condiment'], recipe_data)
]

# CSV 파일 쓰기 (write 모드 'w', newline='' 중요, encoding='utf-8-sig'로 한글 깨짐 방지)
for filename, fieldnames, data in csv_list:
    with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
        # CSV Writer 객체 생성, 필드명 (헤더) 지정
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader() # 헤더 쓰기
        writer.writerows(data) # 데이터 쓰기

    print(f"'{filename}' 파일이 성공적으로 저장되었습니다.")

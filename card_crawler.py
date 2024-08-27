import json  # JSON 파일 저장을 위해 필요
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
from selenium.webdriver import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, ElementNotInteractableException

# 브라우저 꺼짐 방지 옵션
chrome_options = Options()
chrome_options.add_experimental_option("detach", True)
# 크롬 드라이버 생성
driver = webdriver.Chrome(options=chrome_options)

time.sleep(4)

action = ActionChains(driver)
wait = WebDriverWait(driver, 10)

def handle_ad():
    """광고가 나타나는 경우 이를 감지하고 대기하거나 닫는 함수"""
    try:
        ad_close_button = driver.find_element(By.XPATH, '/html/body/div[4]/div[2]/div/button/div[2]/i')  # 광고 닫기 버튼의 XPATH
        # 광고 닫기 버튼이 상호작용 가능한 상태인지 확인
        wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[4]/div[2]/div/button/div[2]/i')))
        ad_close_button.click()
        print("광고를 닫았습니다.")
    except NoSuchElementException:
        print("광고가 나타나지 않았습니다.")
    except ElementNotInteractableException:
        print("광고 닫기 버튼이 현재 상호작용할 수 없는 상태입니다. 잠시 기다립니다.")
        time.sleep(2)
        ad_close_button.click()
    except ElementClickInterceptedException:
        print("광고를 닫는 데 실패했습니다. 계속 진행합니다.")
        time.sleep(3)  # 광고가 사라질 때까지 잠시 대기

# 전체 카드사 URL에 대해 반복문을 수행
for card_number in [7,8,32]:  # 1번부터 10번까지 카드사에 대해 반복(조정할 것)
    url = f'https://card-gorilla.com/team/detail/{card_number}'
    driver.get(url)
    time.sleep(4)

    # 카드사 이름을 가져오기 위한 올바른 XPATH를 설정합니다.
    card_company_name = driver.find_element(By.XPATH, f'//*[@id="q-app"]/section/div[1]/div/div[1]/div/b').text
    company_info = {
        "card_company": card_company_name,
        "cards": []
    }

    for card in range(1, 11):  # 상위 카드 10개만 크롤링
        cur_card_info = driver.find_element(By.XPATH, f'//*[@id="q-app"]/section/div[1]/section/div[2]/article[1]/div/div/ul/li[{card}]/div/div[2]').text.split('\n')
        
        # '자세히 보기'가 리스트에 있으면 제거
        if '자세히 보기' in cur_card_info:
            cur_card_info.remove('자세히 보기')

        card_details = {
            "name": cur_card_info[0],
            "summary": " ".join(cur_card_info[1:]),
            "benefits": {}
        }
        
        print(f'카드사 번호: {card_number}, iteration: {card}번째 카드 ', cur_card_info[0])
        
        detail_buttons = driver.find_element(By.XPATH, f'//*[@id="q-app"]/section/div[1]/section/div[2]/article[1]/div/div/ul/li[{card}]/div/div[2]/div[2]/a')
        
        # 광고 처리 함수 호출
        handle_ad()
        
        detail_buttons.click()
        
        for i in range(1, 11):  # 주요 혜택 배너수가 10개 이하
            try:
                cur_benefit_r = f'//*[@id="q-app"]/section/div[1]/section/div/article[2]/div[1]/dl[{i}]'  # 주요혜택 배너 XPATH
        
                wait.until(EC.presence_of_all_elements_located((By.XPATH, cur_benefit_r))) 
                cur_benefit = driver.find_element(By.XPATH, cur_benefit_r)
                time.sleep(1)  
                
                action.move_to_element(cur_benefit)
                action.click()
                action.perform()
                
                cur_li = cur_benefit.text.split('\n')
                
                print(f'{card}번째 카드에서 선택된 주요혜택 배너명 : ', cur_li[0])
                if cur_li[0] == '유의사항':
                    break

                if cur_li[0] not in card_details["benefits"]:
                    card_details["benefits"][cur_li[0]] = []
                card_details["benefits"][cur_li[0]].append(' '.join(cur_li[1:]))
                
            except Exception as e:
                print(f'제외된 iteration: {i}, 오류: {str(e)}')
                break
        
        driver.back()
        
        print({cur_card_info[0]: card_details})
        company_info["cards"].append(card_details)

    # 카드사 별로 JSON 파일 저장
    output_file = f'CardInfo/{card_company_name}_info.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(company_info, f, ensure_ascii=False, indent=4)

    print(f"{card_company_name} 정보를 {output_file} 파일로 저장했습니다.")




import os
import json

# JSON 파일들이 있는 디렉토리 경로
directory_path = 'CardInfo'

# 결과를 저장할 딕셔너리 초기화
combined_data = {}

# 디렉토리 내 모든 파일 순회
for filename in os.listdir(directory_path):
    if filename.endswith('_info.json'):
        file_path = os.path.join(directory_path, filename)
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # 카드사 이름을 키로 설정하고 데이터를 병합
            card_company_name = filename.split('_info.json')[0]
            combined_data[card_company_name] = data

# 결과를 하나의 JSON 파일로 저장
output_file = 'combined_card_info.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(combined_data, f, ensure_ascii=False, indent=4)

print(f"JSON 파일이 성공적으로 병합되었습니다: {output_file}")

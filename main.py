from selenium import webdriver
from selenium.common import ElementNotInteractableException
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
import json
driver = None


def load_homepage():
    driver = webdriver.Chrome()
    url = f"https://ieeexplore.ieee.org/"
    driver.get(url)
    return driver


def search(query):
    wait = WebDriverWait(driver, 100)
    wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'Typeahead-input')))
    search_box = driver.find_element(By.CLASS_NAME, 'Typeahead-input')
    search_box.send_keys(query)
    search_button=driver.find_element(By.CSS_SELECTOR,'button.fa-search')
    search_button.click()


def get_papers():
    paper_list=[]
    for i in range(5):
        wait = WebDriverWait(driver, 100)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME,'result-item-align')))
        items= driver.find_elements(By.CLASS_NAME,'result-item-align')
        for item in items:
            info= item.find_element(By.CLASS_NAME,'publisher-info-container')
            type_paper= info.find_elements(By.TAG_NAME,'span')[1].text
            link=item.find_element(By.CSS_SELECTOR,'a.fw-bold').get_attribute("href")
            if('Conference Paper' in type_paper):
                paper_list.append(link)
        next_page()
    return paper_list

def next_page():
    li= driver.find_element(By.CLASS_NAME,'next-page-set')
    button= li.find_element(By.TAG_NAME,'button')
    wait = WebDriverWait(driver, 100)
    wait.until(EC.element_to_be_clickable(button))
    driver.execute_script("arguments[0].click();", button)

def select_value(string):
    return string.split(": ")[1]

def extract_data(paper_link):
    driver.get(paper_link)
    wait = WebDriverWait(driver, 100)
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'document-title')))
    info={}
    title=driver.find_element(By.CLASS_NAME, 'document-title')
    info["title"]=title.text
    try:
        page= driver.find_element(By.XPATH, "//div[@class='u-pb-1'][strong[contains(text(), 'Page(s):')]]")
        page_numbers = page.text.split("Page(s): ")[1].split(" - ")[0]
        info["Page(s)"] = int(page_numbers)

    except Exception as e:
        info["Page(s)"] = None
    try:
        cites_in_papers_element = driver.find_element(By.XPATH,
                                                      "//button[div[text()='Papers']]//div[@class='document-banner-metric-count']")
        info["Cites in Papers"] = int(cites_in_papers_element.text)
    except Exception as e:
        info["Cites in Papers"] = None

    try:
        cites_in_patent_element = driver.find_element(By.XPATH,
                                                      "//div[contains(@class, 'document-banner-metric-container')]//button[div[text()='Cites in'][following-sibling::div[text()='Patent']]]/div[@class='document-banner-metric-count']")
        info["Cites in Patent"] = int(cites_in_patent_element.text)
    except Exception as e:
        info["Cites in Patent"] = None

    try:
        full_text_views_element = driver.find_element(By.XPATH,
                                                      "//button[div[div[text()='Full']]]/div[@class='document-banner-metric-count']")
        info["Full Text Views"] = int(full_text_views_element.text)
    except Exception as e:
        info["Full Text Views"] = None

    try:
        Publisher_element = driver.find_element(By.CLASS_NAME,"publisher-info-container")
            #By.XPATH,'//span[contains(@class,"publisher-info-container")]/span/span/span[2]')
        info["Publisher"] = select_value(Publisher_element.text)

    except Exception as e:
        info["Publisher"] = None

    try:
        DOI_element = driver.find_element(By.CLASS_NAME,'stats-document-abstract-doi')
        info["DOI"] = select_value(DOI_element.text)
    except Exception as e:
        info["DOI"] = None

    try:
        Date_of_Conference_element = driver.find_element(By.CLASS_NAME,'doc-abstract-confdate')
        info["Date of Publication"] = select_value(Date_of_Conference_element.text)
    except Exception as e:
        info["Date of Publication"] = None

    try:
        Abstract_element = driver.find_element(By.XPATH,'//div[@class="abstract-text row g-0"]//div[@xplmathjax]')
        info["Abstract"] = Abstract_element.text
    except Exception as e:
        info["Abstract"] = None


    try:
        Published_in_element = driver.find_element(By.CSS_SELECTOR,'.stats-document-abstract-publishedIn a')
        info["Published in"] = {
            "name" :Published_in_element.text,
            "link": Published_in_element.get_attribute("href")
        }
    except Exception as e:
        info["Published in"] = None

    try:
        button_author=driver.find_element(By.ID,'authors')
        button_author.click()
        authors_element = driver.find_elements(By.CLASS_NAME,'author-card')

        info["Authors"] =[]

        for block in authors_element:
            text=block.text
            if len(text)<1 :
                continue
            block_split= text.split("\n")
            author={
                "name":block_split[0]
            }
            if(len(block_split)>1):
                author["from"]= block_split[1]
            info["Authors"].append(author)
    except Exception as e:
        print(e)
        info["Authors"] = None

    try:
        button_Keywords=driver.find_element(By.ID,'keywords')
        button_Keywords.click()
        # IEEE_Keywords_element = driver.find_elements(By.XPATH,"//li[@class='doc-keywords-list-item'][strong[contains(text(),'IEEE')]]//a")
        IEEE_Keywords_element = driver.find_elements(By.XPATH,'//a[contains(@data-tealium_data,"IEEE Keywords")]')
        info["IEEE Keywords"] = [e.text for e in IEEE_Keywords_element if len(e.text)>0]
    except Exception as e:
        info["IEEE Keywords"] = None
    
    try:
        # button_Keywords=driver.find_element(By.ID,'keywords')
        # button_Keywords.click()
        Author_Keywords_element = driver.find_elements(By.XPATH,'//a[contains(@data-tealium_data,"Author Keywords")]')
        print(len(Author_Keywords_element))
        info["Author Keywords"] = [e.text for e in Author_Keywords_element if len(e.text)>0]
    except Exception as e:
        info["Author Keywords"] = None


    return info

def save_json(data,filename="output.json"):
    with open(filename, "w") as outfile: 
        json.dump(data, outfile,indent = 4)

def sortBy(by):
    wait = WebDriverWait(driver, 100)
    wait.until(EC.element_to_be_clickable((By.XPATH,"//*[@label='Sort By']//button")))
    dropdown=driver.find_element(By.XPATH,"//*[@label='Sort By']//button")
    dropdown.click()
    # input()
    # button=driver.find_element(By.XPATH,f"//button[text()='{by} ']")
    # wait = WebDriverWait(driver, 100)
    # wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Newest')]")))
    # Add a small wait to ensure the dropdown options are rendered
    # wait.until(EC.visibility_of_element_located((By.XPATH, f"//button[contains(text(), '{by}')]")))

    # Try clicking the button using JavaScript if normal click does not work
    button = driver.find_element(By.XPATH, f"//button[contains(text(), '{by}')]")

    try:
        button.click()
    except ElementNotInteractableException:
        driver.execute_script("arguments[0].click();", button)

def main():
    info={
        "papers":[]
    }
    global driver
    driver = load_homepage()
    search('security')
    # for i in ['Newest',]
    # sortBy('Relevance')

    paper_list=get_papers()
    for i in paper_list:
        inf=extract_data(i)
        info["papers"].append(inf)
        # print(info)
    # inf=extract_data("https://ieeexplore.ieee.org/document/10568376")
    # info["papers"].append(inf)
    # print(info)
    save_json(info,'relevance.json')
# #
    search('security')
    sortBy('Newest')
    info = {
        "papers": []
    }
    paper_list = get_papers()
    for i in paper_list:
        inf = extract_data(i)
        info["papers"].append(inf)
        # print(info)
    # print(info)
    save_json(info,"newest.json")



if __name__ == '__main__':
    main()

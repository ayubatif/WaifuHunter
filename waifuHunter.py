import time
import os
import sys
from selenium import webdriver

def spellCheck(query):
    from bs4 import BeautifulSoup
    from urllib.request import Request, urlopen

    request = Request("https://www.google.com/search?q="+'+'.join(query.split()), headers={'User-Agent': 'Mozilla/5.0'})
    try:
        page = urlopen(request).read()
    except:
        print("invalid URL")
		
    correction = ""
    spell = BeautifulSoup(page,"html.parser").findAll("a",{"class":["spell"]})

    for sp in spell[:1]:
        correction=sp.text

    if(len(correction)>0):
        query = correction

    print("Hunting for %s" %(query))
    return query

def nextPage(nodeFinder, driver):
    try:
        xpath = '//*[@id="pnnext"]'
        driver.find_element_by_xpath(xpath).click()
        nodeFinder = 1
        print('\n')

    except Exception as ex:
        print(ex)
        driver.quit()

def findEden(driver, data2):
    driver.get('https://www.pixiv.net')
    driver.execute_script("window.open('https://www.google.com', 'new window')")
    driver.switch_to_window(driver.window_handles[2])
    search_box = driver.find_element_by_name('q')
    search_box.send_keys('pixiv %s' %(data2))
    search_box.submit()
    
    edenNode = None
    edenFound = 0
    nodeFinder = 1

    while edenFound is 0:
        if nodeFinder > 100:
            print("couldnt find a link to a pic, try another character")
            driver.quit()
            main()

        if nodeFinder%10 is 0:
            nextPage(nodeFinder, driver)

        xpath = '//*[@id="rso"]/div[1]/div/div[%s]/div/div/div[1]/a[1]' %(nodeFinder%10)

        nodeFinder = nodeFinder + 1
        try:
            edenNode = driver.find_element_by_xpath(xpath)
        except:
            continue
        
        edenLink = edenNode.get_attribute('href')
        if "illust.php" in edenLink:
            edenFound = 1

    return edenLink

def scroll_down(driver):
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

def login(driver, username, password, EXPLICIT_CONTENT):
    driver.get('https://accounts.pixiv.net/login')
    userBox = driver.find_element_by_xpath('//*[@id="LoginComponent"]/form/div[1]/div[1]/input')
    passBox = driver.find_element_by_xpath('//*[@id="LoginComponent"]/form/div[1]/div[2]/input')
    userBox.send_keys(username)
    passBox.send_keys(password)
    passBox.submit()
    time.sleep(3)
    driver.get("https://www.pixiv.net/setting_user.php")
    if EXPLICIT_CONTENT is True:
        driver.find_element_by_xpath('//*[@id="page-setting-user"]/div/div[2]/div[2]/form/table/tbody/tr[2]/td/dl/dd[1]/label[1]/input').click()
    else:
        driver.find_element_by_xpath('//*[@id="page-setting-user"]/div/div[2]/div[2]/form/table/tbody/tr[2]/td/dl/dd[1]/label[2]/input').click()
    driver.find_element_by_xpath('//*[@id="page-setting-user"]/div/div[2]/div[2]/form/div/input').click()

def pixiv_links(driver, eden, dataLimit):
    pixiv_links = []
    i = 0
    n = 0

    while n < 1:
        driver.get(eden)
        scroll_down(driver)
        time.sleep(10)

        pixiv_links.append(driver.current_url)
        for j in range(1,180):
            pixiv_links.append(driver.find_element_by_xpath('//*[@id="root"]/div[1]/div/aside[3]/div[1]/ul/li[%s]/div/a'%(j)).get_attribute('href'))
            if (180*i + j + i+1) > dataLimit:
                n = 1
                break

        eden = pixiv_links[180*i + i+1]
        i = i + 1

    return pixiv_links

def isAlertPresent(driver):
    try:
        driver.switch_to().alert()
        return True
    except:
        return False
		
def scrape_images(pixiv_links, driver):
    from selenium.webdriver.common.keys import Keys
    for i in range(len(pixiv_links)):
        driver.get(pixiv_links[i])
        driver.find_element_by_xpath('//*[@id="pxvdwn_l"]').click()
        while isAlertPresent(driver) is True:
            alert = driver.switch_to.alert
            alert.accept()
        time.sleep(5)
        print("done with %d pix" %(i+1))
		
def extensionSetup(driver):
    driver.get('chrome-extension://fnbkeopcpjainobjebddfcnnknmfipid/options.html')
    driver.find_element_by_xpath('//*[@id="option_list"]/div[4]/label[3]/input').click()
    driver.find_element_by_xpath('//*[@id="save"]').click()

def main():
    loginData = ['whxsss', 'saberisbestdotcom', '']
    while len(loginData[2]) < 1:
        loginData[2]=spellCheck(input("Please type waifu\n>>>"))
    EXPLICIT_CONTENT = False
    """
    if input("type 'y' if you would like to enable explicit R18 pix, else enter: ") == 'y':
        EXPLICIT_CONTENT = True
    """
    dataLimit = input("num of pix: ")
    while(len(dataLimit)==0):
        dataLimit = input("num of pix: ")
    dataLimit = int(dataLimit)
    download_path = os.getcwd() + '\\' + loginData[2]
    print('Downloading %d pix to %s' %(dataLimit, download_path))

    from selenium.webdriver.chrome.options import Options
    chrome_options = Options()
    chrome_options.add_experimental_option('prefs', {
    'profile.default_content_setting_values.automatic_downloads': 1,
    'download.default_directory':download_path
    })
    chrome_options.add_extension(os.getcwd() + '\\pdv1.2.10.72.crx')
    driver = webdriver.Chrome(chrome_options=chrome_options)
    extensionSetup(driver)
    login(driver, loginData[0], loginData[1], EXPLICIT_CONTENT)
    try:
        os.mkdir(loginData[2])
    except:
        print(' ')
    scrape_images(pixiv_links(driver, findEden(driver, loginData[2]), dataLimit), driver)
    driver.quit()
    
main()

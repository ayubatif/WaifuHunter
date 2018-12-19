import time
import os
import sys
from selenium import webdriver

def encodeQuery(q):
    """Converts space to + in url component"""
    return '+'.join(q.split())

def getSoup(link):
    """Gets soup object for HTML parsing purposes"""

    from bs4 import BeautifulSoup
    from urllib.request import Request, urlopen

    request = Request(link, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        page = urlopen(request).read()
    except:
        print("invalid URL")
    return BeautifulSoup(page,"html.parser")

def spellCheck(query):
    """Updates query if goog has spelling suggestion"""

    goog = "https://www.google.com/search?q="+encodeQuery(query)

    soup = getSoup(goog)
    correction = ""
    spell = soup.findAll("a",{"class":["spell"]})

    for sp in spell[:1]:
        correction=sp.text

    if(len(correction)>0):
        query = correction

    print("Hunting for %s" %(query))
    return query

def extensionSetup(driver):
    driver.get('chrome-extension://fnbkeopcpjainobjebddfcnnknmfipid/options.html')
    driver.find_element_by_xpath('//*[@id="option_list"]/div[4]/label[3]/input').click()
    driver.find_element_by_xpath('//*[@id="save"]').click()

def nextPage(nodeFinder, driver):
    """Click next page button on google search"""

    try:
        xpath = '//*[@id="pnnext"]'
        driver.find_element_by_xpath(xpath).click()
        nodeFinder = 1
        print('\n')

    except Exception as ex:
        print(ex)
        driver.quit()

def findEden(driver):
    """Returns edenLink if found"""
    
    edenNode = None # the edenNode is the element to the initial pixiv pic
    edenFound = 0
    nodeFinder = 1 # incrementing int to find edenNode

    while edenFound is 0:
        if nodeFinder > 100:
            print("couldnt find a link to a pic, try another character")
            driver.quit()
            main()

        # Load next page of results
        if nodeFinder%10 is 0:
            nextPage(nodeFinder, driver)

        xpath = '//*[@id="rso"]/div[1]/div/div[%s]/div/div/div[1]/a[1]' %(nodeFinder%10)

        # Get a search result
        nodeFinder = nodeFinder + 1
        try:
            edenNode = driver.find_element_by_xpath(xpath)
        except:
            continue
        
        # Check if link leads to illust
        edenLink = edenNode.get_attribute('href')
        if "illust.php" in edenLink:
            edenFound = 1

    return edenLink

def scroll_down(driver):
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

def login(driver, username, password, EXPLICIT_CONTENT):
    from selenium.webdriver.common.keys import Keys
    
    """Go to login page and attempt login"""
    driver.get('https://accounts.pixiv.net/login')
    userBox = driver.find_element_by_xpath('//*[@id="LoginComponent"]/form/div[1]/div[1]/input')
    passBox = driver.find_element_by_xpath('//*[@id="LoginComponent"]/form/div[1]/div[2]/input')
    userBox.send_keys(username)
    passBox.send_keys(password)
    passBox.submit()
    if EXPLICIT_CONTENT is True:
        driver.get("https://www.pixiv.net/setting_user.php")
        driver.find_element_by_xpath('//*[@id="page-setting-user"]/div/div[2]/div[2]/form/table/tbody/tr[2]/td/dl/dd[1]/label[1]/input').click()
        driver.find_element_by_xpath('//*[@id="page-setting-user"]/div/div[2]/div[2]/form/div/input').click()
        
def collect_img_links(driver, eden, dataLimit):
    """get all jpg links"""
    pixiv_links = []
    img_links = []
    i = 0
    n = 0

    while n < 1:
        driver.get(eden)
        scroll_down(driver) # Scroll for full page
        time.sleep(3) # Wait for list load

        pixiv_links.append(driver.current_url)
        for j in range(1,180):
            url = driver.find_element_by_xpath('//*[@id="root"]/div[1]/div/aside[3]/div[1]/ul/li[%s]/div/a'%(j)).get_attribute('href')
            pixiv_links.append(url)
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
    for i in range(len(pixiv_links)):
        driver.get(pixiv_links[i])
        try:
            driver.find_element_by_xpath('//*[@id="pxvdwn_l"]').click()
            while isAlertPresent(driver) is True:
                alert = driver.switch_to.alert
                alert.accept()
            time.sleep(1)
        except:
            continue
        print("done with %d pix" %(i+1))

def main():
    # Get input. user=loginData[0] pass=loginData[1] waifu=loginData[2]
    loginData = ['whxsss', 'saberisbestdotcom', '']
    while len(loginData[2]) < 1:
        loginData[2]=spellCheck(input("Please type waifu\n>>>"))
    EXPLICIT_CONTENT = False
    if input("type 'y' if you would like to enable explicit R18 pix, else enter: ") == 'y':
        EXPLICIT_CONTENT = True
    dataLimit = input("num of pix: ")
    while(len(dataLimit)==0):
        dataLimit = input("num of pix: ")
    dataLimit = int(dataLimit)
    path = os.getcwd()
    download_path = path + '\\' + loginData[2]
    print('Downloading %d pix to %s' %(dataLimit, download_path))

    # Start the driver
    from selenium.webdriver.chrome.options import Options

    chrome_options = Options()
    chrome_options.add_experimental_option('prefs', {
    'profile.default_content_setting_values.automatic_downloads': 1,
    'download.default_directory':download_path
    })
    chrome_options.add_extension(path + '\\Pixiv-Downloader_v1.2.10.72.crx')
    driver = webdriver.Chrome(chrome_options=chrome_options)
    extensionSetup(driver)

    # Login
    login(driver, loginData[0], loginData[1], EXPLICIT_CONTENT)

    # Homepage search
    driver.execute_script("window.open('https://www.google.com', 'new window')")
    driver.switch_to_window(driver.window_handles[2])
    search_box = driver.find_element_by_name('q')
    search_box.send_keys('pixiv %s' %(loginData[2]))
    search_box.submit()

    # goog search
    edenLink = findEden(driver)

    # Get jpg links
    pixiv_links = collect_img_links(driver, edenLink, dataLimit)

    # Start downloading
    try:
        os.mkdir(loginData[2]) # make new folder
    except:
        print(' ') # use existing folder
    scrape_images(pixiv_links, driver)

    # Reset R18 Filter
    if EXPLICIT_CONTENT is True:
        driver.get("https://www.pixiv.net/setting_user.php")
        driver.find_element_by_xpath('//*[@id="page-setting-user"]/div/div[2]/div[2]/form/table/tbody/tr[2]/td/dl/dd[1]/label[2]/input').click()
        driver.find_element_by_xpath('//*[@id="page-setting-user"]/div/div[2]/div[2]/form/div/input').click()

    # Done
    driver.quit()

main()

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
        xpath = '//*[@id="rso"]/div/div/div[%s]/div/div/h3/a' %(nodeFinder)

        # Get a search result
        try:
            edenNode = driver.find_element_by_xpath(xpath)
        except:
            nextPage(nodeFinder, driver)
            continue

        # Get link
        edenLink = edenNode.get_attribute('href')
        print(edenLink)

        # Check if link leads to illust
        if "illust.php" in edenLink:
            edenFound = 1

        nodeFinder = nodeFinder    + 1

        # Load next page of results
        if nodeFinder > 10:
            nextPage(nodeFinder, driver)

    return edenLink

def scroll_down(driver):
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

def login(driver, username, password):
    """Go to login page and attempt login"""
    driver.get('https://accounts.pixiv.net/login')
    userBox = driver.find_element_by_xpath('//*[@id="LoginComponent"]/form/div[1]/div[1]/input')
    passBox = driver.find_element_by_xpath('//*[@id="LoginComponent"]/form/div[1]/div[2]/input')
    userBox.send_keys(username)
    passBox.send_keys(password)
    passBox.submit()
    time.sleep(3)

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
            url = driver.find_element_by_xpath('//*[@id="root"]/div[1]/div/aside[3]/div[1]/ul/li[%d]/div/a[2]' %(j)).get_attribute('href')
            pixiv_links.append(url)
            if (180*i + j + i+1) > dataLimit:
                n = 1
                break

        eden = pixiv_links[180*i + i+1]
        i = i + 1

    return pixiv_links

def isAlertPresent(driver):
    try:
        driver.switch_to().alert();
        return True
    except:
        return False

def scrape_images(pixiv_links, driver):
    for i in range(len(pixiv_links)):
        driver.get(pixiv_links[i])
        driver.find_element_by_xpath('//*[@id="pxvdwn_l"]').click()
        while isAlertPresent(driver) is True:
            alert = driver.switch_to.alert
            alert.accept()
            driver.find_element_by_xpath('//*[@id="pxvdwn_l"]').click()
        while isAlertPresent(driver) is True:
            alert = driver.switch_to.alert
            alert.accept()
        time.sleep(1)
        print("done with %d pix" %(i+1))

def main():
    # Get input. user=loginData[0] pass=loginData[1] waifu=loginData[2]
    loginData = ['whxsss', 'saberisbestdotcom', spellCheck(input("Please type waifu\n>>>"))]
    dataLimit = int(input("num of pix: "))
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
    login(driver, loginData[0], loginData[1])

    # Homepage search
    driver.get('http://www.google.com/xhtml')
    search_box = driver.find_element_by_name('q')
    search_box.send_keys('pixiv %s' %(loginData[2]))
    search_box.submit()

    # goog search
    edenLink = findEden(driver)

    # Get jpg links
    pixiv_links = collect_img_links(driver, edenLink, dataLimit)

    # Start downloading
    try:
        os.mkdir(loginData[2]) # pix folder
    except:
        print(' ')
    scrape_images(pixiv_links, driver)
    driver.quit()

main()

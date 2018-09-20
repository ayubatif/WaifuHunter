import time
import os
import sys
from selenium import webdriver
import requests


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

def nextPage(nodeFinder):
    """Click next page button on google search"""

    try:
        xpath = '//*[@id="pnnext"]'
        driver.find_element_by_xpath(xpath).click()
        nodeFinder = 1
        print('\n')

    except Exception as ex:
        print(ex)
        driver.quit()

def findEden():
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
            nextPage(nodeFinder)
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
            nextPage(nodeFinder)

    return edenLink

def scroll_down(driver):
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

def loginDetails():
    """Gets input and returns user/pass/waifu in list"""
    import getpass

    details = []
    details.append(input("Email or pixiv ID: "))
    details.append(getpass.getpass("Password: "))
    details.append(spellCheck(input("Please type waifu\n>>>")))
    return details


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
            url = driver.find_element_by_xpath('//*[@id="root"]/div[1]/div/aside[3]/div[1]/ul/li[%d]/a[2]' %(j)).get_attribute('href')
            pixiv_links.append(url)
            if (180*i + j + i+1) > dataLimit:
                n = 1
                break

        eden = pixiv_links[180*i + i+1]
        i = i + 1

    for j in range(len(pixiv_links)):
        print('done with %d' %(j+1))
        driver.get(pixiv_links[j])
        img_links.append(driver.find_element_by_class_name('_2r_DywD').get_attribute('src'))

    return img_links


class ImageScraper:
    """Downloads images to a path, given url list"""

    def __init__(self, waifu, urlz, download_path):
        self.waifu = waifu
        self.urlz = urlz
        self.download_path = download_path

        self.session = requests.Session()

    def scrape_images(self):
        i = 0
        for url in self.urlz:
            response = self.session.get(url).text
            i += 1
            self.save_image('%s_%d'%(self.waifu, i), url)

    def save_image(self, file_name, item_link):
        response = self.session.get(item_link, stream=True)
        print(response.status_code)
        if response.status_code == 200:
            with open(os.path.join(self.download_path, file_name), 'wb') as image_file:
                for chunk in response.iter_content(1024):
                    image_file.write(chunk)
        print(file_name)

def main():
    # Get input. user=loginData[0] pass=loginData[1] waifu=loginData[2]
    loginData = loginDetails()
    dataLimit = int(input("num of pix: "))
    path = os.getcwd()

    # Start the driver
    from selenium.webdriver.chrome.options import Options
    chrome_options = Options()
    chrome_options.add_argument("--window-size=1920x1080")
    driver = webdriver.Chrome(path + "\\chromedriver.exe")

    # Login
    login(driver, loginData[0], loginData[1])

    # Homepage search
    driver.get('http://www.google.com/xhtml')
    search_box = driver.find_element_by_name('q')
    search_box.send_keys('pixiv %s' %(loginData[2]))
    search_box.submit()

    # goog search
    edenLink = findEden()

    # Get jpg links
    pics = collect_img_links(driver, edenLink, dataLimit)
    driver.quit()

    # Start downloading
    scraper = ImageScraper(loginData[2], pics, path)
    scraper.scrape_images()

main()

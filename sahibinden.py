import pandas as pd
from bs4 import BeautifulSoup
#from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from seleniumwire import webdriver
from pprint import pprint
import time
from rotate_proxy import RotateProxy

class SahibindenScraper:
    SCRAPE_ADS_TYPE = 'CLICK'       # CLICK or REQUEST
    WINDOW_SIZE = 50

    def __init__(self, starting_page:int=1, ending_page:int=20, filename:str='test') -> None:
        self.starting_page = starting_page
        self.ending_page = ending_page
        self.filename = filename
        self.page_urls = []
        self.ad_urls = []
        self.ad_xpaths = []
        self.list_for_excel = []
        self.main_url = 'https://www.sahibinden.com/otomotiv-ekipmanlari-yedek-parca'
        self.used_proxy = None

        #self.rotate_proxy = RotateProxy(used_proxy=None)
        #self.used_proxy, self.seleniumwire_options = self.rotate_proxy.change_proxy()

        #self.browser = webdriver.Firefox(seleniumwire_options=self.seleniumwire_options)

        # run app
        self.main()

    
    def main(self):
        try:
            if self.SCRAPE_ADS_TYPE == 'CLICK':
                self.create_page_urls()
                self.create_ad_xpaths()

                for page_url in self.page_urls:
                    # change ip
                    self.rotate_proxy = RotateProxy(used_proxy=self.used_proxy)
                    self.used_proxy, self.seleniumwire_options = self.rotate_proxy.change_proxy()
                    self.browser = webdriver.Firefox(seleniumwire_options=self.seleniumwire_options)
                    self.browser.get(page_url)

                    # by-pass cloudflare
                    self._bypass_cloudflare()

                    # wait for context to load
                    WebDriverWait(self.browser, 600).until(EC.visibility_of_element_located((By.XPATH, '/html/body/div[5]/div[4]/form/div[1]/div[3]/table/tbody/tr[1]/td[2]/a[1]')))
                    counter = 1
                    for ad_xpath in self.ad_xpaths:  
                        try:
                            self.browser.find_element(By.XPATH, ad_xpath).click()
                            print(counter)
                            self.scrape_ad_info()
                            self.browser.back()
                            WebDriverWait(self.browser, 60).until(EC.visibility_of_element_located((By.XPATH, '/html/body/div[5]/div[4]/form/div[1]/div[3]/table/tbody/tr[1]/td[2]/a[1]')))
                            counter += 1
                        except:
                            counter += 1
                            continue
                    self.browser.quit()

                        


            elif self.SCRAPE_ADS_TYPE == 'REQUEST':
                self.create_page_urls()
                
                for page_url in self.page_urls:
                    self.get_ad_urls(url=page_url)

                    counter = 1
                    for ad_url in self.ad_urls:
                        if counter % 5 == 0:
                            self.browser.quit()
                            self.rotate_proxy = RotateProxy(used_proxy=self.used_proxy)
                            self.used_proxy, self.seleniumwire_options = self.rotate_proxy.change_proxy()
                            self.browser = webdriver.Firefox(seleniumwire_options=self.seleniumwire_options)
                            time.sleep(3)

                        print(counter)
                        self.browser.get(ad_url)
                        self.scrape_ad_info(ad_url=ad_url)
                        self.ad_urls = []

                        counter += 1

            else:
                return f'{self.SCRAPE_ADS_TYPE} is not a valid value, choose CLICK or REQUEST'
            
        except Exception as e:
            print(e)
        finally:
            self.convert_to_excel()

    
    def create_page_urls(self):
        for offset in range(self.starting_page - 1, self.ending_page):
            self.page_urls.append(f'{self.main_url}?pagingOffset={offset * self.WINDOW_SIZE}&pagingSize={self.WINDOW_SIZE}')


    def create_ad_xpaths(self):
        for ad_no in range(1, self.WINDOW_SIZE + 5):
            self.ad_xpaths.append(f'/html/body/div[5]/div[4]/form/div[1]/div[3]/table/tbody/tr[{ad_no}]/td[2]/a[1]')


    def get_ad_urls(self, url:str):
        self.browser.get(url)
        WebDriverWait(self.browser, 60).until(EC.visibility_of_element_located((By.XPATH, '/html/body/div[5]/div[4]/form/div[1]/div[3]/table/tbody/tr[1]/td[2]/a[1]')))
        r = self.browser.page_source
        soup = BeautifulSoup(r, 'lxml')

        a_tags = soup.find_all('a', attrs={'class':'classifiedTitle'})
        for a_tag in a_tags:
            self.ad_urls.append('https://www.sahibinden.com' + a_tag.get('href'))

    
    def scrape_ad_info(self):
        WebDriverWait(self.browser, 30).until(EC.visibility_of_element_located((By.CSS_SELECTOR, '.classifiedOtherBoxes')))

        has_badge = False
        try:
            self.browser.find_element(By.CSS_SELECTOR, '.badge')
            has_badge = True
        except:
            has_badge = False

        if has_badge:
            r = self.browser.page_source
            soup = BeautifulSoup(r, 'lxml')

            seller = self._get_text_from_element(soup, tag='span', default='-', attrs={'class':'storeInfo classified-edr-real-estate'})
            seller_name = self._get_text_from_element(soup, tag='div', default='-', attrs={'class':'paris-name'})
            title = self._get_text_from_element(soup, default='-', tag='h1', attrs=None)

            phone_number_1st, phone_number_2nd = self._get_phone_numbers(soup=soup, default='-')
            category_dict = self._get_categories(soup=soup, default='-')

            info = {
                'İlan Linki': self.browser.current_url,
                'Başlık': title,
                'Firma': seller,
                'Satıcı Adı': seller_name,
                'Telefon 1': phone_number_1st,
                'Telefon2': phone_number_2nd,
            }

            info = {**info, **category_dict}
            self.list_for_excel.append(info)

            pprint(info)
            print('\n-------------------------------------\n')
        time.sleep(5)
        
    
    def _get_text_from_element(self, soup:BeautifulSoup, default=None, **kwargs):
        try:
            if kwargs.get('attrs') is not None:
                element = soup.find(kwargs.get('tag'), attrs=kwargs.get('attrs'))
            else:
                element = soup.find(kwargs.get('tag'))
            return element.getText().strip()
        except:
            return default
        

    def _get_phone_numbers(self, soup:BeautifulSoup, default=None):
        try:
            phone_numbers = []
            phone_number_tags = soup.find_all('span', attrs={'class':'pretty-phone-part show-part'})

            for phone_number in phone_number_tags:
                phone_numbers.append(phone_number.getText().strip())
        except:
            phone_numbers = []

        if len(phone_numbers) != 0:
            phone_number_1st = phone_numbers[0]
            if len(phone_numbers) > 1:
                phone_number_2nd = phone_numbers[1]
            else:
                phone_number_2nd = default
        else:
            phone_number_1st = default
            phone_number_2nd = default
        
        return phone_number_1st, phone_number_2nd
    

    def _get_categories(self, soup:BeautifulSoup, default=None):
        try:
            categories = []
            category_tags = soup.find('div', attrs={'class':'search-result-bc'}).find('ul').find_all('li', attrs={'class':'bc-item'})

            for category in category_tags:
                categories.append(category.find('a').get('title').strip())
        except:
            categories = []

        if len(categories) == 0:
            return {'Ana Kategori':default, 'Alt Kategori 1': default, 'Alt Kategori 2': default, 'Alt Kategori 3':default}
        else:
            categories.pop(0)
            return {'Ana Kategori':categories[0], 'Alt Kategori 1': categories[1], 'Alt Kategori 2': categories[2], 'Alt Kategori 3': categories[3]}
        

    def _bypass_cloudflare(self):
        WebDriverWait(self.browser, 20).until(EC.frame_to_be_available_and_switch_to_it((By.XPATH,"//iframe[@title='Widget containing a Cloudflare security challenge']")))
        cloudflare_checkbox = WebDriverWait(self.browser, 20).until(EC.element_to_be_clickable((By.XPATH, "//label[@class='cb-lb']")))
        time.sleep(3)
        cloudflare_checkbox.click()
        
    
    def convert_to_excel(self):
        df = pd.DataFrame(self.list_for_excel)
        df.to_excel(f'{self.filename}.xlsx', index=False)
        print(f'Veriler {self.filename}.xlsx adlı excel dosyasına kaydedildi. ')



if __name__ == '__main__':
    scraper = SahibindenScraper()

# //*[@id="searchResultsTable"]/tbody/tr[1]/td[2]/a[1]
# //*[@id="searchResultsTable"]/tbody/tr[2]/td[2]/a[1]

# /html/body/div[5]/div[4]/form/div[1]/div[3]/table/tbody/tr[1]/td[2]/a[1]
# /html/body/div[5]/div[4]/form/div[1]/div[3]/table/tbody/tr[2]/td[2]/a[1]
# /html/body/div[5]/div[4]/form/div[1]/div[3]/table/tbody/tr[5]/td[2]/a[1]
# /html/body/div[5]/div[4]/form/div[1]/div[3]/table/tbody/tr[53]/td[2]/a[1]
# /html/body/div[5]/div[4]/form/div[1]/div[3]/table/tbody/tr[7]/td[2]/a[1]
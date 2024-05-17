from seleniumwire import webdriver
from dotenv import load_dotenv
import os
import time
import random

class RotateProxy:
    load_dotenv()
    PROXY_FILENAME = os.getenv('PROXY_FILENAME')
    BROWSER_PROFILE_PATH = os.getenv('BROWSER_PROFILE_PATH')
    
    def __init__(self, used_proxy:str=None):
        self.proxy_list = []
        self.used_proxy = used_proxy

        self.read_proxy_file()

        if self.used_proxy == None:
            self.used_proxy = random.choice(self.proxy_list)

    
    def read_proxy_file(self):
        with open(self.PROXY_FILENAME, mode='r', encoding='utf-8') as f:
            for line in f:
                self.proxy_list.append(line.rstrip('\n'))


    def change_proxy(self):
        used_proxy_index = self.proxy_list.index(self.used_proxy)
        if used_proxy_index >= len(self.proxy_list) - 1:
            self.proxy = self.proxy_list[0]
        else:
            self.proxy = self.proxy_list[used_proxy_index + 1]

        splitted_proxy = self.proxy.split(':')
        ip_port = str(splitted_proxy[0]) + ':' + str(splitted_proxy[1])
        username = str(splitted_proxy[3])
        password = str(splitted_proxy[4])

        seleniumwire_options = {
            'proxy':{
                'http':f'http://{username}:{password}@{ip_port}',
                'https':f'https://{username}:{password}@{ip_port}',
                'no_proxy':'localhost, 127.0.0.1'
            }
        }
        print(f'\n---------------------------------------------------\nThe proxy is changed, new IP: {ip_port}\n---------------------------------------------------\n')

        return self.proxy, seleniumwire_options

    
    def set_browser_proxy_options_using_selenium(self):
        '''
        Summary: This function sets the proxy preferences for Firefox.
        Caution: You need to open proxy settings then click OK button when browser is opened. 
        '''
        self.proxy = random.choice(self.proxy_list)
        ip, port = self.proxy.split(':')

        options = webdriver.FirefoxOptions()
        options.add_argument('--user-data-dir=', rf'{self.BROWSER_PROFILE_PATH}')
        options.set_preference('network.proxy.type', 1)
        options.set_preference('network.proxy.http', ip)
        options.set_preference('network.proxy.http_port', int(port))
        options.set_preference('network.proxy.share_proxy_settings', True)
        #options.set_preference('network.proxy.socks', ip)
        #options.set_preference('network.proxy.socks_port', int(port))
        options.set_preference('network.proxy.socks_version', 4)
        options.set_preference('network.http.use_cache', False)
    
        return options
    

if __name__ == '__main__':
    for i in range(1, 20):
        proxy = RotateProxy(used_proxy=None)
        used_proxy, seleniumwire_options = proxy.change_proxy()
        print(used_proxy)

        browser = webdriver.Firefox(seleniumwire_options=seleniumwire_options)
        browser.get('https://whatismyipaddress.com/')
        time.sleep(10)
        browser.quit()


        






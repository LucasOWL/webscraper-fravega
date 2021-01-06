import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
from datetime import datetime
from classes.BaseWebscraper import BaseWebscraper
from classes.FravegaWebscraper import FravegaWebscraper
from classes.CetrogarWebscraper import CetrogarWebscraper
from classes.SonyWebscraper import SonyWebscraper
from classes.JumboWebscraper import JumboWebscraper
from classes.DiscoWebscraper import DiscoWebscraper
from parameters import URLS_KEYWORDS, EMAIL_SUBJECT, USERNAME, PASSWORD, TO_ADDRESS, TIMEOUT

class Webscraper(object):

    COLORS = {
        'HEADER': '\033[95m',
        'OKBLUE': '\033[94m',
        'OKCYAN': '\033[96m',
        'OKGREEN': '\033[92m',
        'WARNING': '\033[93m',
        'FAIL': '\033[91m',
        'ENDC': '\033[0m',
        'BOLD': '\033[1m',
        'UNDERLINE': '\033[4m',
    }

    def __init__(self, urlsKeywordsDict, emailSubject, username, password, toAddress, timeout):
        self.urlsKeywordsDict = urlsKeywordsDict
        self.emailSubject = emailSubject
        self.username = username
        self.password = password
        self.toAddress = toAddress
        self.timeout = timeout
    
        self.webpageToObject = {
            'Frávega': FravegaWebscraper(url=self.urlsKeywordsDict['Frávega']['URL'],
                                         keywords=self.urlsKeywordsDict['Frávega']['keywords']),
            'Cetrogar': CetrogarWebscraper(url=self.urlsKeywordsDict['Cetrogar']['URL'],
                                           keywords=self.urlsKeywordsDict['Cetrogar']['keywords']),
            'Sony': SonyWebscraper(url=self.urlsKeywordsDict['Sony']['URL'],
                                           keywords=self.urlsKeywordsDict['Sony']['keywords']),
            'Jumbo': JumboWebscraper(url=self.urlsKeywordsDict['Jumbo']['URL'],
                                           keywords=self.urlsKeywordsDict['Jumbo']['keywords']),
            'Disco': DiscoWebscraper(url=self.urlsKeywordsDict['Disco']['URL'],
                                           keywords=self.urlsKeywordsDict['Disco']['keywords']),
        }
    
    def __repr__(self):
        return f'{self.__class__.__name__}({self.urlsKeywordsDict})'
    
    def __str__(self):
        return f'{self.__class__.__name__}: {self.urlsKeywordsDict}'
    
    def getAllProducts(self, verbose=True):
        """Returns a dictionary of product: price for every product in every webpage
        """

        products_by_webpage = {}
        for webpage in self.webpageToObject:
            if verbose:
                print(f'Scraping {webpage}...')
            products_by_webpage[webpage] = self.webpageToObject[webpage].getProducts()

        return products_by_webpage
    
    # Complete process
    def checkNewProducts(self):
        """Verifies if there is a new product for every webpage and sends an email when it occurs
        """

        initial_products_prices = self.getAllProducts(verbose=False)
        send_email_flag = True
        while True:
            now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

            try:
                new_products_prices = self.getAllProducts(verbose=True)
                for webpage in new_products_prices:
                    for product in new_products_prices[webpage]:
                        # Send email when there is a new product or if a product that did not have stock has been restocked
                        no_stock_status = BaseWebscraper.NO_STOCK_STATUS
                        product_restocked_flag = initial_products_prices[webpage][product] == no_stock_status and \
                                                 new_products_prices[webpage][product] != no_stock_status 
                        if product != '' and (product not in initial_products_prices[webpage] or product_restocked_flag):
                            send_email_flag = True
                            break
                    if send_email_flag:
                        break
                
                if send_email_flag:
                    self.sendEmail(productsPrices=new_products_prices)
                    print(f'{self.COLORS["OKGREEN"]}NEW PRODUCTS ALERT!{self.COLORS["ENDC"]} E-mail has been sent. Time: {now}')
                    send_email_flag = False
                    initial_products_prices = new_products_prices
                else:
                    print(f'{self.COLORS["WARNING"]}Nothing new{self.COLORS["ENDC"]}. Time: {now}')
            except Exception as e:
                print(f"Error: '{e}'. Time: {now}")
                continue
            
            time.sleep(self.timeout * 60)

    def sendEmail(self, productsPrices):
        # Start e-mail server
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.ehlo()
        server.starttls()
        server.ehlo()

        server.login(user=self.username, password=self.password)

        # Setup e-mail message
        message = MIMEMultipart('alternative')
        message['Subject'] = self.emailSubject
        message['From'] = 'Webscraping Bot'
        message['To'] = self.toAddress
        body = ''
        for webpage in productsPrices:
            body += f'{webpage.upper()}:\n'
            for product in sorted(productsPrices[webpage]):
                body += f'- {product}: {productsPrices[webpage][product]}\n'
            body += f"\nURL: {self.urlsKeywordsDict[webpage]['URL']}\n\n\n"
        body = MIMEText(body.encode('utf-8'), 'plain', _charset='utf-8')
        message.attach(body)

        server.sendmail(from_addr=self.username, to_addrs=self.toAddress, msg=message.as_string())
        
        server.quit()


# Start
ws = Webscraper(urlsKeywordsDict=URLS_KEYWORDS, emailSubject=EMAIL_SUBJECT, username=USERNAME,
                password=PASSWORD, toAddress=TO_ADDRESS, timeout=TIMEOUT)
ws.checkNewProducts()

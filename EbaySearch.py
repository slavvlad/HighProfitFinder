__author__ = 'vladi'

import sys
from optparse import OptionParser
import ebaysdk
from ebaysdk.finding import Connection as finding
from ebaysdk.trading import Connection as Trading
from ebaysdk.soa.finditem import Connection as FindItem
from ebaysdk.exception import ConnectionError
from amazon.api import AmazonAPI
from enum import Enum
from decimal import Decimal
import json
import time
import os.path
import datetime

fileName= "Result/Output%s.txt" % time.time()
print fileName
from datetime import date


class ebay_search(Enum):
    finding=0
    trading=1
    GetDetails=2

def Print(text):
    if type(text) != str:
        return
    utf8=text.encode('utf-8')

    print utf8
    with open(fileName, "a") as text_file:
        text_file.write(utf8 + '\n')

def to_file(content, tfile='State.json'):
    with open(tfile, 'w') as outfile:
        #content_dict = json.loads(content)
        json.dump(content, outfile)
def from_file(tfile='State.json'):
    if not os.path.isfile(tfile):
        return {}
    try:
        with open(tfile) as auth_file:
            data = json.load(auth_file)
    except:
        return {}
    return data

def FindCompletedItems(opts):
    strDoesNotApply = 'Does not apply'
    global_category={
    'kids':['116652','28145','176988','220','2984'],
    'kitchen':['20635','20625','20651','25357','25367','11874'],
    'baby_swig':['2990'],
    'pet':['1281','301','21097','1335','10823','48947','10823','47178','168213'],
    'home_and_garden':['11700','163008','163058','165253','13905','159907'],
    'headphones':['15052'],
    'garden_supplies':['2032'],
    'lamps':['112581'],
    #'organizers':['180915','146399','10321','168159'],
    'baby_gear':['100223'],
    'jewelry_and_watches':['98863','165254','39541','165670','165695','165703','47122'],
    'toys_hobbies':['220'],
    'baby':['100223','20433','2984'],
    'books':['171276','11104','46752','268'],
    #'valentines':['70978','170097'],
    'electronics':['3270','60207','14948','7294'],
    'fitness':['888','15273','40892','40883','28065','44075','44076','13362'],
    'dvd':['11232','617','46760'],
    'drone':['179697','182969'],
    #'valentines_day':['70978','35892','170097','907'],
    'threeD_supplies':['183062'],
    'jewelry_watches':['281'],
    'smart_assistent':['184435'],
    'camera':['625','15200','73459','150044','3326','27432','104058','11827'],
    'bushes_and_shrubs':['3185']}
    profit= 2 #$
    #profitToSearch=5
    profitFoundCount=0
    soldMoreThan=2
    pageIndex=0
    pageIndexMax=3
    days=10
    counter=0
    itemIdList=from_file()

    while True:
        for key, value in global_category.iteritems():
            for categoryId in value:
                for pageIndex in range(1, pageIndexMax):

                    dic = perfome_ebay_search(categoryId, pageIndex,ebay_search.finding,7,None,opts)


                    if  dic.get('searchResult') == None or ('_count' in dic['searchResult'] and int(dic['searchResult']['_count'])==0):
                        #Print ('where are no more result for current criteria.Prifits fount %s. Page index %s' % (profitFoundCount,pageIndex))
                        break

                    #dictstr = api.response_dict()
                    #api = FindItem(debug=opts.debug, consumer_id=opts.appid, config_file=opts.yaml)


                    amazon = AmazonAPI('AKIAJNSPI6YF2GJ6A5HA', 'hMSoDB9E0CkMSuQsuUU5fenIaysaqMup7YPvWnDr', 'slavvlad-20',region="US")

                    if 'item' not in  dic['searchResult']:
                        continue #there are not relevant product
                    for item in dic['searchResult']['item']:
                        if item['itemId'] in itemIdList and date.today()< datetime.datetime.strptime(itemIdList[item['itemId']], '%Y-%m-%d').date() + datetime.timedelta(days=days):
                            continue
                        itemIdList[item['itemId']]= str(date.today())
                        to_file(itemIdList)
                        counter=counter+1
                        #transation = api.execute('GetItemTransactions',{'NumberOfDays': 7,'ItemID': item['itemId']}).dict()
                        try:
                            transation = perfome_ebay_search(categoryId,pageIndex,ebay_search.trading, days, item['itemId'], opts)
                        except:
                            #e = sys.exc_info()[1]
                            #Print('GetItemTransactions failed due to the next reason %s\n'% e)
                            continue
                        if int(transation['PaginationResult']['TotalNumberOfEntries'])>soldMoreThan:
                            try:
                                itemDetails = perfome_ebay_search(categoryId,pageIndex,ebay_search.GetDetails,days,item['itemId'],opts)
                            except:
                                #e = sys.exc_info()[1]
                                #Print('\nGetItem failed due to the next reason %s\n'% e)
                                continue

                            #for r in records:
                            try:
                                upc= ''
                                ISBN=''
                                for i in itemDetails['Item']['ItemSpecifics']['NameValueList']:
                                    if type(i) is dict:
                                        if 'UPC' in i['Name'] and i['Value']<>strDoesNotApply:
                                            upc=i['Value']
                                            break
                                        elif 'ISBN' in i['Name'] and i['Value']<>strDoesNotApply:
                                            ISBN = i['Value']
                                            break
                                    else:
                                        if 'UPC' == i:
                                            upc=i
                                            continue
                                transDetails=tuple
                                if type(transation['TransactionArray']['Transaction']) is dict:
                                    transDetails= transation['TransactionArray']['Transaction']['TransactionPrice']
                                else:
                                    transDetails= transation['TransactionArray']['Transaction'][0]['TransactionPrice']
                                #Print("ID(%s) TITLE(%s) Sold times(%s) WatchCount(%s) Prise(%s%s)\n UPC(%s)" % (item['itemId'], item['title'][:50], transation['PaginationResult']['TotalNumberOfEntries'], item['listingInfo']['watchCount'] if  'watchCount' in item['listingInfo'] else 'Non',transDetails['value'],transDetails['_currencyID'],'Non' if upc is '' else upc  ))
                                #Print ("Title: %s" % item['title'])
                                #Print ("CategoryID: %s" % item['primaryCategory']['categoryId'])
                                try:
                                    if upc:# if the upc is not empty
                                        product = amazon.lookup(IdType='UPC',ItemId=upc, SearchIndex='All') #,ResponseGroup='Offers,Small'
                                        amazonPrise=calculate_profit(transDetails['value'],product,profit)
                                        if amazonPrise>0:
                                            profitFoundCount=profitFoundCount+1
                                            #print colored("Amazon Asin(%s) prise (%s)\n Amazon Title - %s" % (product.asin, amazonPrise,product.title),'red')
                                            #Print ("Amazon Asin(%s) prise (%s)\n Amazon Title - %s\nProfit found index - %s" % (product.asin, amazonPrise,product.title,profitFoundCount))
                                            Print("Profits %s index found %s\nEbay ID\n%s\nASIN\n%s\nUPC\n%s\nEbay Title\n %s\nAmazon Title\n %s\n-----------------"% (amazonPrise,profitFoundCount,item['itemId'],product.asin,product.upc,item['title'],product.title))

                                except:
                                    if ISBN:# if the upc is not empty
                                        try:
                                            product = amazon.lookup(IdType='ISBN',ItemId=ISBN, SearchIndex='All')
                                            amazonPrise=calculate_profit(transDetails['value'],product,profit)
                                            if amazonPrise>0:
                                                profitFoundCount=profitFoundCount+1
                                                #Print ("Amazon ISBN(%s) prise (%s)\n Amazon Title - %s\nProfit found index - %s" % (ISBN, amazonPrise,product.title,profitFoundCount))
                                                Print("Profits %s index found %s\nEbay ID\n%s\nASIN\n%s\nUPC\n%s\nEbay Title\n %s\nAmazon Title\n %s\n-----------------" % (amazonPrise, profitFoundCount, item['itemId'], product.asin, product.upc, item['title'], product.title))
                                        except:
                                            Print( "cannot fine %s UPC %s ISBN on Amazon" % (upc,ISBN))


                                #Print( "-------------------")
                            except :
                                e = sys.exc_info()[1]
                                Print(e)

def perfome_ebay_search(category_id, page_index,mode,num_days,item_id, opts):
    try:
        if mode==ebay_search.finding :
            api = finding(siteid='EBAY-US', config_file=opts.yaml, appid=opts.appid)
            response = api.execute('findCompletedItems', {
                # 'keywords': 'Baby Groot Flower Pot Head Wood Planter Figure Guardians of The Galaxy 3D Print',
                # 'keywords': 'thermal clothing',
                # 'keywords': 'valentines day gift',
                'categoryId': category_id,
                'itemFilter': [
                    {'name': 'Condition', 'value': 'New'},
                    {'name': 'HideDuplicateItems', 'value': 'true'},
                    {'name': 'SoldItemsOnly', 'value': 'false'},
                    {'name': 'LocatedIn', 'value': 'US'},

                    # {'name': 'MinPrice', 'value': '150', 'paramName': 'Currency', 'paramValue': 'USD'},
                    {'name': 'MaxPrice', 'value': '170', 'paramName': 'Currency', 'paramValue': 'USD'},
                    {'name': 'ListingType', 'value': 'FixedPrice'}
                ],
                'paginationInput': {
                    'entriesPerPage': '1000',
                    'pageNumber': page_index
                },
                'sortOrder': 'WatchCountDecreaseSort'
            })
        elif mode == ebay_search.trading:
            api = Trading(debug=opts.debug, config_file=opts.yaml, appid=opts.appid, certid=opts.certid, devid=opts.devid,
                    warnings=True, timeout=20)
            response = api.execute('GetItemTransactions',
                        {'NumberOfDays': num_days, 'IncludeVariations': 'true', 'ItemID': item_id})
        else:
            api = Trading(debug=opts.debug, config_file=opts.yaml, appid=opts.appid, certid=opts.certid, devid=opts.devid,
                          warnings=True, timeout=20)
            response = api.execute('GetItem',{'ItemID':item_id,'IncludeItemSpecifics':'true'})
    except:
        e = sys.exc_info()[1]
        if e.response._dict['Errors']['ErrorCode'] == '518':  # riched daily limit
            Print( str(datetime.datetime.now()) + " reached daily request limits. Going to sleep for one hour" )
            time.sleep(60 * 60)  # waiting for 1 hour
            perfome_ebay_search(category_id,page_index,mode,num_days,item_id,opts)
    return  response.dict()


def calculate_profit(ebay_prise,amazon, profit):
    ebay_prise=Decimal(ebay_prise)
    amazonTuple={}
    result=0
    amazon_prise=0
    if type(amazon) is list:
        for item in amazon:
            if amazonTuple=={} or amazonTuple.price_and_currency[0]>item.price_and_currency[0]:
                amazonTuple=item
    else:
        amazonTuple=amazon
    amazon_prise=amazonTuple.price_and_currency[0]

    fees =(amazon_prise+profit) * 19/100
    try:
        if amazon_prise+profit +fees<ebay_prise :
                #profitFoundCount=profitFoundCount-1
            #print colored('The profit is (%s)' % ((ebay_prise)-amazon_prise -fees), 'red' )
            #Print ('The profit is {}'.format((ebay_prise-amazon_prise -fees)))
            return (ebay_prise-amazon_prise -fees)

        #elif amazon_prise +fees<ebay_prise:
            #print colored('The profit is %s' % (ebay_prise-amazon_prise -fees), 'blue' )
         #   Print('The profit is {}'.format((ebay_prise - amazon_prise - fees)))
                #print colored("Amazon Asin(%s) prise (%s)\n Amazon Title - %s" % (product.asin, product.price_and_currency,product.title),'red')
        #Print ("Amazon Asin(%s) prise (%s)\nAmazon Title - %s" % (amazonTuple.asin, amazon_prise,amazonTuple.title))
    except:
        print "Unexpected error:", sys.exc_info()[0]
    return result

def AdvansedSearch(opt,product_id):
    try:
        api = finding(debug=opts.debug, appid=opts.appid,
                      config_file=opts.yaml, warnings=True)

        api_request = {

            'keywords': u'groot',
            'itemFilter': [
                {'name': 'Condition',
                 'value': 'Used'},
                {'name': 'LocatedIn',
                 'value': 'GB'},
            ],
            'affiliate': {'trackingId': 1},
            'sortOrder': 'CountryDescending',
        }

        response = api.execute('findItemsAdvanced', api_request)
        print response
        #dump(api)
    except ConnectionError as e:
        print(e)
        print(e.response.dict())

def getOrders(opts):

    try:
        api = Trading(debug=opts.debug, config_file=opts.yaml, appid=opts.appid, certid=opts.certid, devid=opts.devid,
                        warnings=True, timeout=20)

        #result=api.execute('GetOrders', {'NumberOfDays': 30})
        result=api.execute('GetItemTransactions', {'NumberOfDays': 30})
        print result
        #dump(api, full=False)

    except ConnectionError as e:
        print(e)
        print(e.response.dict())

def GetProductFeature(productId):
    from ebaysdk.shopping import Connection as Shopping
    try:
        api = Shopping(debug=opts.debug, appid=opts.appid,
                       config_file=opts.yaml, warnings=True)

        response = api.execute('FindProducts', {
            "ProductID": {'@attrs': {'type': 'Reference'},
                          '#text': productId}})
        print response
        #dump(api, full=False)

    except ConnectionError as e:
        print(e)
        print(e.response.dict())

def init_options():
    usage = "usage: %prog [options]"
    parser = OptionParser(usage=usage)

    parser.add_option("-d", "--debug",
                      action="store_true", dest="debug", default=False,
                      help="Enabled debugging [default: %default]")
    parser.add_option("-y", "--yaml",
                      dest="yaml", default=None,
                      help="Specifies the name of the YAML defaults file. [default: %default]")
    parser.add_option("-a", "--appid",
                      dest="appid", default=None,
                      help="Specifies the eBay application id to use.")
    parser.add_option("-p", "--devid",
                      dest="devid", default=None,
                      help="Specifies the eBay developer id to use.")
    parser.add_option("-c", "--certid",
                      dest="certid", default=None,
                      help="Specifies the eBay cert id to use.")

    (opts, args) = parser.parse_args()
    return opts, args

if __name__ == "__main__":
    print("FindItem samples for SDK version %s" % ebaysdk.get_version())
    (opts, args) = init_options()

    #AdvansedSearch(opts,11111)
    FindCompletedItems(opts)
    #getOrders(opts)

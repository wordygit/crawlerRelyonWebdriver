#! /usr/bin/env python 
# -*- coding: utf-8 -*-
import time
import threading
import os
import socket
import pcap
import random
import dpkt
import json
import sys
from datetime import datetime
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.common.exceptions	import UnexpectedAlertPresentException
from selenium.common.exceptions import NoAlertPresentException
from selenium.common.exceptions import TimeoutException
from log import Logger


############################################################################################
#why the socket.inet_ntoa(net) not eq to the ip of dev?
#IpOfDevToSniff = '192.168.1.0'
WhereToStoreSamples = '../pcap'                               
############################################################################################

 
class CrawlerExcetion(Exception):
    def __init__(self,err):
        self.err=err
    def __str__(self):
        return self.err

if os.path.exists(WhereToStoreSamples) == False:
    os.mkdir(WhereToStoreSamples)
Log = Logger('autoproto.crawler','crawler.log')   
_global_opensed = True      #starting of access websit, notify the _SnifferThr thread to start capture 
class _SnifferThr(threading.Thread):
    '''capture pcap during resource accessing'''
    def __init__(self, pcappath:str):
        threading.Thread.__init__(self)
        self.pcappath = pcappath
        self.ret = -1

    def run(self):
        try:
            Log.info('SnifferThr start, pcap file %s' % self.pcappath)
            iface = None
            for dev in pcap.findalldevs():
                net, mask = pcap.lookupnet(bytes(dev,'utf-8'))
                if not net: continue
                #why the socket.inet_ntoa(net) not eq to the ip of dev?
                #if IpOfDevToSniff == socket.inet_ntoa(net):
                if socket.inet_ntoa(net) != '0.0.0.0' and socket.inet_ntoa(mask) != '0.0.0.0':
                    iface = dev
                    break
            if not iface:
                Log.error('error no iface found')
                raise CrawlerExcetion('error no iface found')
            pc = pcap.pcap(iface)
            #ignore other protocol
            pc.setfilter('tcp || udp')
            with open(self.pcappath,'wb') as f:
                pfile = dpkt.pcap.Writer(f)
                for timestamp,packet in pc:
                    if _global_opensed == False:break
                    pfile.writepkt(packet, timestamp)
            self.ret = 0
            Log.info('SnifferThr end, pcap file %s' % self.pcappath)
        except Exception as e:
            self.ret = -1
            Log.warning(f'SnifferThr exception {e}, pcap file {self.pcappath}')

    @property
    def result(self):
        return self.ret



class _WebaccessThr(threading.Thread):
    '''access resources in urllist by browser'''
    PROCESS = { 'IE':('iexplore.exe','IEDriverServer.exe')}
    #web driver
    DRIVER = {'IE':webdriver.Ie}
    RESOURCELIMIT = 50
    #a timeout threshold
    TIMEOUT = {'IE':70}
    #for an url list, more the 50 percent means the end 
    WELLDONE_PCT = 0.5

    def __init__(self, browser:str, urllist):
        threading.Thread.__init__(self)
        self.urllist = urllist
        self.browser = browser
        self.ret = -1

    def kill(self, browser):
        '''kill '''
        os.system(r'taskkill /F /IM %s' % _WebaccessThr.PROCESS[browser][0])
        #os.system(r'taskkill /F /IM %s' % _WebaccessThr.PROCESS[browser][1])

    def run(self):
        global _global_opensed
        #avoid background traffic
        for p in _WebaccessThr.PROCESS:
            self.kill(p)
        time.sleep(0.5)
        try:
            browser = _WebaccessThr.DRIVER[self.browser]()
            browser.set_page_load_timeout(_WebaccessThr.TIMEOUT[self.browser])
        except WebDriverException as e:
            Log.warning(e)
            _global_opensed = False
            return


        _global_opensed = True
        cnt = 0
        #limit the quantity to increase the efficiency
        if len(self.urllist) <= _WebaccessThr.RESOURCELIMIT:
            idx = range(0, len(self.urllist))
        else:
            idx = random.sample(range(0, len(self.urllist)), _WebaccessThr.RESOURCELIMIT)

        def urlfilter(urls:list):
            suffixfilter = ('.css', '.js', '.doc', '.txt', '.php', '.pdf', '.jsp', '.xml', '.apk', '.zip', '.woff')
            nonlocal idx
            urls = [u[1] for u in enumerate(urls) if u[0] in idx]
            for url in urls[:]:
                for suffix in suffixfilter:
                    if url.endswith(suffix):
                        urls.remove(url)
        urlfilter(self.urllist)
        Log.info('WebaccessThr start')
        for url in self.urllist:
            try:
                browser.get(url)
                cnt += 1
        
                if float(cnt)/float(len(self.urllist)) > _WebaccessThr.WELLDONE_PCT:
                    self.ret = 0
            except UnexpectedAlertPresentException as e:
                Log.warning(e)
                try:
                    browser.switch_to.alert.dismiss()
                except NoAlertPresentException as e:
                    Log.warning(e)
                #browser.close()
                self.kill(self.browser)
                browser = _WebaccessThr.DRIVER[self.browser]()
                browser.set_page_load_timeout(_WebaccessThr.TIMEOUT[self.browser])
                continue
            except WebDriverException as e:
                Log.warning(e)
                #browser.close()
                self.kill(self.browser)
                browser = _WebaccessThr.DRIVER[self.browser]()
                browser.set_page_load_timeout(_WebaccessThr.TIMEOUT[self.browser])
                continue
        try:
            browser.close()
        except WebDriverException as e:
            Log.warning(e)
        _global_opensed = False
        Log.info('WebaccessThr end, %s  access %.2f%% resources' % (self.browser, (float(cnt)/float(len(self.urllist)))*100))

        #一个网址未访问,近程会率先退出导致抓报进程永久阻塞
        if cnt == 0:
            os.system('ping www.baidu.com')
            time.sleep(2)
        return

    @property
    def result(self):
        return self.ret


'''
interface
hreflist: list of url should be crawler
wherestore:     dir to store pcap
app:      domain name
browser:  brower tuple
ret:        0 success,1 fail
'''
def sample(hreflist, app:str, browser=('IE',)):
    ret = {}
    if len(hreflist) == 0 or not app:
        Log.warning('parameter error')
        return None
    wherestore = os.path.join(WhereToStoreSamples, app)
    if os.path.exists(wherestore) == False:
        os.mkdir(wherestore)
    global _global_opensed
    start = datetime.now()
    for br in browser:
        _global_opensed = True
        pcappath = wherestore + '/' + app + '_' + br + '_' + datetime.now().strftime('%Y%m%d%H%M') + '.pcap'
        print(pcappath)
        cnifferThread = _SnifferThr(pcappath)
        cnifferThread.start()
        webaccessThread = _WebaccessThr(br, hreflist)
        webaccessThread.start()
        cnifferThread.join()
        webaccessThread.join()
        ret[br] = cnifferThread.result|webaccessThread.result
        if ret[br] == 0 and os.path.getsize(pcappath) > 0:
            break
        time.sleep(2)
    Log.info('sample, %s %d resource elapsed %d seconds' % (app, len(hreflist), (datetime.now()-start).seconds))
    return ret


if __name__ == '__main__':
    wwwdict = {'xuebao.czu.cn':['http://xuebao.czu.cn']}
    for www in wwwdict:
        ret = sample(wwwdict[www], www, browser=('IE',))
        print(ret)

 


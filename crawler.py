#! /usr/bin/env python 
# -*- coding: utf-8 -*-
import re
import pycurl
import certifi
import time
import difflib
import chardet
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
#必须配置！ 要嗅探的网卡配置的网络及采样存放位置
NetToSniff = '192.168.1.0'
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
_global_opensed = True      #访问网页结束，设置该标志通知抓包停止
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
                if socket.inet_ntoa(net) == NetToSniff:
                    iface = dev
                    break
            if not iface:
                Log.error('error no iface found')
                raise CrawlerExcetion('error no iface found')
            pc = pcap.pcap(iface)
            with open(self.pcappath,'wb') as f:
                pfile = dpkt.pcap.Writer(f)
                for timestamp,packet in pc:
                    if _global_opensed == False:break
                    pfile.writepkt(packet, timestamp)
            self.ret = 0
            Log.info('SnifferThr end, pcap file %s' % self.pcappath)
        except:
            self.ret = -1
            Log.warning('SnifferThr exception, pcap file %s' % self.pcappath)

    @property
    def result(self):
        return self.ret



class _WebaccessThr(threading.Thread):
    '''access resources in urllist by browser'''
    #进程表
    PROCESS = { 'IE':('iexplore.exe','IEDriverServer.exe')}
    #浏览器实例化接口
    DRIVER = {'IE':webdriver.Ie}
    #每个域名资源上限，限制这个是为了提高速度和较少报文。默认未使用
    RESOURCELIMIT = 50
    #浏览器行为有差异，所以不同浏览器设置的超时时间不同
    TIMEOUT = {'IE':70}
    #浏览域名是否成功的标准，默认是成功访问50%以上的资源，可认为成功
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
        #减少背景流
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
        #随机挑选30个资源，效率会有所提升
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
                #资源访问50%可以满足抓包需求？
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
抓包接口：
hreflist, 超链接列表
wherestore,      包存放的目录
app,      网址或者app名，用做包名
browser,  浏览器元组
返回:        各浏览器的抓包成功或失败，0成功，1失败  {'Chrome':0, 'Firefox':0, 'IE':0}
'''
def sample(hreflist, wherestore:str, app:str, browser=('IE',)):
    ret = {}
    if len(hreflist) == 0 or not wherestore:
        Log.warning('parameter error')
        return None
    global _global_opensed
    start = datetime.now()
    for br in browser:
        _global_opensed = True
        pcappath = wherestore + '/' + app + '_' + br + '_' + datetime.now().strftime('%Y%m%d%H%M') + '.pcap'
        cnifferThread = _SnifferThr(pcappath)
        cnifferThread.start()
        webaccessThread = _WebaccessThr(br, hreflist)
        webaccessThread.start()
        cnifferThread.join()
        webaccessThread.join()
        ret[br] = cnifferThread.result|webaccessThread.result
        #根据非翻墙抓包的经验来看，主要采集一个浏览器抓包成功即可退出了，浏览器的优先级未IE,Chrome，Firefox
        if ret[br] == 0 and os.path.getsize(pcappath) > 0:
            break
        time.sleep(2)
    Log.info('sample, %s %d resource elapsed %d seconds' % (app, len(hreflist), (datetime.now()-start).seconds))
    return ret


if __name__ == '__main__':
    wwwdict = {'www.sohu.com':['http://www.sohu.com']}
    for www in wwwdict:
        ret = sample(wwwdict[www], '.', www[www.find('//')+2:], browser=('IE',))
        print(ret)

 


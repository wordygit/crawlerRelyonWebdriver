#! /usr/bin/evn python
# -*- coding:UTF8 -*-
#

import os
import logging

class Logger(object):
    '''
        通用log类
    '''
    def __init__(self,logger ='root',txt='tmp.log'):
        self.logger = logging.getLogger(logger)
        self.txt = txt
        self._init_logger()

    def _init_logger(self):
        self.logger.setLevel(logging.DEBUG)
        file = logging.FileHandler(self.txt)
        file.setLevel(logging.INFO)
        # 屏幕输出日志
        stream = logging.StreamHandler()
        stream.setLevel(logging.INFO)
        # 日志样式
        fm = logging.Formatter("[%(asctime)s    %(name)s    %(levelname)s  %(myfn)s:%(myfunc)s:%(mylno)d]  %(message)s")           
        file.setFormatter(fm)
        stream.setFormatter(fm)
        self.logger.addHandler(file)
        self.logger.addHandler(stream)	
        
    def _update_kwargs(self, kwargs):
        try:
            fn,lno,func, _ = self.logger.findCaller()
            fn = os.path.basename(fn)
        except Exception as ex:
            fn, lno, func = "(unknown file)", 0, "(unknown function)"
        if not "extra" in kwargs: kwargs["extra"] = {}
        kwargs["extra"]["myfn"] = fn
        kwargs["extra"]["mylno"] = lno
        kwargs["extra"]["myfunc"] = func

    def debug(self, msg, *args, **kwargs):
        self._update_kwargs(kwargs)
        self.logger.debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self._update_kwargs(kwargs)
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self._update_kwargs(kwargs)
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self._update_kwargs(kwargs)
        self.logger.error(msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        self._update_kwargs(kwargs)
        self.logger.critical(msg, *args, **kwargs)

if __name__ == '__main__':
    from log import Logger
    log = Logger('root','root.log')
    log.info('message')
    log.debug('message')
    log.warning('message')
    log.error('message')
    log.critical('message')

    log = Logger('root.basicpattern','basic.log')
    log.info('messagen')
    log.debug('message')
    log.warning('message')
    log.error('message')
    log.critical('message')  

    log = Logger('root.ruleextract', 'rule.log')
    log.info('message')
    log.debug('message')
    log.warning('message')
    log.error('message')
    log.critical('message')      
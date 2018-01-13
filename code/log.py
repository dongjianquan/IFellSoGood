#!/usr/bin/env python
# coding=utf-8
import logging  
import datetime


def create_log():
    logger = logging.getLogger("loggingmodule.NomalLogger")  
    todaystr = datetime.datetime.today().strftime('%Y_%m_%d_%Y_%H_%M')
    
    handler = logging.FileHandler("./"+todaystr+"_log.txt")  
    formatter = logging.Formatter("[%(levelname)s][%(funcName)s][%(asctime)s]%(message)s")  
    handler.setFormatter(formatter)  
    logger.addHandler(handler)  
    logger.setLevel(logging.DEBUG) 
    return logger
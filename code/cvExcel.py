#!/usr/bin/env python
# coding=utf-8

import xlwt     
import datetime

#需要xlwt库的支持
#import xlwt

def set_style(name,height,bold=False):
    style = xlwt.XFStyle()  # 初始化样式

    font = xlwt.Font()  # 为样式创建字体
    font.name = name # 'Times New Roman'
    font.bold = bold
    font.color_index = 4
    font.height = height

    # borders= xlwt.Borders()
    # borders.left= 6
    # borders.right= 6
    # borders.top= 6
    # borders.bottom= 6

    style.font = font
    # style.borders = borders

    return style

def SaveExcel(targetDict):
    
    file = xlwt.Workbook(encoding = 'utf-8')     
    #指定file以utf-8的格式打开
    last = datetime.datetime.today().strftime('%Y_%m_%d')

    table = file.add_sheet(last)           
    #指定打开的文件名

     #生成第一行
    row0 = [u'代码',u'收盘价格',u'开盘价格',u'最高价',u'最低价',u'成交量',u'日期']
    for i in range(0,len(row0)):
        table.write(0,i,row0[i],set_style('Times New Roman',220,True))
        
     #生成第1列  
    j = 1
    for code, values in targetDict.items():
        c_data = values.close.values
        o_data = values.open.values
        h_data = values.high.values
        l_data = values.low.values
        v_data = values.volume.values
        date_data = values.date.values
        print code,c_data,o_data
        table.write(j,0,code)
        table.write(j,1,c_data[2])
        table.write(j,2,o_data[2]) 
        table.write(j,3,h_data[2]) 
        table.write(j,4,l_data[2]) 
        table.write(j,5,v_data[2]) 
        table.write(j,6,date_data[2])         
        j=j+1;
        
    file.save(last+'.xls')

    

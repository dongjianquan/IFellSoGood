# coding:utf-8
import tushare as ts
import talib as ta
import datetime
import time
import sys
sys.path.append('/home/ubuntu/ys')
from MailNotification import MailNotification
from formular import lookback_trade_cal
#from cvExcel import SaveExcel
from log import create_log

#from formular import RSIRaise

#全局变量定义
#--------------------------------------------------------
# 接收通知邮箱
RECEIVE_ACCOUNTS = [ '181877329@qq.com','347834826@qq.com','825975777@qq.com','13832567834@163.com']
# 回溯长度设置
LOOKBACKDAYS = 3
# 成交量放大倍数
RATIO = 2
# 上影线比例超过多少就过滤
UP_LINE_RATIO = 0.3
# 唐奇安通道设置, 20为短周期，50为长周期
D_Channel = {'up': 20, 'down':10}
# 绘图K线长度
K_Length = 30
#--------------ta------------------------------------------

#15点前根据当前时间获取成交量系数
def get_radio_by_hour(now):
    plus = 1 #系数
    
    if (now > 15):
        plus = 1
    else:
        if(now < 12):
            hours = now - 9
        else:
            hours = (now - 13) + 2
        plus =   hours / float(4)  
        
    return RATIO *  plus
    

#15点前获取当前股票数据  通过5分钟数据累加  需要优化性能
def get_tday_data(code):
    logger.info("start")

    data = ts.get_k_data(code = code, ktype='5')    
    #无数据返回全0
    if (len(data) == 0):
        return 0,0,0,0,0
    
    #截取最后48条 然后过滤今天的数据
    
    today = data.tail(48)
    
    data_index = 0
    last = datetime.datetime.today().strftime('%Y-%m-%d')
    dates = today.date.values
    open_data = today.open.values
    high_data = today.high.values
    low_data =  today.low.values
    close_data =  today.close.values
    volume_data =  today.volume.values
    
    today_open=0
    today_close=0
    today_high=0
    today_low=0
    today_volume = 0
    
    #print today 
    while data_index < len(today) : 
        if last in dates[data_index]  :
            if(today_open == 0):
                today_open = open_data[data_index]
            today_close = close_data[data_index]
            if(today_high < high_data[data_index]):
                today_high = high_data[data_index]        
            if(today_low == 0 or today_low > low_data[data_index]):
                today_low = low_data[data_index]  
            today_volume = today_volume + volume_data[data_index]
        data_index += 1
    
    #logger.info(today_open,today_close,today_high,today_low,today_volume)
    logger.info("end")
    return today_open,today_close,today_high,today_low,today_volume        


#初始化日志文件
logger = create_log()


########### Log记录信息##########
logger.info("------"*3)
logger.info("Start find stokc,date=%s!" % datetime.datetime.now().strftime("%Y-%m-%d  %H:%m"))

################################


# 通过 tushare获取股票代码列表
# A股全部
totList = ts.get_stock_basics().index
                             
# 交易日回溯处理
last = datetime.datetime.today().strftime('%Y-%m-%d')
first,last = lookback_trade_cal(last,LOOKBACKDAYS)

########## Log记录信息##########
logger.info('开始日期: ' + first)
logger.info('结束日期: ' + last)
################################

# 通过tushare获取前lookback_days 个交易日数据,并筛选满足收盘价序列的股票
stockList = totList
targetDict = {}

i = 0
for stock in stockList:
    data = ts.get_k_data(code = stock,start = first, end = last )
    records = len(data)
    if (records == 0):
        continue
    logger.info("start analysis code=%s len=%d" % (stock,records))
    print("start analysis code=%s len=%d" % (stock,records))

    c_data = data.close.values
    v_data = data.volume.values   
    open_data = data.open.values
    high_data = data.high.values
    low_data = data.low.values
    
    data_index = 0
    c_flag = True
    v_flag = True

    while data_index < records - 1:
        if c_data[data_index] < c_data[data_index + 1]:
            data_index = data_index + 1
        else:
            c_flag = False
            break
        
    if c_flag:
        timenow = time.strftime('%H',time.localtime())
        is_holiday = ts.is_holiday(datetime.datetime.today().strftime('%Y-%m-%d'))

        if timenow < "15" and (not is_holiday):
            today_open,today_close,today_high,today_low,today_volume = get_tday_data(stock)
            if today_open == 0:
                continue
            
            #今天上涨    
            if today_close <= today_open:
                continue
            
            #上影线不要太长
            if (today_high - today_close) > (today_close - today_open) * UP_LINE_RATIO:
                continue  
            
            #当天放量
            RaalTimeRadio =  get_radio_by_hour(int(timenow)) #根据当前时间获取放量 比例
            v_data_index = 0
            while v_data_index < records - 1:
                #今天比昨天放量  
                if today_volume > v_data[v_data_index+1] * RaalTimeRadio:
                    v_data_index = v_data_index + 1
                else:
                    v_flag = False
                    break  
    
        else:
            #筛掉 记录丢失的股票
            if(records != LOOKBACKDAYS):
                continue
            
            #今天上涨    
            if open_data[records-1] > c_data[records-1]:
                continue
                
            #上影线不要太长
            if (high_data[records-1] - c_data[records-1]) > (c_data[records-1] - open_data[records-1]) * UP_LINE_RATIO:
                continue                
        
            #当天放量
            v_data_index = 0
            while (v_data_index < (records - 1)):
          
                #当天放量    
                if (v_data[records-1] > (v_data[v_data_index] * RATIO)):
                    v_data_index = v_data_index+1
                else:
                    v_flag = False
                    break     
                        
        #前两天成交量相差不超过50%               
        if abs(v_data[1]-v_data[0])/v_data[1] > 0.5:
            v_flag = False
                        
        if c_flag and v_flag:
            logger.info('Find one stock raise: %s ,todayV[%d] 1DayBefore[%d] 2DayBefore[%d] ' % (stock,v_data[records-1],v_data[1],v_data[0]))
            print('Find one stock raise: %s ,todayV[%d] 1DayBefore[%d] 2DayBefore[%d] ' % (stock,v_data[records-1],v_data[1],v_data[0]))
            logger.info("\n%s"%data)
            targetDict[stock] = data

    else:
        continue
    
# 量价条件
cvSet = set()
# 筛选条件1：阳线
positiveSet = set()
# 筛选条件2：MACD > 0, DIFF > DEA
macdSet = set()
# 筛选条件3：ADX >= 30, PDI > MDI
dmiSet = set()
# 筛选条件4：high 突破唐奇安通道
dcSet = set()
# 筛选条件5：一字板股票
# limitupSet = set()

## 筛选条件6：RSI3天上涨
#rsiSet = set()

logger.info('Find total stock :  %s.'  % len(targetDict))
 

#K线图路径
attachs = []
for code, values in targetDict.items():
    print (code)
    # 获取条件2,3的OHLC数据
    firstTech, last = lookback_trade_cal(last, 100)
    dataTech = ts.get_k_data(code=code, start=firstTech, end=last)

    # 条件5: 一字板股票
    last5 = dataTech.tail()
    if len(set(last5.mean()[:-2])) == 1:
        print (u'一字板：')
        print (dataTech)
        print (last5)
        print (set(last5.mean()[:-2]))
        print (last5.mean()[:-2])        
        targetDict.pop(code)
        # limitupSet.add(code)
        continue

#    #RSI
#    print "RSI指标：" 
#    #RSI连续3天上涨
#    rsi_flag = RSIRaise(code)
#    print rsi_flag
#    if rsi_flag:
#        rsiSet.add(code)
    
    #SaveExcel(targetDict)
    
    # 条件1
    if len(values[values.close >= values.open]) == LOOKBACKDAYS:
        positiveSet.add(code)

    # 条件2
    short = 12
    long = 26
    smooth = 9
    diff, dea, hist = ta.MACD(dataTech['close'].values, short, long, smooth)

    if hist[-1] > 0. and diff[-1] > 0. and dea[-1] > 0.:
        macdSet.add(code)

    # 条件3
    adxPeriod = 14
    adx = ta.ADX(dataTech['high'].values, dataTech['low'].values, dataTech['close'].values, adxPeriod)
    pdi = ta.PLUS_DI(dataTech['high'].values, dataTech['low'].values, dataTech['close'].values, adxPeriod)
    mdi = ta.MINUS_DI(dataTech['high'].values, dataTech['low'].values, dataTech['close'].values, adxPeriod)

    if adx[-1] >= 30 and pdi[-1] > mdi[-1]:
        dmiSet.add(code)

    # 计算唐奇安通道
    dataTech['d_up'] = ta.MAX(dataTech['high'].values, D_Channel['up'])
    dataTech['d_up'] = dataTech['d_up'].shift(1)
    dataTech['d_down'] = ta.MIN(dataTech['low'].values, D_Channel['down'])
    dataTech['d_down'] = dataTech['d_down'].shift(1)


    # 条件4
    if targetDict[code].tail(1)['high'].values >= dataTech.tail(1)['d_up'].values:
        dcSet.add(code)

    targetDict[code] = dataTech.tail(1)['d_up'].values[0]
    # print targetDict


    k_data = dataTech.tail(K_Length)
    # print k_data
    #plot_k(k_data, code,attachs, True)


# print attachs
    # ax = dataTech['close'].plot()
    # fig = ax.get_figure()
    # fig.savefig('{}.png'.format(code))

# cvSet = set(targetDict.keys) - limitupSet


########## Log记录信息##########
print u"满足量价规则： %d" %len(targetDict.keys()) 
print targetDict 
print u"满足阳线条件:  %d" %len(positiveSet) 
print positiveSet 
print u"满足MACD条件:  %d" %len(macdSet) 
print macdSet 
print u"满足DMI条件:  %d" %len(dmiSet) 
print dmiSet
print u"突破唐奇安通道：%d" %len(dcSet)
print dcSet
#print "RSI指标3天上涨:%d" %len(rsiSet)
#print rsiSet
print u"综上，符合所有： %d" %len(list(positiveSet & macdSet & dmiSet & dcSet))
print positiveSet & macdSet & dmiSet & dcSet
################################

# 生成邮件正文
if len(targetDict):
    msgText = '今日共发现{}个股票{}满足量价条件，技术指标筛选如下：\n'.format(len(targetDict), targetDict.keys()) + \
          '[1]满足阳线规则: {} \n'.format(list(positiveSet)) + \
          '[2]满足MACD规则: {} \n'.format(list(macdSet)) + \
          '[3]满足DMI规则: {} \n'.format(list(dmiSet)) + \
          '[4]突破唐奇安通道: {} \n'.format(list(dcSet)) + \
          '符合所有规则有{}个 \n'.format(len(list(positiveSet & macdSet & dmiSet & dcSet )))

    msgHtml = '<html><body><div><div>今日共发现<b><font color="#ff0000">{}</font></b>个股票<b><font color="#ff0000">{}</font></b>满足量价条件，技术指标筛选如下：</div>'.format(
        len(targetDict),targetDict.keys()) \
              + '<div><b>[1]满足阳线规则:</b> {}&nbsp;</div>'.format(list(positiveSet)) \
              + '<div><b>[2]满足MACD规则:</b> {}&nbsp;</div>'.format(list(macdSet)) \
              + '<div><b>[3]满足DMI规则:</b> {}&nbsp;</div>'.format(list(dmiSet)) \
              + '<div><b>[4]突破唐奇安通道:</b> {}&nbsp;</div>'.format(list(dcSet)) \
              + '<div>符合所有规则有{}个, 近{}个交易日走势如下&nbsp;</div></div>'.format(len(list(positiveSet & macdSet & dmiSet & dcSet )),K_Length) 

    for i in targetDict.keys():
        msgHtml = msgHtml + \
                '<div><b>【{}】</b>&nbsp;：建议入场价{}元</div>'.format(i, targetDict[i]) +\
                '<img src="cid:{}" alt="{}">'.format(i, i, i)
    msgHtml = msgHtml + '</body></html>'

else:
    msgText = '今日无收获.....'
    msgHtml = '<html><body><b>今日无收获.....</b></body></html>'


subject = last + ': '
# 发送通知
with MailNotification(RECEIVE_ACCOUNTS) as mail:
   if len(targetDict):
       subject = subject + u'恭喜发财! 发现{}个目标股'.format(len(targetDict))
   else:
       subject = subject + u'稍安勿躁! 未发现目标股'

   mail.send_multi(subject, msgHtml, 'html', attachs)

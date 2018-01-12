#coding=utf-8
# author: Y.Raul
# date : 2017-11-12
# 系统包导入
import pandas as pd
import numpy as np
import platform
import json
import datetime
import os

# 绘图包导入
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.finance as mpf
from matplotlib import gridspec
#分析包导入
import talib as ta

#数据包导入
import tushare as ts

import sys
sys.path.append('/home/ubuntu/ys')
from MailNotification import MailNotification

#reload(sys)   
#sys.setdefaultencoding('utf8')  

# 接收通知邮箱
RECEIVE_ACCOUNTS = ['181877329@qq.com','347834826@qq.com']

class PortfolioManger:
    """
    1. 记录入场时间，价格(读取json文件)
    2. 获取数据，并缓存
    3. 计算唐奇安通道，ATR，MACD
    4. 绘图
        3.1 K线图，包括唐奇安通道，入场价格，跟踪止损价格
        3.2 ATR波动图
        3.3 MACD图
    """
    def __init__(self):

        # 判断运行平台
        if platform.system() == 'Windows':
            self.jsonPath  = './portfolio.json'
        elif platform.system() == 'Linux':
            self.jsonPath = '/home/ubuntu/ys/portfolio.json'

        self.portfolio = {}
        self.stock_data = {}
        self.fig_attachs = []
        self.indicators = {}

        # 读取持仓文件
        tmp = []
        with open(self.jsonPath) as f:
            tmp.extend(json.loads(f.read()))

        self.stock_count = len(tmp)
        # print u"当前持仓股票共计{0}个".format(self.stock_count)

        for record in tmp:
            self.portfolio[record['code']] = {'name': record["name"], 'entry_price': record["entry_price"], 'entry_date': record["entry_date"], \
                                              'entry_pos': record["entry_pos"]}

        # 技术指标参数
        # 唐奇安通道设置, 上轨20为短周期，50为长周期
        self.D_Channel = {'up': 20, 'down': 10}
        #MACD设置
        self.Macd = {'short': 12, 'long': 26, 'smooth':9}

    def __backdate(self, back_days):
        """
        从今天回溯back_days个交易日
        :param back_days:
        :return:
        """
        trade_cal = ts.trade_cal()
        last = datetime.date.today().strftime('%Y-%m-%d')
        while not trade_cal[trade_cal.calendarDate == last].isOpen.values:
            last = datetime.datetime.strptime(last, '%Y-%m-%d') - datetime.timedelta(days=1)
            last = last.strftime('%Y-%m-%d')

        trade_cal = trade_cal[trade_cal.isOpen == 1]
        trade_cal.index = range(len(trade_cal))
        first = trade_cal.ix[(trade_cal[trade_cal.calendarDate == last].index[0] - back_days + 1), 0]
        trade_cal.index = range(len(trade_cal))
        first = trade_cal.ix[(trade_cal[trade_cal.calendarDate == last].index[0] - back_days + 1), 0]

        return first, last

    def getData(self):
        """
        获取股票数据
        :return:
        """
        for code, value in self.portfolio.items():
            entry_date = value['entry_date'][0]

            # 根据建仓日期与当前日期，确定股票日数据回溯长度
            self.delta_days = (datetime.datetime.today() - datetime.datetime.strptime(entry_date, '%Y-%m-%d')).days
            if self.delta_days >= 60:
                self.back_days = self.delta_days
            else:
                self.back_days = 60

            first, last = self.__backdate(self.back_days)
            self.stock_data[code] = ts.get_k_data(code, first, last )

            # print self.stock_data[code].tail()


    def calIndicator(self):
        """
        计算技术指标
        atr，macd，唐奇安通道
        :return:
        """
        for code in self.stock_data.keys():

            high = self.stock_data[code]['high'].values
            low = self.stock_data[code]['low'].values
            close = self.stock_data[code]['close'].values

            # 计算唐奇安通道
            self.stock_data[code]['d_up'] = ta.MAX(high, self.D_Channel['up'])
            self.stock_data[code]['d_up'] = self.stock_data[code]['d_up'] .shift(1)
            self.stock_data[code]['d_down'] = ta.MIN(low, self.D_Channel['down'])
            self.stock_data[code]['d_down'] = self.stock_data[code]['d_down'].shift(1)

            #计算ATR
            self.stock_data[code]['atr'] = ta.ATR(high, low, close)

            #计算MACD,diff 快， dea 慢， hist 差
            diff, dea, hist = ta.MACD(close, self.Macd['short'], self.Macd['long'], self.Macd['smooth'])
            self.stock_data[code]['diff'] = diff
            self.stock_data[code]['dea'] = dea
            self.stock_data[code]['hist'] = hist

            # print self.stock_data[code].tail()
            # 技术指标筛选
            last5 = self.stock_data[code].tail()
            # # MACD
            # if  last5.iloc[-1]['diff'] <= last5.iloc[-1]['dea']:
            #     print "MACD Fasle"
            #
            # # ATR
            # if last5.iloc[-1]['atr'] <= last5.iloc[-2]['atr']:
            #     print "ATR False"
            #     atrI = False
            #
            # # D_Channel
            # if last5.iloc[-1]['low'] <= last5.iloc[-1]['d_down']:
            #     print "D_Channel False"
            #     D_ChannelI = False

            self.indicators[code] = {'MACD': last5.iloc[-1]['diff'] >= last5.iloc[-1]['dea'], \
                                     'ATR': last5.iloc[-1]['atr'] >= last5.iloc[-2]['atr'],\
                                     'D_Down': last5.iloc[-1]['low'] >= last5.iloc[-1]['d_down']}


    def createFig(self):
        """
        生成图片：
        1、K线图，包含唐奇安通道，成交量, 入场位置
        2、ATR图
        3、MACD图
        :return:
        """
        for code, data in self.stock_data.items():

            fig = plt.figure(figsize=(10, 6))
            gs = gridspec.GridSpec(4, 1, height_ratios=[2, 0.4, 0.8, 0.8])
            ax = plt.subplot(gs[0])
            ax2 = plt.subplot(gs[1])
            ax3 = plt.subplot(gs[2])
            ax4 = plt.subplot(gs[3])

            # 绘制K线图
            mpf.candlestick2_ochl(ax, data['open'], data['close'], data['high'], data['low'],
                                  width=0.6, colorup='red', colordown='green', alpha=1)
            # 绘制入场点
            entry_date = self.portfolio[code]['entry_date']
            entry_price = self.portfolio[code]['entry_price']
            for i in range(len(entry_date)):
                ax.annotate("{}".format(entry_price[i]), xy=(entry_date[i], entry_price[i] * 0.95), xytext=(entry_date[i], entry_price[i]*0.9),
                                 arrowprops=dict(facecolor='R', shrink = 0.05),
                                 horizontalalignment='left', verticalalignment='top')
                ax.axhline(entry_price[i], xmin = 1 - self.delta_days * 1.0 /self.back_days,color="y", linestyle="-.")
            # 绘制唐奇安通道
            ax.plot(data['date'], data['d_up'], color='r', label='Up: {} days'.format(self.D_Channel['up']))
            ax.plot(data['date'], data['d_down'], color='b',label='Down: {} days'.format(self.D_Channel['down']))
            ax.legend(loc = 0)
            ax.set_title(code)
            ax.grid(True)

            # 绘制成交量图
            mpf.volume_overlay(ax2, data['open'], data['close'], data['volume'], colorup='r', colordown='g', width=0.2, alpha=1)
            ax2.grid(True)

            # 绘制MACD图
            ax3.plot( data['diff'], color='y',label='diff')
            ax3.plot(data['dea'], color='b', label='dea')
            ax3.legend(loc = 0)
            ax3.grid(True)

            # 绘制ATR图
            ax4.plot(data['date'], data['atr'], color='r', label='atr')
            ax4.legend(loc = 0)
            ax4.set_xticks(range(0, len(data['date']), 5))
            ax4.set_xticklabels(data['date'][::5], rotation=45)
            ax4.grid(True)

            plt.subplots_adjust(hspace=0.09)

            # 保存图片
            figPath = os.getcwd() + '/{}.png'.format(code)
            fig.savefig(figPath, dpi=150, bbox_inches = 'tight')
            self.fig_attachs.append(figPath)
        # plt.show()


    def createMsg(self):
        """
        生成操作建议：
        1、MACD指标趋势：DIFF VS DEA
        2、ATR指标趋势
        3、唐奇安通道指标趋势
        :return:
        """
        self.msgHtml = '<html><body><div><div>当前共持仓<b><font color="#ff0000">{}</font></b>个股票，相关指标如下：</div>'.format(
            self.stock_count)

        for code, data in self.stock_data.items():
            if self.indicators[code]['MACD']:
                MACDmsg = '多头趋势'
            else:
                MACDmsg = '空头趋势'

            if self.indicators[code]['ATR']:
                ATRmsg = '趋势增强'
            else:
                ATRmsg = '趋势减弱'
            if self.indicators[code]['D_Down']:
                D_Downmsg = '平稳运行'
            else:
                D_Downmsg ='破位'

            name = self.portfolio[code]['name'].encode('utf8')
            print name
            msg = '<div><b><font color="#ff0000">{}</font></b></div>'.format(code) \
                  + '<div><b>[0]NAME: </b> <font color="#ff0000">{}</font></div>'.format(name) \
                  + '<div><b>[1]MACD: </b> <font color="#ff0000">{}</font></div>'.format(MACDmsg) \
                  + '<div><b>[2]ATR: </b> <font color="#ff0000">{}</font></div>'.format(ATRmsg) \
                  + '<div><b>[4]D_Down: </b> <font color="#ff0000">{}</font></div>'.format(D_Downmsg) \
                  + '<img src="cid:{}" alt="{}">'.format(code, code)

            self.msgHtml += msg

        self.msgHtml += '</body></html>'


if __name__ == "__main__":
    pm = PortfolioManger()
    pm.getData()
    pm.calIndicator()
    #pm.createFig()
    pm.createMsg()
    
    #发送邮件
    subject = datetime.date.today().strftime('%Y-%m-%d') + ': 持仓分析 '
    with MailNotification(RECEIVE_ACCOUNTS) as mail:
        msgHtml = pm.msgHtml
        mail.send_multi(subject, pm.msgHtml, 'html', pm.fig_attachs )

#coding=utf8
import os.path
import smtplib, json, email
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from  email.mime.multipart import MIMEMultipart
from email.header import Header
from email.utils import parseaddr,formataddr
from email import encoders
from email.MIMEImage import MIMEImage
import platform

RECEIVE_ACCOUNTS = '181877329@qq.com'

class MailNotification():
    def __init__(self, receive_accounts):
        self.receiveAccounts = receive_accounts
        if platform.system() == 'Windows':
            self.jsonPath  = './config.json'
        elif platform.system() == 'Linux':
            self.jsonPath = '/home/ubuntu/ys/config.json'
    
    def __enter__(self):

        self.get_account()
        self.connect_host()
        return self

    def __format__addr(self, s):
        name, addr = parseaddr(s)
        return formataddr(( \
            Header(name, 'utf-8').encode(), \
            addr.encode('utf-8') if isinstance(addr, unicode) else addr))

    def get_account(self):
        with open( self.jsonPath) as f:
       # with open('config.json') as f:
            config = json.loads(f.read())
            self.account = config['account']
            self.password = config['password']
            self.host = config['host']
            self.postfix = config['postfix']
            
    def connect_host(self):
        self.server = smtplib.SMTP(self.host)
        # self.server.set_debuglevel(1)
        self.server.login(self.account, self.password)
        
    def send_text(self, from_, tos_, subject, text, text_type):

        msg = MIMEText(text, text_type, 'utf-8')
        msg['From'] = self.__format__addr(u'股票小助手<%s>' % from_)    #发送邮箱地址
        # msg['To'] = to_    #接收邮箱地址
        msg['Subject'] = Header(subject, 'UTF-8')    #邮件主题，注意此处使用了UTF-8编码，不然发送中文乱码
        msg['Date'] = email.Utils.formatdate()          #发送时间
        # msg['To'] = to  # 接收邮箱地址

        try:
            failed = self.server.sendmail(from_, tos_, msg.as_string())
        except Exception , ex:
            print Exception, ex
            print 'Error - send failed'
        else:
            print "send success!"
        
    def send_notification(self, subject, notification, text_type):
        self.send_text(self.account + self.postfix, self.receiveAccounts,\
                subject,
                notification + '\n' ,
                text_type)

    def send_multi(self, subject, text, text_type, attachs ):

        # 邮件对象
        msg = MIMEMultipart()
        msg['From'] = self.__format__addr(u'股票小助手<%s>' % (self.account + self.postfix))    #发送邮箱地址
        # msg['To'] = to_    #接收邮箱地址
        msg['Subject'] = Header(subject, 'UTF-8')    #邮件主题，注意此处使用了UTF-8编码，不然发送中文乱码
        msg['Date'] = email.Utils.formatdate()          #发送时间
        # msg['To'] = to  # 接收邮箱地址

        # 邮件正文是MIMEText
        msg.attach(MIMEText(text, text_type, 'utf-8'))

        #添加附件
        for attach in attachs:
            with open(attach, 'rb') as f:
        #设置附件的MIME和文件名，扩展名
                fileName = os.path.basename(attach).split('.')[0]
                # extenName = os.path.splitext(attach)[1]
                # print fileName

                img = MIMEImage(f.read())
                img.add_header('Content-ID', fileName)
                msg.attach(img)

                # mime = MIMEBase('image', extenName, filename = fileName)
                # 加上必要的头信息:
                # mime.add_header('Content-Disposition', 'attachment', filename= fileName)
                # mime.add_header('Content-ID', '<0>')
                # mime.add_header('X-Attachment-Id', '0')
                # 把附件的内容读进来:
                # mime.set_payload(f.read())
                # 用Base64编码:
                # encoders.encode_base64(mime)
                # 添加到MIMEMultipart:
                # msg.attach(mime)

        try:
            failed = self.server.sendmail(self.account + self.postfix, self.receiveAccounts, msg.as_string())
        except Exception , ex:
            print Exception, ex
            print 'Error - send failed'
        else:
            print "send success!"

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.server.close()

if __name__=='__main__':
    #attachs = ['002879.png', '300708.png', '300672.png']
    attachs = []
    # attachs = ['/home/ubuntu/ys/tu-160.jpg']
    set1 = set(['002879','300708','300672'])
    set2 = set(['300708', '300672'])
    set3 = set(['300672'])
    set4 = set(['300708'])

    with MailNotification(RECEIVE_ACCOUNTS) as mail:
    #     msg = '<html><body><h1>Hello</h1>' +\
    # '<p><img src="cid:0"></p>' + \
    #           '<p><img src="cid:1"></p>' +\
    # '</body></html>'
        msgText = '今日共发现{}个股票满足量价条件，技术指标筛选如下：\n'.format(len(set1)) +\
            '[1]满足阳线规则: {} \n'.format(list(set2)) + \
            '[2]满足MACD规则: {} \n'.format(list(set3)) + \
            '[3]满足DMI规则: {} \n'.format(list(set4)) + \
            '综上，符合所有规则：{} \n'.format(list(set2 & set3 & set4 ))
        # mail.send_notification('First mail notification!', msg, 'html')
        msgHtml = '<html><body><div><div>今日共发现<b><font color="#ff0000">{}</font></b>个股票满足量价条件，技术指标筛选如下：</div>'.format(len(set1)) \
        +'<div><b>[1]满足阳线规则:</b> {}&nbsp;</div>'.format(list(set2))  \
        +'<div><b>[2]满足MACD规则:</b> {}&nbsp;</div>'.format(list(set3)) \
        +'<div><b>[3]满足DMI规则:</b> {}&nbsp;</div>' .format(list(set4))\
        +'<div>综上，符合所有规则：{}&nbsp;</div></div>'.format(list(set2 & set3 & set4 ))\
        +'<div>个股近20个交易日走势如下&nbsp;</div></div>'

        for i in list(set1):
            msgHtml = msgHtml + \
            '<img src="cid:{}" alt="{}">'.format(i,i,i)
        msgHtml = msgHtml + '</body></html>'

        mail.send_multi('带附件的邮件', msgHtml, 'html', attachs )

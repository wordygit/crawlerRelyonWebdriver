import csv
jiangsu2000 = {}
domain = []
f = open(r'D:\workspace\crawlerRelyonWebdriver\nodup2000.csv', 'r',encoding='gbk')
csvfile = csv.reader(f)

#文件到列名是 公司企业名称、域名(域名可能是多个域名通过逗号连接的字串)、简介
for line in csvfile:
    #第一行是列名， 跳过
    if line[0] == '业务': continue
    jiangsu2000[line[0]] = {}
    #把公司到域名都收集到到一起，计算出一个能作为协议名的特征
    if line[1] != None:
        #当个http//开头到域名
        if '//' in line[1] and not ',' in line[1]: 
            jiangsu2000[line[0]]['域名'] = [line[1].split('//')[1]]
        else:
            jiangsu2000[line[0]]['域名'] = [domain.split(':')[0] for domain in line[1].split(',')]

    #print(line[2])  
    jiangsu2000[line[0]]['简介'] = line[2]
    jiangsu2000[line[0]]['AppName'] = set()



for k,v in jiangsu2000.items():
    #k是公司或企业名称，  V是域名、简介的字典
    for x in v['域名']:
        #有的域名级别很多，多与2个‘.’,把后缀去掉，比如www.a.baoying.gov.cn 变成 www.baoying.gov
        if len(x.split('.')) > 4 and x.endswith('cn'):
            domainNosuffix = x.rsplit('.', 1)[0]
            jiangsu2000[k]['AppName'].add('.'.join(domainNosuffix.split('.')[-3:])) 
        #单纯域名级别>4的不多，先不用处理
        elif len(x.split('.')) > 4: 
            jiangsu2000[k]['AppName'].add(x)
        elif len(x.split('.')) == 4:
            domainNosuffix = x.rsplit('.', 1)[0]
            jiangsu2000[k]['AppName'].add(domainNosuffix[domainNosuffix.index('.')+1:])
            #if 'sj.js' in domainNosuffix[domainNosuffix.index('.')+1:]:
            #    print(domainNosuffix[domainNosuffix.index('.')+1:])
        else:
            if len(x.split('.')) ==2 or '.' not in x:
                jiangsu2000[k]['AppName'].add(x)
            else: 
                jiangsu2000[k]['AppName'].add(x[x.index('.')+1:])
    
    stat = {}
    for app in jiangsu2000[k]['AppName']:
        stat[app] = 0
        for x in v['域名']: 
            if app in x:
               stat[app] += 1
    statsorted = sorted(stat.items(), key=lambda item:item[1],  reverse=True)
    #if '南通' in k:
    #    print(statsorted)
    if len(statsorted)>1:
        if statsorted[0][0] == 'edu.cn' or statsorted[0][0] == 'com.cn' or statsorted[0][0] == 'org.cn' or statsorted[0][0] == 'js.cn':
            jiangsu2000[k]['AppName'] = statsorted[1][0]
        else: 
            jiangsu2000[k]['AppName'] = statsorted[0][0]
        #print(jiangsu2000[k]['AppName'])  
    else: 
        jiangsu2000[k]['AppName'] = list(jiangsu2000[k]['AppName'])[0]
    #if len(jiangsu2000[k]['AppName'].split('.')[0])< 5: 
    #    print(k, ':  ', jiangsu2000[k]['AppName'])
    for app in jiangsu2000[k]['AppName']:
        for x in v['域名']: 
            if '.'+jiangsu2000[k]['AppName'] not in x:
                pass
                #print('.'+jiangsu2000[k]['AppName'], ' not in ', x)
        

ff = open(r'D:\workspace\crawlerRelyonWebdriver\nodup2000_bak.csv', 'w', encoding='utf-8', newline='')
csvwriter = csv.writer(ff) 
csvwriter.writerow(['业务','协议名(特征)', '域名','中文简介','英文简介'])           


nodomain = {}
for k,v in jiangsu2000.items():
    v['域名'] = ','.join(v['域名'])
    des = None
    if v['域名'] and v['域名'] != 'None':
        #print(v['简介'])
        if v['简介'] and v['简介']!= 'None':
            des = v['简介'].strip('简介：').split('。')[0]
            if des.startswith('注册号：'): 
               des = k 
            csvwriter.writerow([k, v['AppName'], v['域名'], des, ''])
        else: 
            csvwriter.writerow([k, v['AppName'], v['域名'], k, ''])
    else:
        nodomain[k] = {}
        nodomain[k]['域名'] = 'None'
        nodomain[k]['简介'] = v['简介']
        nodomain[k]['AppName'] = 'None'

for k, v in nodomain.items(): 
    csvwriter.writerow([k, v['AppName'], v['域名'],  v['简介'], ''])

ff.close()
            
        


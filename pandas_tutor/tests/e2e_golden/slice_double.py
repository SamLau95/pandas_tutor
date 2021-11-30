# https://www.shanelynn.ie/summarising-aggregation-and-grouping-data-in-python-pandas/
import pandas as pd
import io

csv = """
index,date,duration,item,month,network,network_type
0,15/10/14 06:58,34.429,data,2014-11,data,data
1,15/10/14 06:58,13,call,2014-11,Vodafone,mobile
2,15/10/14 14:46,23,call,2014-11,Meteor,mobile
3,15/10/14 14:48,4,call,2014-11,Tesco,mobile
4,15/10/14 17:27,4,call,2014-11,Tesco,mobile
5,15/10/14 18:55,4,call,2014-11,Tesco,mobile
6,16/10/14 06:58,34.429,data,2014-11,data,data
7,16/10/14 15:01,602,call,2014-11,Three,mobile
8,16/10/14 15:12,1050,call,2014-11,Three,mobile
9,16/10/14 15:30,19,call,2014-11,voicemail,voicemail
10,16/10/14 16:21,1183,call,2014-11,Three,mobile
11,16/10/14 22:18,1,sms,2014-11,Meteor,mobile
12,16/10/14 22:21,1,sms,2014-11,Meteor,mobile
13,17/10/14 06:58,34.429,data,2014-11,data,data
14,17/10/14 10:53,1,sms,2014-11,Tesco,mobile
15,17/10/14 11:19,1,sms,2014-11,Tesco,mobile
16,17/10/14 11:20,1,sms,2014-11,Meteor,mobile
17,17/10/14 17:22,1,sms,2014-11,Vodafone,mobile
18,17/10/14 17:23,1,sms,2014-11,Vodafone,mobile
"""
data = pd.read_csv(io.StringIO(csv))
data['duration'][8:13]  # <-- should show arrows after being turned into Series

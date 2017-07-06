# - * - coding: UTF-8 - * - 

import pymysql

# mysql --user=root -p
def connectionLocal():
    conn = pymysql.connect(host="127.0.0.1", # your host, usually localhost
                      user="root", # your username
                      passwd=None, # your password
                      db="yellowpage",
                      port=3306,
                      charset='utf8',
                      ) 
    cur = conn.cursor()

    return cur, conn

# mysql --user=root -p
def connections():
    conn = pymysql.connect(host="192.168.10.54", # your host, usually localhost
                      user="azb", # your username
                      passwd="anzhibin", # your password
                      db="yellowpage",
                      port=3306,
                      charset='utf8',
                      ) 
    cur = conn.cursor()

    return cur, conn


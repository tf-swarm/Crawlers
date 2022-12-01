import threading
import logging
import pymysql  # 导入 pymysql


from WorldCup2022.config import MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB

def CUD_data(sql, data):  # 增删改
    db = pymysql.connect(host=MYSQL_HOST,
                         user=MYSQL_USER,
                         password=MYSQL_PASSWORD,
                         db=MYSQL_DB,
                         port=3306,
                         charset='utf8mb4',
                         cursorclass=pymysql.cursors.DictCursor)  # 游标设置为字典类型

    # 使用cursor()方法获取操作游标
    cur = db.cursor()
    lock = threading.Lock()
    try:
        db.ping(reconnect=True)  # 查看链接是否断开，断开重新连
        lock.acquire()
        cur.execute(sql, data)  # 执行sql语句
        lock.release()

        # 涉及写操作要注意提交
        db.commit()
    except Exception as e:
        # db.rollback()
        raise e
    finally:
        pass
        # 关闭连接
        cur.close()
        db.close()


def CUD_batch(sql, data):  # 批量增删改
    db = pymysql.connect(host=MYSQL_HOST,
                         user=MYSQL_USER,
                         password=MYSQL_PASSWORD,
                         db=MYSQL_DB,
                         port=3306,
                         charset='utf8mb4',
                         cursorclass=pymysql.cursors.DictCursor)  # 游标设置为字典类型
    # 使用cursor()方法获取操作游标
    cur = db.cursor()

    try:
        db.ping(reconnect=True)  # 查看链接是否断开，断开重新连

        cur.executemany(sql, data)  # 执行sql语句

        # 涉及写操作要注意提交
        db.commit()
    except Exception as e:
        # db.rollback()
        raise e
    finally:
        pass
        # 关闭连接
        cur.close()
        db.close()


# 查
def read_data(sql, data=None):
    db = pymysql.connect(host=MYSQL_HOST,
                         user=MYSQL_USER,
                         password=MYSQL_PASSWORD,
                         db=MYSQL_DB,
                         port=3306,
                         charset='utf8mb4',
                         cursorclass=pymysql.cursors.DictCursor)  # 游标设置为字典类型

    # 使用cursor()方法获取操作游标
    cur = db.cursor()

    lock = threading.Lock()
    try:

        db.ping(reconnect=True)  # 查看链接是否断开，断开重新连
        if data:
            lock.acquire()
            cur.execute(sql, data)  # 执行sql语句
            lock.release()
        else:
            lock.acquire()
            cur.execute(sql)  # 执行sql语句
            lock.release()
        results = cur.fetchall()

    except Exception as e:

        results = None
        logging.error('%s:%s:%s'%(e,sql,data))
        print(e)
        raise e
    finally:
        # 关闭连接
        cur.close()
        db.close()

    return results

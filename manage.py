import os
from flask import Flask, jsonify
import pymysql
from flask import render_template
from flask import request
from werkzeug.utils import secure_filename
import oss2
from functools import wraps
from datetime import datetime
import re

from security import *


def record_error(func):
    @wraps(func)
    def inner():
        try:
            func()
        except Exception as e:
            with open("/home/12plus12/Blog/pan/error", "w") as f:
                f.write("[{}]".format(datetime.now()))
    return inner


@record_error
def a():
    b
    print("a")


def write_record(record):
    with open("record.txt", "a") as f:
        f.write(str([datetime.now()]) + str(record) + "\n")


def connect_mysql():
    conn = pymysql.connect(
        host="rm-uf6nvi051r1qg9lo2125010.mysql.rds.aliyuncs.com",
        user=MysqlAccount,
        password=MysqlPsd,
        database="filedb",
        charset="utf8"
    )
    return conn


app = Flask(__name__)


@app.route("/test", methods=["POST"])
def test():
    f = request.files["file"]
    file_name = secure_filename(f.filename)
    return file_name


@app.route("/favicon.ico")
def favicon():
    return app.send_static_file("img/favicon.ico")


@app.route("/pan/")
def pan():
    conn = connect_mysql()
    cursor = conn.cursor()
    sql = """
        SELECT * FROM filetb;
    """
    cursor.execute(sql)
    files = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template("pan.html", files=files)


@app.route("/upload", methods=["GET", "POST"], strict_slashes=False)
#@record_error
def upload_file():
    if request.method == "GET":
        return render_template("upload.html")
    elif request.method == "POST":
        f = request.files["file"]
        file_hash = request.form.to_dict()["file_hash"]
        category = request.form.get("category")
        file_name = secure_filename(f.filename)

        # 根据文件名后缀获取分类
        p = re.search(r"\.(\w+)", file_name)
        if p:
            if p.group(1) in ["txt", "doc", "xls", "xlsx", "ppt", "csv", "docx", "pptx", "tmd", "tmdx", "prd", "prdx", "pmd", "pmdx"]:
                category_id = 2
                ali_category = "documents"
            elif p.group(1) in ["jpg", "jpeg", "png", "gif", "psd", "tiff", "swf"]:
                category_id = 3
                ali_category = "images"
            elif p.group(1) in ["wma", "mp3", "cda"]:
                category_id = 4
                ali_category = "audios"
            elif p.group(1) in ["mp4", "flv", "rmvb", "mvb", "avi", "3gp"]:
                category_id = 5
                ali_category = "videos"
            else:
                category_id = 6
                ali_category = "others"
        else:
            category_id = 6
            ali_category = "others"

        conn = connect_mysql()
        cursor = conn.cursor()
        # 查询文件是否已存在
        sql = """
            SELECT * FROM filetb WHERE file_name = %s OR file_hash = %s;
        """
        res = cursor.execute(sql, [file_name, file_hash])
        if res:
            return jsonify({"status": 200, "is_existed": 1})

        sql = """
                INSERT INTO filetb (file_name, category_id, file_url, file_hash) VALUES (%s, %s, %s, %s);
        """
        cursor.execute(sql, [file_name, category_id,
                             "https://12plus12-bucket.oss-cn-shanghai.aliyuncs.com/{}/{}".format(ali_category, file_name), file_hash])
        sql = """
                INSERT INTO cfr(FID, CID) SELECT filetb.id, category.id FROM filetb INNER JOIN category ON filetb.file_name=%s AND category.id=%s;
        """
        cursor.execute(sql, [file_name, category_id])

        if category != "":
            sql = """
            INSERT INTO cfr(FID, CID) SELECT filetb.id, category.id FROM filetb INNER JOIN category ON filetb.file_name=%s AND category.category_name=%s;
            """
            cursor.execute(sql, [file_name, category])

        conn.commit()
        cursor.close()
        conn.close()

        f.save("/home/12plus12/Blog/pan/static/files/{}/{}".format(ali_category, file_name))

        auth = oss2.Auth(AccessKey, AccessPsd)
        bucket = oss2.Bucket(auth, "http://oss-cn-shanghai-internal.aliyuncs.com", "12plus12-bucket")
        bucket.put_object_from_file(ali_category + "/" + file_name,
                                    "/home/12plus12/Blog/pan/static/files/{}/{}".format(ali_category, file_name))
        return jsonify({"status": 200, "is_existed": 0})


from views import categories_blu, category_name_blu, add_category_blu, identify_image_blu
app.register_blueprint(categories_blu)
app.register_blueprint(category_name_blu)
app.register_blueprint(add_category_blu)
app.register_blueprint(identify_image_blu)

if __name__ == "__main__":
    a()
    #app.run(host="0.0.0.0", port=5000, debug=True)

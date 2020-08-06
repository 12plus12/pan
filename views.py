from flask import Blueprint, jsonify, request
import pymysql
import json
from werkzeug.utils import secure_filename
from PIL import Image

import locale
locale.setlocale(locale.LC_ALL, "C")
import tesserocr

from security import *

categories_blu = Blueprint("categories", __name__)
category_name_blu = Blueprint("category_name", __name__)
add_category_blu = Blueprint("add_category", __name__)
identify_image_blu = Blueprint("identify_image", __name__)


def connect_mysql():
    conn = pymysql.connect(
        host="rm-uf6nvi051r1qg9lo2125010.mysql.rds.aliyuncs.com",
        user=MysqlAccount,
        password=MysqlPsd,
        database="filedb",
        charset="utf8"
    )
    return conn


@categories_blu.route("/categories/")
def categories():
    # 返回所有分类条目
    conn = connect_mysql()
    cursor = conn.cursor()
    sql = """
        SELECT category_name, is_basic FROM category;
    """
    cursor.execute(sql)
    categories = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(categories)


@category_name_blu.route("/categories/<category_name>/")
def category_name(category_name):
    # 返回查询分类的文件数据
    conn = connect_mysql()
    cursor = conn.cursor()
    sql = """
        SELECT file_name, file_url, category_id FROM filetb WHERE id in (SELECT FID FROM cfr WHERE CID = (SELECT id FROM category WHERE category_name = %s));
    """
    cursor.execute(sql, category_name)
    files = cursor.fetchall()
    cursor.close()
    conn.close()

    return jsonify(files)


@add_category_blu.route("/add_category", methods=["POST"])
def add_category():
    # 处理添加分类请求，返回成功或失败
    data = str(request.get_data(), encoding="utf-8")
    category_name = json.loads(data)["category_name"]
    conn = connect_mysql()
    cursor = conn.cursor()
    sql = """
        SELECT * FROM category WHERE category_name = %s;
    """
    res = cursor.execute(sql, category_name)
    if res:
        cursor.close()
        conn.close()
        return jsonify({"status": 200, "is_existed": 1})
    # 添加分类
    sql = """
        INSERT INTO category (category_name) value (%s);
    """
    cursor.execute(sql, category_name)
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"status": 200, "is_existed": 0})


@identify_image_blu.route("/identify_image", methods=["POST"])
def identify_image():
    # 传入图片,识别图中文字,返回结果
    f = request.files["file"]
    file_name = secure_filename(f.filename)
    f.save("/home/12plus12/Blog/pan/static/files/identify/{}".format(file_name))

    image = Image.open("/home/12plus12/Blog/pan/static/files/identify/{}".format(file_name))
    image = image.convert("L")
    threshold = 127
    table = []
    for i in range(256):
        if i < threshold:
            table.append(0)
        else:
            table.append(1)

    image = image.point(table, "1")
    
    #import locale
    #locale.setlocale(locale.LC_ALL, 'C')
    #import tesserocr
    result = tesserocr.image_to_text(image)

    #locale.setlocale(locale.LC_ALL, "en_US.utf-8")

    return result


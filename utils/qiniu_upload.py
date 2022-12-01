from qiniu import Auth, put_file, etag
import uuid
import os
import requests

class QiNiu():

    def __init__(self):
        self.access_key = ""
        self.secret_key = ""
        self.bucked_name = "image"
        self.image_url = "https://file.image.com/"

    def qiniu_token(self, key):
        qin = Auth(access_key=self.access_key,secret_key=self.secret_key)
        token = qin.upload_token(self.bucked_name, key, 3600)
        return token

    def get_upload_img_url(self, url):
        try:
            file_path = self.download_image(url)
            # 指定图片名称,上传后保存的文件名
            file_name = '{}.png'.format(uuid.uuid4())
            # 指定上传空间，获取token
            token = self.qiniu_token(file_name)
            ret, info = put_file(token, file_name, file_path)
            if ret:
                image_file = self.image_url + ret.get('key')
                return image_file
            else:
                raise ValueError('上传失败，请重试')
        except ValueError as e:
            print("引发异常：", e)

    def download_image(self, url):
        file_path = self.create_image_dirs()
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36",
        }
        res = requests.get(url, headers=headers)
        with open(file_path, 'wb') as f:
            f.write(res.content)
        return file_path


    def create_image_dirs(self):
        # \local_img\b678-9c4415e85b38.png
        file_path = os.path.dirname(os.path.abspath(__file__))
        dirs = file_path + "\local_img"
        if not os.path.exists(dirs):
            os.makedirs(dirs)
        img_name = '{}.png'.format(uuid.uuid4().hex)
        image_path = dirs + "\\" + img_name
        return image_path


Qiniu = QiNiu()

# if __name__ == '__main__':
#     # url = "https://pbs.twimg.com/profile_images/1517222404296167426/9mYFBFUv_normal.jpg"
#     url = "https://pbs.twimg.com/card_img/1537836132989165568/sgeWt93I?format=png&name=small"
#     Qiniu = QiNiu()
#     imag = Qiniu.get_upload_img_url(url)
#     print("--imag--:", imag)





from selenium import webdriver
from time import sleep
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import os
from selenium.webdriver import Chrome, ChromeOptions, Safari
import shutil
import argparse

class DewuVideoUploader(object):
    def __init__(self, target="chrome"):

        print('creating...')
        # self.driver = webdriver.Safari()
        # opt = ChromeOptions()            # 创建Chrome参数对象
        # opt.headless = True              # 把Chrome设置成可视化无界面模式，windows/Linux 皆可
        if target == "chrome":
            self.driver = Chrome()
        elif target == "safari":
            self.driver = Safari()
        else:
            raise NotImplementedError
        print('created!')
        
    def upload(self, file_path, cookies, title, des, tags):
        # if channel_name is None:
        #     channel_name = self.channel_name
        # if title is None:
        #     title = self.title
        # if des is None:
        #     des = self.des
        # if tags is None:
        #     tags = self.tags
        

        self.driver.get('https://creator.dewu.com/release')
        self.driver.maximize_window()
        self._set_cookie(cookies)
        # sleep(10)
        self._set_file_input(file_path)
        sleep(1)
        self._set_title(title)
        sleep(1)
        self._set_des(des, tags)
        sleep(1)
        while not self._check_video_uploaded():
            sleep(1)

        # sleep(1000)
        # sleep(100)
        self._submit()
        sleep(2)
        
    def close(self):
        self.driver.close()
    
    def _set_cookie(self, cookies):
        for cookie in cookies:
            self.driver.add_cookie(
                {
                    'domain':cookie['domain'],
                    'name': cookie['name'],
                    'value':cookie['value'],
                    'path': cookie['path']
                }
            )
        self.driver.refresh()
    
    def _check_video_uploaded(self):
        try:
            progress = WebDriverWait(self.driver, 1).until(
            EC.presence_of_element_located((By.CLASS_NAME, "pd-progress-text"))
            )
            print(f"video uploading : {progress.get_attribute('title')}")
            return False
        except TimeoutException:
            return True
            
    def _set_file_input(self, file_path):
        file_input = WebDriverWait(self.driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']")))
        file_input.send_keys(file_path)
            
    def _set_title(self, title):
        title_box = WebDriverWait(self.driver, 2).until(EC.presence_of_element_located((By.ID, "title")))
        title_box.click()
        title_box.send_keys(title)
        
    def _set_des(self, des, tags):
        class_name = "richTextareaMain___EoGYP"
        des_box = WebDriverWait(self.driver, 2).until(EC.presence_of_element_located((By.CLASS_NAME, class_name)))
        # self.driver.execute_script("arguments[0].focus();", des_box)
        # des_box.send_keys(f"")
        # sleep(1)
        self.driver.execute_script(f'document.getElementsByClassName(\'{class_name}\')[0].innerHTML+=\'{des}\'')
        sleep(1)
        for i, html in enumerate(tags):
            # html = self.tags_dict[tag]
            command = f'document.getElementsByClassName(\'{class_name}\')[0].innerHTML+=\'{html}\''
            self.driver.execute_script(command)
            # sleep(1)
            command = f'document.getElementsByClassName(\'{class_name}\')[0].innerHTML+=\'&nbsp;\''
            self.driver.execute_script(command)
            sleep(1)
        des_box.send_keys(" ")

    def _submit(self):
        button = WebDriverWait(self.driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "button[type='submit']")))
        # print(button)
        button.click()
        # sleep(2)
        

# if __name__ == "__main__":
#     parser = argparse.ArgumentParser(description='Run Example')
#     parser.add_argument('data_dir', type=str, help='path of config file')
#     args = parser.parse_args()
#     dewu = DewuVideoUploader()
#     # channel_names = cookies_dict.keys()
#     channel_names = ['marko']
#     # video_dir = "/Users/Markos/Desktop/test_videos"
#     video_dir = args.data_dir
#
#     video_names = []
#     team_video_names = []
#
#     tags = ["上海村BA开打", "我在得物打篮球"]
#
#
#     team_names = os.listdir(video_dir)
#     team_names = [name for name in team_names if name[0] != '.']
#     for team_name in team_names:
#         if not os.path.isdir(os.path.join(video_dir, team_name)):
#             continue
#         video_names_team = os.listdir(os.path.join(video_dir, team_name))
#         if video_names_team == '.':
#             continue
#         print(video_names_team)
#         for video_name in video_names_team:
#             if video_name[0] == ".":
#                 continue
#             team_video_names.append(team_name)
#             video_names.append(video_name)
#
#     # team_names = []
#
#
#     for i, channel in enumerate(channel_names):
#
#         video_name = video_names[i]
#         player_name = video_name.split(".")[0].split('_')[-1]
#         team_name = team_video_names[i]
#         if player_name == team_name:
#             continue
#         # print("")
#         title = f"上海村BA来袭! 一起来看{team_name}队{player_name}精彩集锦!"
#
#         des = f"村BA上海站{team_name}队{player_name}精彩集锦"
#
#         # print(title)
#         # print(des)
#         file_name = os.path.join(video_dir, team_name, video_name)
#         tmp_file = "./tmp.mp4"
#         tmp_file = os.path.abspath(tmp_file)
#         print(file_name, tmp_file)
#         shutil.move(file_name, tmp_file)
#         # print(file_name, channel, title, des, tags)
#         # print(os.path.exists(file_name))
#         # print(type(file))
#         # print("\n")
#
#         dewu.upload(tmp_file, channel, title, des, tags)
#         shutil.move(tmp_file, file_name)
#     dewu.close()
        
    
    # channel_name = "marko"
    # upload_file = "/Users/Markos/Desktop/test.mp4"
    # title = "发布测试v2.1"
    # des = "Hello World again!!!"
    # tags = ["贵州村ba总决赛", "自动剪辑"]
    # print(upload_file, channel_name, title, des, tags)
    # print(os.path.exists(upload_file))

    # dewu.upload(upload_file, channel_name, title, des, tags)
    



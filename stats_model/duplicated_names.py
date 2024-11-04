# -*- coding: UTF-8 -*-
import json
import pandas as pd
import os
from tqdm import tqdm


def process_team_name(name):
    name = name.upper()
    if name in TEAM_multi_name_list:
        name = TEAM_multi_name_list[name]

    return name


def get_teams_from_game_name(game_name):
    team1, team2 = game_name.split("_")[1:]
    team1 = process_team_name(team1)
    team2 = process_team_name(team2)
    return [team1, team2]

def process_name(name, team):
    if "号" in name:
        name = name.split("号")[1]
    elif "#" in name:
        name = name.split("#")[1]
    if name == "":
        return "nobody"
    while name[0].isdigit():
        name = name[1:]
        if name == "":
            name = "nobody"
    name = name.upper()
    try:
        multi_name_list = eval(f"{team}_multi_name_list")
    except:
        multi_name_list = {}
    if name in multi_name_list:
        name = multi_name_list[name]

    return name



JUSHOOP_multi_name_list = {
                   "奥利佛": "PDH",
                    "奥利弗": "PDH",
                   "涛总": "韬总",
                   "东川路哈登": "哈登",
                    "潘达汉": "PDH",
                    "张钊伟": "张钊玮",
                    "YTT": "印添添",
                    "赵弈": "赵羿",
                    "ROCKYWANG": "ROCKY"
                    }

BNS_multi_name_list = {"立神": "周立立",
                       "徐孟杨": "徐孟扬",
                        "大曾": "曾浩丰",
                        "小黑": "唐恺胤",
                        "蔡": "蔡浩博",
                        "大宝贝": "孟皓骅",
                        "托尼": "张佳运",
                        "石头哥": "张诚",
                        "小胡": "胡叶晟",
                        "小刘": "刘悦纯",
                        "超超": "倪文超",}

光耀_multi_name_list = {"苗指导": "苗浩原",
                        "WILLIAM": "沈文亮",
                        "WENLIANG SHEN": "沈文亮",
                        "威廉": "沈文亮",
}

TOPGUN_multi_name_list = {"沙申鑫": "沙鑫申",
                        "小马": "马程忠",
}

SONIC_multi_name_list = {"小雨": "杨正宇",
                        "法兰克": "FRANK",
                         "伟哥": "WAYNE"
}
OP_multi_name_list = {"伍吉祥": "小黑"}


EMJ_multi_name_list = {
    "MARKOS": "马考",
}

EMR_multi_name_list = {

}

肘擎_multi_name_list = {

}




"""
同一个球队的多个名字
"""

TEAM_multi_name_list = {
    "CHALLENGER": "挑战者",
    "普渡": "PURDUE",
    "白队": "OP",
    "蓝队": "OP",
    "寿星队": "OP",
    "猛男队": "OP",
    "牛郎": "OP",
    "织女": "OP",
    "尊宝海鲜": "OP",
    "斌糖葫芦": "OP",
    "高飞": "OP",
    "饮水机管理员": "OP",
    "寿星": "OP",
    "虎先锋": "OP",
}




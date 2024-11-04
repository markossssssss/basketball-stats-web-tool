import os
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from matplotlib.colors import LinearSegmentedColormap
import pandas as pd
from pylab import mpl
from PIL import Image
from plottable import Table, ColDef
from plottable.cmap import normed_cmap
import numpy as np
import json
from PIL import Image, ImageFilter, ImageEnhance
import random
import argparse
from multiprocessing import Process
from . import decimal_to_percent
import platform


# 中文乱码和坐标轴负号处理。
matplotlib.rc('font', family='SimHei', weight='bold')
plt.rcParams['axes.unicode_minus'] = False
system = platform.system()
if system == "Darwin":
    plt.rcParams['font.family'] = ['Arial Unicode MS']

avg_title = "JUSHOOP平均"


def get_data_df(resource_dir, df_name):
    return pd.read_csv(os.path.join(resource_dir, df_name), header=0, index_col=0)

def get_img(resource_dir, team_name, img_name, get_path=False):
    postfixes = ["png", "jpg", "jpeg"]
    target_path = None
    for postfix in postfixes:
        img_path = os.path.join(resource_dir, "resources", team_name, img_name + "." + postfix)
        # print(img_path)
        if os.path.exists(img_path):
            target_path = img_path
    if target_path is None:
        raise FileNotFoundError("图片不存在")
    if get_path:
        return target_path
    return Image.open(target_path).convert("RGBA")

def get_output_path(resource_dir, team_name, file_name):
    target_dir = os.path.join(resource_dir, "results", team_name)
    if not os.path.exists(target_dir):
        os.mkdir(target_dir)
    return os.path.join(resource_dir, "results", team_name, file_name)
    

# 圆形头像
def circle_img(team, name, target_size, resource_dir=".", transparency_factor=0.7):
    try:
        ima = get_img(resource_dir, team, name)
    except:
        ima = Image.new('RGBA', (64, 64), (random.randint(1, 255), random.randint(1, 255), random.randint(1, 255), 0))
    
    size = ima.size
    r2 = min(size[0], size[1])
    if size[0] != size[1]:
        ima = ima.resize((r2, r2), Image.LANCZOS)
    
    r3 = int(r2 / 2)
    imb = Image.new('RGBA', (r3 * 2, r3 * 2), (255, 255, 255, 0))
    pima = ima.load()
    pimb = imb.load()

    for i in range(r2):
        for j in range(r2):
            lx = abs(i - r3)
            ly = abs(j - r3)
            l = (pow(lx, 2) + pow(ly, 2)) ** 0.5
            if l < r3:
                # 获取原始像素的 RGBA 值
                r, g, b, a = pima[i, j]
                # 调整 Alpha 通道，乘以透明度因子
                new_a = int(a * transparency_factor)
                # 将新像素值赋给目标图像
                pimb[i - (r3 - r3), j - (r3 - r3)] = (r, g, b, new_a)
    
    imb = imb.resize((target_size, target_size), Image.LANCZOS)
    
    return imb

def getImage(team, name, size, resource_dir):
    return OffsetImage(circle_img(team, name, size, resource_dir))

def fix_range(x, lower_bound, upper_bound):
    return max(lower_bound, min(x, upper_bound))

def map_range(x, origin, target):
    origin_gap = origin[1] - origin[0]
    target_gap = target[1] - target[0]
    rate = target_gap/origin_gap
    return target[0] + rate * (x - origin[0])

def process_percentage(target_list, idxes):
    for i in idxes:
        target_list[i] = target_list[i] * 100
    for i in range(len(target_list)):
        target_list[i] = round(target_list[i], 1)
    return target_list

def add_percentage(target_list, idxes):
    for i in idxes:
        target_list[i] = f"{target_list[i]}%"
    return target_list

def get_oppo_fig(team, resource_dir=".", negative_id=[5]):
    def get_bar_height(value, avg, reverse=False):
        if avg == 0: # 净胜分
            return fix_range(value * 10, 0, 100)
        value = (value - avg) / avg * (-1 if reverse else 1)
        return map_range(fix_range(value, -0.4, 0.3), [-0.4, 0.3], [0, 100])
    teams = [team, "对手"]

    df = get_data_df(resource_dir, f'{team}_OPPONENT.csv')
    terms = df.columns.values.tolist()[::-1]
    # 2、3是百分比
    percentage_idxes = [2, 3]
    bns_data = process_percentage(df.loc[team].values.tolist()[::-1], percentage_idxes)
    opponent_data = process_percentage(df.loc['对手'].values.tolist()[::-1], percentage_idxes)

    avg_data = process_percentage(df.loc['JUSHOOP平均'].values.tolist()[::-1], percentage_idxes)

    num_data1 = bns_data
    num_data2 = opponent_data


    # print(bns_data)
    # print(opponent_data)
    # print(avg_data)

    bar_data1 = [-1 * get_bar_height(bns_data[i], avg_data[i], reverse=(i in negative_id)) for i in range(len(bns_data))]
    bar_data2 = [get_bar_height(opponent_data[i], avg_data[i], reverse=(i in negative_id)) for i in range(len(opponent_data))]

    txt_colors = ["#EC4B08" if bns_data[i] >= opponent_data[i] else '#FFFFFF' for i in range(len(bns_data))]
    txt_colors2 = ["#EC4B08" if bns_data[i] < opponent_data[i] else '#FFFFFF' for i in range(len(bns_data))]

    bar_colors = ["#EC4B08" if bns_data[i] >= opponent_data[i] else '#707070' for i in range(len(bns_data))]
    bar_colors2 = ["#EC4B08" if bns_data[i] < opponent_data[i] else '#707070' for i in range(len(bns_data))]

    for i in negative_id:
        # 失误等负面数据
        txt_colors[i], txt_colors2[i] = txt_colors2[i], txt_colors[i]
        bar_colors[i], bar_colors2[i] = bar_colors2[i], bar_colors[i]

    num_data1 = add_percentage(num_data1, percentage_idxes)
    num_data2 = add_percentage(num_data2, percentage_idxes)
    # print(bar_data2)

    # data2 = list(map(lambda x: -1 * x if x > 0 else 0, opponent_data))
    # for i in range(len(city_name)):
    #     data1.append(random.randint(100, 150))
    #     data2.append(random.randint(100, 150)*-1)

    fig, ax = plt.subplots()

    bar_height = 0.6
    num_font = {'weight': 'bold',
            'size': 12,
            'family': 'serif',
            }

    ax.barh(range(len(terms)), [100 for i in range(len(bar_data1))], height=bar_height, color='#EEEEEE', alpha=0.05, left=22)
    ax.barh(range(len(terms)), [-100 for i in range(len(bar_data1))], height=bar_height, color='#EEEEEE', alpha=0.05, left=-22)

    a = ax.barh(range(len(terms)), bar_data1, height=bar_height, color=bar_colors, left=-22)
    b = ax.barh(range(len(terms)), bar_data2, height=bar_height, color=bar_colors2, left=22)

    # 为横向水平的柱图右侧添加数据标签。
    for i, rect in enumerate(a):
        w = rect.get_width()
        # print(w, rect.get_y(), rect.get_height())
        ax.text(-140, rect.get_y() + rect.get_height() / 2, f'{num_data1[i]}', ha='center', va='center', color=txt_colors[i], fontdict=num_font)
        ax.text(0, rect.get_y() + rect.get_height() / 2, terms[i], ha='center', va='center', color="white")

    for i, rect in enumerate(b):
        w = rect.get_width()
        ax.text(140, rect.get_y() + rect.get_height() / 2, f'{num_data2[i]}', ha='center', va='center', color=txt_colors2[i], fontdict=num_font)

    # plt.title(f'{teams[0]} vs {teams[1]}', loc='center', fontsize='25',
    #           fontweight='bold', color='red')

    plt.xlim(-140, 140)

    fontdict = {
        "fontsize": 20,  # 字体大小
        "color": "white",  # 字体颜色
        "family": "Arial Unicode MS",  # 字体类型，可参考：https://blog.csdn.net/weixin_45492560/article/details/123980725
        "fontweight": "black",  # 字体线条粗细，可选参数 :{"light": ,"normal":,"medium":,"semibold":,"bold":,"heavy":,"black"}
        "verticalalignment": "center",  # 设置水平对齐方式 ，可选参数 ：center、top、bottom、baseline
        "horizontalalignment": "center",  # 设置垂直对齐方式，可选参数：left、right、center
        "rotation": 0,  # 旋转角度，可选参数为:vertical,horizontal 也可以为数字
        "alpha": 1,  # 透明度，参数值0至1之间
        # "backgroundcolor": "black",  # 标题背景颜色
        # # 设置外边框
        # "bbox": {
        #     "boxstyle": "round",  # 边框类型，参考：https://vimsky.com/examples/usage/python-matplotlib.patches.BoxStyle-mp.html
        #     "facecolor": "black",  # 背景颜色，好像与上述 backgroundcolor 有冲突
        #     "edgecolor": "red",  # 边框线条颜色
        # }
    }

    spaces = (24-len(teams[0])//2) * " "
    ax.set_title(
        f'{teams[0]}{spaces}对手球队',
        fontdict=fontdict
    )

    plt.axis('off')

    # plt.show()
    target_path = get_output_path(resource_dir, team, 'oppo.png')
    plt.savefig(target_path, transparent=True, bbox_inches='tight')
    return target_path




def get_pro_subfig(team, fig, start, end, resource_dir=".", percentage_idxes=None, reverse_idxes=None, legend=False, idx=1):
    def get_bar_height(value, pro, reverse=False):
        value = (value-pro)/pro * (-1 if reverse else 1)
        return map_range(fix_range(value, -0.8, 0.2), [-0.8, 0.2], [0, 100])
    # 0: 80分 -0.4:0分 0.1:100分
    df = get_data_df(resource_dir, f'{team}_PRO.csv')

    terms = df.columns.values.tolist()[::-1][start:end]
    if percentage_idxes is None:
        percentage_idxes = []
    bns_data = process_percentage(df.loc[team].values.tolist()[::-1][start:end], percentage_idxes)
    pro_data = process_percentage(df.loc['NBA平均'].values.tolist()[::-1][start:end], percentage_idxes)
    avg_data = process_percentage(df.loc['JUSHOOP平均'].values.tolist()[::-1][start:end], percentage_idxes)

    # print(avg_data)
    # print(bns_data)
    # print(pro_data)
    #
    # print(df)
    if reverse_idxes is None:
        reverse_idxes = []
    bns_bar = [get_bar_height(bns_data[i], pro_data[i], reverse=(i in reverse_idxes)) for i in range(len(bns_data))]
    avg_bar = [get_bar_height(avg_data[i], pro_data[i], reverse=(i in reverse_idxes)) for i in range(len(bns_data))]
    # print(avg_bar)
    # print(bns_bar)

    txt_colors = ["#EC4B08" if bns_data[i] >= avg_data[i] else '#FFFFFF' for i in range(len(bns_data))]
    for i in reverse_idxes:
        # 失误等负面数据
        txt_colors[i]= "#EC4B08" if bns_data[i] < avg_data[i] else '#FFFFFF'



    # plt.style.use('seaborn')

    # avg_data = add_percentage(avg_data, percentage_idxes)
    # bns_data = add_percentage(bns_data, percentage_idxes)
    # pro_data = add_percentage(pro_data, percentage_idxes)
    # print(bar_data2)

    # data2 = list(map(lambda x: -1 * x if x > 0 else 0, opponent_data))
    # for i in range(len(city_name)):
    #     data1.append(random.randint(100, 150))
    #     data2.append(random.randint(100, 150)*-1)
    num_font = {'weight': 'bold',
                'size': 30,
                'family': 'serif',
                }
    width = 0.4 # NO NBA
    # width = 0.3 # with NBA
    # fig, ax = plt.subplots(figsize=(25, 10))
    ax = fig.add_subplot(2, 1, idx)

    # ax.bar()
    # ax.bar(range(len(terms)), [100 for i in range(len(terms))], lw=0.5, width=width, color='#EEEEEE', alpha=0.05)
    c = ax.bar(list(map(lambda x: x - width, range(len(terms)))), bns_bar, lw=0.5, width=width, color='#EC4B08')
    a = ax.bar(range(len(terms)), avg_bar, lw=0.5, width=width, color='#707070')
    # b = ax.bar(list(map(lambda x: x + width, range(len(terms)))), pro_bar, lw=0.5, width=width, color='#0578A7')

    if legend:
        # leg = plt.legend(labels=[team, "JUSHOOP平均", "NBA平均"], fontsize=40, loc=1, bbox_to_anchor=(1.01,1.4),borderaxespad = 0.)
        # title = "JUSHOOP平均"
        title = avg_title
        leg = plt.legend(labels=[team, title], fontsize=40, loc=1, bbox_to_anchor=(0.98, 1.4),
                         borderaxespad=0.)
        for text in leg.get_texts():  # 获取图例中的文本对象
            text.set_color('black')

    bns_data = [(f"{round(bns_data[i], 1)}%" if (i in percentage_idxes) else bns_data[i]) for i in range(len(bns_data))]
    pro_data = [(f"{round(pro_data[i], 1)}%" if (i in percentage_idxes) else pro_data[i]) for i in range(len(pro_data))]
    avg_data = [(f"{round(avg_data[i], 1)}%" if (i in percentage_idxes) else avg_data[i]) for i in range(len(avg_data))]

    plt.hlines(80, -0.65, 4.3, ls="--", color="white", linewidth=2)
    if legend:
        plt.text(3.8, 82, "nba水平参考线", ha='left', va='bottom', color="white", fontdict={'size': 22})

    # # 为横向水平的柱图右侧添加数据标签。
    for i, rect in enumerate(c):
        ax.text(rect.get_x() + width / 2, rect.get_height(), f'{bns_data[i]}', ha='center', va='bottom', color=txt_colors[i], fontdict=num_font)
        # ax.text(rect.get_x() + width/2*3, 25, f'{terms[i]}', ha='center', va='bottom', color="white", fontsize=15)
    for i, rect in enumerate(a):
        ax.text(rect.get_x() + width / 2, rect.get_height(), f'{avg_data[i]}', ha='center', va='bottom', color="white", fontdict=num_font)
        # ax.text(rect.get_x() + width / 2, 10, f'{terms[i]}', ha='center', va='bottom', color="white", fontsize=40) # with NBA
        ax.text(rect.get_x(), 10, f'{terms[i]}', ha='center', va='bottom', color="white",
                fontsize=36)  # with NBA

    # for i, rect in enumerate(b):
    #     ax.text(rect.get_x() + width / 2, rect.get_height(), f'{pro_data[i]}', ha='center', va='bottom', color="white", fontsize=30)


    plt.xticks(range(len(terms)), terms, size=40)
    ax = fig.gca()
    ax.spines['bottom'].set_color('white')
    ax.spines['left'].set_color('white')
    ax.spines['top'].set_color('white')
    ax.spines['right'].set_color('white')

    plt.tick_params(axis='x', colors='white')
    plt.tick_params(axis='y', colors='white')
    plt.axis('off')


def get_boston_fig(team, data, x_term, y_term, size_term, quadrants, resource_dir, x_precentage=False, y_precentage=False, x_inverse=False, y_inverse=False, size_factor=400):
    gap_rate = 0.05

    names = data.index
    if x_precentage:
        data[x_term] = data[x_term] * 100
    if y_precentage:
        data[y_term] = data[y_term] * 100
    min_x, max_x = min(data[x_term]), max(data[x_term])
    min_y, max_y = min(data[y_term]), max(data[y_term])
    x_gap = (max_x - min_x) * gap_rate
    y_gap = (max_y - min_y) * gap_rate


    fig, ax = plt.subplots(figsize=(10, 10), dpi=200)
    # print(data[size_term])

    size_func = lambda x: max(10, int(np.sqrt(x * size_factor)+1))
    # print(names)
    for i in range(data.shape[0]):
        # print(team, names[i], data[size_term][i], size_func(data[size_term][i]))
        ab = AnnotationBbox(getImage(team, names[i], size_func(data[size_term][i]), resource_dir), (data[x_term][i], data[y_term][i]), frameon=False)
        ax.add_artist(ab)

    for x, y, name, i in zip(data[x_term], data[y_term], names, range(len(names))):
        plt.text(x, y - (-2 * (y_inverse - 0.5)) * size_func(data[size_term][i]) / 200 * (max_y - min_y) / 6, name, ha='center', va='center', fontsize=12, color="white")


    x_left_most = min_x - x_gap
    x_right_most = max_x + x_gap
    # x_middle = np.mean(data[x_term])
    x_middle = (min_x + max_x) / 2


    text_left = (x_left_most + x_middle) / 2
    text_right = (x_middle + x_right_most) / 2
    text_top = max_y - (max_y - min_y) * (1 + 2 * gap_rate) / 20
    text_bottom = min_y + (max_y - min_y) * (1 + 2 * gap_rate) / 20

    # print(x_left_most, x_right_most, x_middle_left+1)
    # print(text_left)

    quadrant_color = "#ABC3C5"
    alpha=0.6

    plt.text(text_left, text_top,
             quadrants[0],
             ha='center',
             va='center',
             fontsize=40,
             color=quadrant_color,
             alpha=alpha)

    plt.text(text_left, text_bottom,
             quadrants[1],
             ha='center',
             va='center',
             fontsize=40,
             color=quadrant_color,
             alpha=alpha)

    plt.text(text_right, text_top,
             quadrants[2],
             ha='center',
             va='center',
             fontsize=40,
             color=quadrant_color,
             alpha=alpha)

    plt.text(text_right, text_bottom,
             quadrants[3],
             ha='center',
             va='center',
             fontsize=40,
             color=quadrant_color,
             alpha=alpha)
    ax = fig.gca()
    ax.spines['bottom'].set_color('white')
    ax.spines['left'].set_color('white')
    ax.spines['top'].set_color('white')
    ax.spines['right'].set_color('white')

    plt.tick_params(axis='x', colors='white')
    plt.tick_params(axis='y', colors='white')
    # print(min_x, min_y, max_x, max_y)

    # 绘制坐标
    plt.xlim(xmin=min_x - x_gap, xmax=max_x + x_gap)
    plt.ylim(ymin=min_y - y_gap, ymax=max_y + y_gap)
    if x_inverse:
        ax.invert_xaxis()
    if y_inverse:
        ax.invert_yaxis()
    # 绘制分割线
    # plt.axhline(y=np.mean(data[y_term]), ls="-", color="white", linewidth=2)
    # plt.axvline(x=np.mean(data[x_term]), ls="-", color="white", linewidth=2)
    plt.axhline(y=(min_y + max_y)/2, ls="-", color="white", linewidth=2)
    plt.axvline(x=(min_x + max_x)/2, ls="-", color="white", linewidth=2)


    return min_x, min_y, max_x, max_y




def get_boston(team, resource_dir="."):
    target_paths = []
    """
       球员得分能力
    """
    data = get_data_df(resource_dir, f'{team}_score.csv')
    get_boston_fig(team, data, "出手次数", "真实命中", "得分", ["合理球员", "进攻混子", "进攻核心", "打铁匠"], resource_dir, size_factor=250, y_precentage=True)
    # 绘制X，Y轴标签
    plt.xlabel("低<————— 出手次数 —————>高", fontsize=17, color="white")
    plt.ylabel("低<—————— 真实命中率(%) ——————>高", fontsize=17, color="white")

    target_path = get_output_path(resource_dir, team, 'scores.png')
    plt.savefig(target_path, transparent=True, bbox_inches='tight')
    target_paths.append(target_path)

    """
       球员团队能力
    """
    data = get_data_df(resource_dir, f'{team}_team_spirit.csv')
    get_boston_fig(team, data, "进攻效率", "防守效率", "出场时间", ["内鬼", "防守领袖", "进攻狂魔", "攻防一体"], resource_dir, size_factor=50, y_inverse=True)
    # 绘制X，Y轴标签
    plt.xlabel("低<————— 进攻效率 —————>高", fontsize=17, color="white")
    plt.ylabel("低<—————— 防守效率 ——————>高", fontsize=17, color="white")

    target_path = get_output_path(resource_dir, team, f'team_spirit.png')
    plt.savefig(target_path, transparent=True, bbox_inches='tight')
    target_paths.append(target_path)


    """
        球员出手选择
    """
    data = get_data_df(resource_dir, f'{team}_offense_options.csv')

    get_boston_fig(team, data, "三分占比", "受助攻率", "真实命中", ["饼皇", "单打杀器", "三分炮台", "民间库里"], resource_dir, size_factor=5000, x_precentage=True, y_precentage=True )
    # 绘制X，Y轴标签
    plt.xlabel("低<————— 三分得分占比 —————>高", fontsize=17, color="white")
    plt.ylabel("低<—————— 受助攻率 ——————>高", fontsize=17, color="white")

    target_path = get_output_path(resource_dir, team, 'options.png')
    plt.savefig(target_path, transparent=True, bbox_inches='tight')
    target_paths.append(target_path)

    """
        球员篮板水平
    """
    data = get_data_df(resource_dir, f'{team}_rebound_feat.csv')

    get_boston_fig(team, data, "在场篮板率", "每分钟篮板数", "场均篮板", ["威少", "篮板绝缘体", "板皇", "亚当斯"], resource_dir, size_factor=300, x_precentage=True)
    # 绘制X，Y轴标签
    plt.xlabel("低<————— 在场球队篮板率 —————>高", fontsize=17, color="white")
    plt.ylabel("低<—————— 每分钟篮板数 ——————>高", fontsize=17, color="white")

    target_path = get_output_path(resource_dir, team, 'rebounds.png')
    plt.savefig(target_path, transparent=True, bbox_inches='tight')
    target_paths.append(target_path)

    return target_paths



def get_pro_fig(team, resource_dir="."):
    fig = plt.figure(figsize=(25, 20))
    get_pro_subfig(team, fig, 0, 5, resource_dir, percentage_idxes=[0,1,2,3,4], legend=True, idx=1)

    get_pro_subfig(team, fig, 5, 10, resource_dir, percentage_idxes=[0,1,2], reverse_idxes=[3], idx=2)
    
    target_path = get_output_path(resource_dir, team, 'pro.png')
    plt.savefig(target_path, transparent=True, bbox_inches='tight')
    return target_path
    # get_pro_subfig(team, 5, 8)
    # plt.savefig(f'{team}_pro_3.png', transparent=True, bbox_inches='tight')
    # get_pro_subfig(team, 8, 10)
    # plt.savefig(f'{team}_pro_4.png', transparent=True, bbox_inches='tight')


def get_best_player(data, term):
    names = data.index
    max_value = np.max(data[term])
    name = names[list(data[term]).index(max_value)]
    return name, max_value


def draw_stats(team, width, height, titles, names, values):
    fontdict = {
        "fontsize": 18,  # 字体大小
        "color": "white",  # 字体颜色
        "fontweight": "bold",  # 字体线条粗细，可选参数 :{"light": ,"normal":,"medium":,"semibold":,"bold":,"heavy":,"black"}
        "verticalalignment": "center",  # 设置水平对齐方式 ，可选参数 ：center、top、bottom、baseline
        "horizontalalignment": "center",  # 设置垂直对齐方式，可选参数：left、right、center
        "rotation": 0,  # 旋转角度，可选参数为:vertical,horizontal 也可以为数字
        "alpha": 1,  # 透明度，参数值0至1之间
    }
    line_len = width / 2 * 0.9
    left_start = width / 2 / 20
    left_end = left_start + line_len
    right_start = width / 2 + width / 2 / 20
    right_end = right_start + line_len

    height_gap = height/10
    height_start = height/2.5
    heights = [height_start, height_start + height_gap, height_start + height_gap * 2, height_start + height_gap * 3]
    for height in heights:
        plt.hlines(height, left_start, left_end, ls="-", color="white", linewidth=2)
        plt.hlines(height, right_start, right_end, ls="-", color="white", linewidth=2)

    fontdict = {
        "fontsize": 12,  # 字体大小
        "color": "white",  # 字体颜色
        "fontweight": "bold",  # 字体线条粗细，可选参数 :{"light": ,"normal":,"medium":,"semibold":,"bold":,"heavy":,"black"}
        "verticalalignment": "center",  # 设置水平对齐方式 ，可选参数 ：center、top、bottom、baseline
        "horizontalalignment": "left",  # 设置垂直对齐方式，可选参数：left、right、center
        "rotation": 0,  # 旋转角度，可选参数为:vertical,horizontal 也可以为数字
        "alpha": 1,  # 透明度，参数值0至1之间
    }
    fontdict_num = {
        "fontsize": 10,  # 字体大小
        "color": "white",  # 字体颜色
        "fontweight": "bold",  # 字体线条粗细，可选参数 :{"light": ,"normal":,"medium":,"semibold":,"bold":,"heavy":,"black"}
        "verticalalignment": "center",  # 设置水平对齐方式 ，可选参数 ：center、top、bottom、baseline
        "horizontalalignment": "right",  # 设置垂直对齐方式，可选参数：left、right、center
        "rotation": 0,  # 旋转角度，可选参数为:vertical,horizontal 也可以为数字
        "alpha": 1,  # 透明度，参数值0至1之间
        # 设置外边框
        "bbox": {
            "boxstyle": "square",
            # 边框类型，参考：https://vimsky.com/examples/usage/python-matplotlib.patches.BoxStyle-mp.html
            "facecolor": "#EC4B08",  # 背景颜色，好像与上述 backgroundcolor 有冲突
            "alpha": 1,
            "edgecolor": "#EC4B08",
            "pad": 0.1,
        },
    }
    fontdict_name = {
        "fontsize": 14,  # 字体大小
        "color": "white",  # 字体颜色
        "fontweight": "bold",  # 字体线条粗细，可选参数 :{"light": ,"normal":,"medium":,"semibold":,"bold":,"heavy":,"black"}
        "verticalalignment": "center",  # 设置水平对齐方式 ，可选参数 ：center、top、bottom、baseline
        "horizontalalignment": "center",  # 设置垂直对齐方式，可选参数：left、right、center
        "rotation": 0,  # 旋转角度，可选参数为:vertical,horizontal 也可以为数字
        "alpha": 1,  # 透明度，参数值0至1之间
        # 设置外边框
        # "bbox": {
        #     "boxstyle": "square",
        #     # 边框类型，参考：https://vimsky.com/examples/usage/python-matplotlib.patches.BoxStyle-mp.html
        #     "facecolor": "#CF4302",  # 背景颜色，好像与上述 backgroundcolor 有冲突
        #     "alpha": 1,
        #     "edgecolor": "#CF4302",
        # },
    }

    for i in range(len(titles)):
        plt.text((left_start if i < 4 else right_start) + line_len / 30, heights[i % 4] - height * 0.05, f"{titles[i]}", fontdict=fontdict)
        plt.text((left_start if i < 4 else right_start) + line_len / 30 * 29, heights[i % 4] - height * 0.05, f"{values[i]}",
                 fontdict=fontdict_num)
        plt.text((left_start if i < 4 else right_start) + line_len / 2, heights[i % 4] - height * 0.05, f"{names[i]}",
                 fontdict=fontdict_name)


def plot_table_basic(team, resource_dir="."):
    plt.rcParams['font.family'] = ['Arial Unicode MS']  # 用黑体显示中文

    row_colors = {
        "even": "#D37027",
        "odd": "#D67C39",
    }

    bg_color = row_colors["odd"]

    data = get_data_df(resource_dir, f'{team}_player_basic_stat.csv')

    print(len(data))
    fig, ax = plt.subplots(figsize=(15, len(data)//3), dpi=80)


    # fig, ax = plt.subplots()

    fig.set_facecolor(bg_color)
    ax.set_facecolor(bg_color)

    cmap = LinearSegmentedColormap.from_list(
        name="bugw", colors=["#FF0000", "#e0e8df", "#00EE76"], N=256
    )
    cmap_r = LinearSegmentedColormap.from_list(
        name="bugw", colors=["#00EE76", "#e0e8df", "#FF0000"], N=256
    )

    table_cols = ["得分", "篮板", "助攻", "抢断", "盖帽", "2分", "3分", "罚球", "2分命中", "3分命中", "罚球命中",
                  "后+前场篮板", "失误", "出场次数", "上场时间"]
    team_title = team
    table_col_defs = [
        ColDef("姓名", width=1.3, textprops={"ha": "left", "weight": "bold"}, title="姓名"),
        ColDef("得分", width=0.5),
        ColDef("助攻", width=0.5),
        ColDef("篮板", width=0.5),
        ColDef("抢断", width=0.5),
        ColDef("盖帽", width=0.5),
        ColDef("2分", width=0.8),
        ColDef("3分", width=0.8),
        ColDef("罚球", width=0.8),
        ColDef("2分命中", width=0.8, formatter=decimal_to_percent),
        ColDef("3分命中", width=0.8, formatter=decimal_to_percent),
        ColDef("罚球命中", width=0.8, formatter=decimal_to_percent),
        ColDef("后+前场篮板", width=0.95, title="后板+前板"),
        ColDef("失误", width=0.5),
        ColDef("出场次数", title="场次", width=0.6),
        ColDef("上场时间", width=0.5),
    ]

    tab = Table(data,
                ax=ax,
                column_definitions=table_col_defs,
                row_dividers=True,
                col_label_divider=False,
                footer_divider=True,
                columns=table_cols,
                even_row_color=row_colors["even"],
                footer_divider_kw={"color": bg_color, "lw": 2},
                row_divider_kw={"color": bg_color, "lw": 2},
                column_border_kw={"color": bg_color, "lw": 2},
                # 如果设置字体需要添加"fontname": "Roboto"
                textprops={"fontsize": 15, "ha": "center", "color": "black"}, )

    JUSHOOP_title_txt = f"{team} 球员基础数据统计"

    plt.title(label="{}\n{}".format(JUSHOOP_title_txt, "_" * 110),
              fontsize=25,
              fontweight="bold",
              color="black",
              y=1)

    matplotlib.pyplot.subplots_adjust(left=0.02, bottom=0.001, right=0.982, top=0.893)

    target_path = get_output_path(resource_dir, team, "basic_stats.pdf")
    plt.savefig(target_path, dpi=300)
    return target_path

def plot_table_advanced(team, resource_dir="."):
    plt.rcParams['font.family'] = ['Arial Unicode MS']  # 用黑体显示中文

    row_colors = {
        "even": "#D37027",
        "odd": "#D67C39",
    }

    bg_color = row_colors["odd"]

    data = get_data_df(resource_dir, f'{team}_player_advanced_stat.csv')

    fig, ax = plt.subplots(figsize=(15, len(data)//3), dpi=80)


    # fig, ax = plt.subplots()

    fig.set_facecolor(bg_color)
    ax.set_facecolor(bg_color)

    cmap = LinearSegmentedColormap.from_list(
        name="bugw", colors=["#FF0000", "#e0e8df", "#00EE76"], N=256
    )
    cmap_r = LinearSegmentedColormap.from_list(
        name="bugw", colors=["#00EE76", "#e0e8df", "#FF0000"], N=256
    )

    table_cols = ["效率值", "真实命中","回合占有率","受助攻率","助攻失误比","在场篮板率","进攻效率","防守效率","出场次数"]
    team_title = team
    table_col_defs = [
        ColDef("姓名", width=1.3, textprops={"ha": "left", "weight": "bold"}, title="姓名"),
        ColDef("效率值", width=0.6),
        ColDef("真实命中", width=0.6, formatter=decimal_to_percent),
        ColDef("回合占有率", width=0.6, formatter=decimal_to_percent),
        ColDef("受助攻率", width=0.6, formatter=decimal_to_percent),
        ColDef("助攻失误比", width=0.6),
        ColDef("在场篮板率", width=0.6, formatter=decimal_to_percent),
        ColDef("进攻效率", width=0.6),
        ColDef("防守效率", width=0.6),
        ColDef("出场次数", title="场次", width=0.6),
    ]

    tab = Table(data,
                ax=ax,
                column_definitions=table_col_defs,
                row_dividers=True,
                col_label_divider=False,
                footer_divider=True,
                columns=table_cols,
                even_row_color=row_colors["even"],
                footer_divider_kw={"color": bg_color, "lw": 2},
                row_divider_kw={"color": bg_color, "lw": 2},
                column_border_kw={"color": bg_color, "lw": 2},
                textprops={"fontsize": 15, "ha": "center", "color": "black"}, )

    JUSHOOP_title_txt = f"{team} 球员进阶数据统计"

    plt.title(label="{}\n{}".format(JUSHOOP_title_txt, "_" * 110),
              fontsize=25,
              fontweight="bold",
              color="black",
              y=1)

    matplotlib.pyplot.subplots_adjust(left=0.02, bottom=0.001, right=0.982, top=0.893)

    target_path = get_output_path(resource_dir, team, "advanced_stats.pdf")
    plt.savefig(target_path, dpi=300)
    return target_path


def get_player_leader(team, resource_dir="."):
    data = get_data_df(resource_dir, f'{team}_player_basic_stat.csv')

    try:
        ima = get_img(resource_dir, team, "background")
    except:
        # print("background not found")
        raise FileNotFoundError(f"background not found {team}")
        # ima = Image.open(f"background_JUSHOOP.jpg").convert("RGBA")
    ima = ima.filter(ImageFilter.BoxBlur(5))
    bright_enhancer = ImageEnhance.Brightness(ima)
    ima = bright_enhancer.enhance(0.4)
    width, height = ima.size
    fig = plt.figure(dpi=200)
    plt.imshow(ima)
    fig.set_size_inches(width / 200, height / 200)
    fig.canvas.manager.full_screen_toggle()
    plt.axis('off')
    terms = ["得分", "篮板", "助攻", "抢断", "盖帽", "3分命中", "失误", "效率值"]
    names = []
    values = []

    for term in terms:
        name, value = get_best_player(data, term)
        names.append(name)
        if term[-2:] == "命中":
            value = f"{round(value*100, 1)}%"
        values.append(value)
    fontdict = {
        "fontsize": 18,  # 字体大小
        "color": "white",  # 字体颜色
        "fontweight": "bold",  # 字体线条粗细，可选参数 :{"light": ,"normal":,"medium":,"semibold":,"bold":,"heavy":,"black"}
        "verticalalignment": "center",  # 设置水平对齐方式 ，可选参数 ：center、top、bottom、baseline
        "horizontalalignment": "center",  # 设置垂直对齐方式，可选参数：left、right、center
        "rotation": 0,  # 旋转角度，可选参数为:vertical,horizontal 也可以为数字
        "alpha": 1,  # 透明度，参数值0至1之间
    }
    plt.text(width / 2, height / 10, f"{team} STATS LEADERS", fontdict=fontdict)
    draw_stats(team, width, height, terms, names, values)

        
    target_path = get_output_path(resource_dir, team, "leaders.png")
    plt.savefig(target_path, transparent=True, bbox_inches='tight')
    return target_path

def get_best_player_poster(team, resource_dir="."):
    def get_rank(name, term, data):
        values = data[term]
        value = values[name]
        rank = sorted(list(values), reverse=True).index(value) + 1
        if str(rank)[-1] == "1":
            rank = f"{rank}st"
        elif str(rank)[-1] == "2":
            rank = f"{rank}nd"
        elif str(rank)[-1] == "3":
            rank = f"{rank}rd"
        else:
            rank = f"{rank}th"
        return value, rank

    data = get_data_df(resource_dir, f'{team}_player_basic_stat.csv')

    try:

        # ima = Image.open(f"background_{team}.jpg").convert("RGBA")
        ima = get_img(resource_dir, team, "MVP")
    except:
        # print("background not found")
        raise FileNotFoundError(f"background not found {team}")
        # ima = Image.open(f"background_JUSHOOP.jpg").convert("RGBA")
    ima = ima.filter(ImageFilter.BoxBlur(5))
    bright_enhancer = ImageEnhance.Brightness(ima)
    ima = bright_enhancer.enhance(0.6)
    width, height = ima.size
    fig = plt.figure(dpi=200)
    plt.imshow(ima)
    fig.set_size_inches(width / 200, height / 200)
    fig.canvas.manager.full_screen_toggle()
    plt.axis('off')
    terms = ["得分", "篮板", "助攻", "抢断", "盖帽", "2分命中", "3分命中", "效率值"]
    values = []
    ranks = []

    best_name, value = get_best_player(data, "效率值")

    for term in terms:
        value, rank = get_rank(best_name, term, data)
        ranks.append(rank)
        if term[-2:] == "命中":
            value = f"{round(value*100, 1)}%"
        values.append(value)
    fontdict = {
        "fontsize": 18,  # 字体大小
        "color": "white",  # 字体颜色
        "fontweight": "bold",  # 字体线条粗细，可选参数 :{"light": ,"normal":,"medium":,"semibold":,"bold":,"heavy":,"black"}
        "verticalalignment": "center",  # 设置水平对齐方式 ，可选参数 ：center、top、bottom、baseline
        "horizontalalignment": "center",  # 设置垂直对齐方式，可选参数：left、right、center
        "rotation": 0,  # 旋转角度，可选参数为:vertical,horizontal 也可以为数字
        "alpha": 1,  # 透明度，参数值0至1之间
    }
    plt.text(width / 2, height / 10, f"最佳球员 {best_name}", fontdict=fontdict)
    draw_stats(team, width, height, terms, values, ranks)

    target_path = get_output_path(resource_dir, team, "best.png")
    plt.savefig(target_path, transparent=True, bbox_inches='tight')
    return target_path

report_page_funcs = [get_oppo_fig, get_pro_fig, get_boston, plot_table_basic,
                      plot_table_advanced, get_player_leader, get_best_player_poster]
report_page_imgs = [ "__JUSHOOP_OPPO_PATH__", "__JUSHOOP_PRO_PATH__",
                     ["__JUSHOOP_SCORES_PATH__", "__JUSHOOP_TEAM_SPRIT_PATH__", 
                     "__JUSHOOP_OPTION_PATH__", "__JUSHOOP_REBOUNDS_PATH__"], 
                     "__JUSHOOP_BASIC_STATS_PATH__", "__JUSHOOP_ADVANCED_STATS_PATH__", 
                     "__JUSHOOP_LEADERS_PATH__", "__JUSHOOP_BEST_PATH__",]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run Example')
    parser.add_argument('target_team', type=str, help='path of config file')
    args = parser.parse_args()
    teams = ["JUSHOOP", "TOPGUN", "SONIC", "光耀", "BNS"]
    target_teams = teams if args.target_team == "ALL" else [args.target_team]

    for target_team in target_teams:
        func_lists = [get_oppo_fig, get_pro_fig, get_boston, get_player_leader, plot_table_basic,
                      plot_table_advanced, get_best_player_poster]
        process_list = []
        for i in range(7):
            p = Process(target=func_lists[i], args=(target_team,))  # 实例化进程对象
            p.start()
            process_list.append(p)

        for i in process_list:
            p.join()

        print(f'{target_team}结束')

# get_oppo_fig(target_team)
# get_pro_fig(target_team)
# get_boston(target_team)
# get_player_leader(target_team)
# plot_table_basic(target_team)
# plot_table_advanced(target_team)
# get_best_player_poster(target_team)

# def write_latex():
#     Latex_file = open('text.tex', 'w+')
#     Latex_file.write(
#         '\\documentclass{article}\n'
#         '\\usepackage{graphicx}\n'
#         '\\usepackage{caption, subcaption}\n'
#         '\\usepackage[parfill]{parskip}\n'
#         '\\usepackage[version=4]{mhchem}\n'
#         '\\usepackage{geometry}\n'
#         '\\geometry{ paper=a4paper, top=3cm, bottom=3cm, left=2.5cm, right=2.5cm, headheight=20pt, footskip=1.5cm, headsep=1.2cm}\n'
#         '\\begin{document}\n'
#         f'\\centering\\section*{{Exp$\\_$ID: 01/30 $\\_$1}}\n'
#         '\\begin{figure}[htb]\n'
#         f'\\includegraphics[width=\\linewidth]{{Figure_1.png}}\n'
#         '\\caption{Amplification Curve} \\label{fig:1}\n'
#         '\\end{figure}\n'
#         '\\section*{Notes:} \n'
#         f'This experiment tested 1 assays targeting 1.\n'
#         '\n'
#         'Write Discussion Here...\n'
#         '\\section*{Further experiment/Trouble shooting}\n'
#         '$\\bullet$ Write comments here\n'
#         '\\end{document}\n'
#
#     )
#
# write_latex()
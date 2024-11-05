import numpy as np
from plottable.cmap import normed_cmap
from matplotlib.colors import LinearSegmentedColormap
from plottable import Table, ColDef
from plottable.table import create_cell, ColumnType, Row
import matplotlib
import matplotlib.pyplot as plt
import os
import pandas as pd
from typing import Callable
from typing import Any, Callable, Dict, List, Tuple
from numbers import Number
import argparse
import json
import matplotlib.font_manager as font_manager
import matplotlib.gridspec as gridspec

from datetime import datetime
import platform


FONT = 'LogoSC Unbounded Sans'

fonts = font_manager.fontManager.ttflist

# 获取字体名称及其路径
font_info = [(font.name, font.fname) for font in fonts]

MY_TITLE_TEXT_PRORPS = {"fontsize": 26, "ha": "center", "weight": "bold", "color": "#d48401", "family": "LogoSC Unbounded Sans"}

ROW_HEIGHT = 0.8

class myTable(Table):

    def _init_rows(self):
        """Initializes the Tables Rows."""
        self.rows = {}
        num_lines = len(self.df.to_records())
        label_y = -1 - (-num_lines // 2) * (1 - ROW_HEIGHT)
        self.col_label_row = self._get_col_label_row(label_y, self._get_column_titles())
        for idx, values in enumerate(self.df.to_records()):
            self.rows[idx] = self._get_row(idx, values, num_lines)

        

    def _get_col_label_row(self, idx: int, content: List[str | Number]) -> Row:
        """Creates the Column Label Row.

        Args:
            idx (int): index of the Row
            content (List[str  |  Number]): content that is plotted as text.

        Returns:
            Row: Column Label Row
        """
        widths = self._get_column_widths()

        if "height" in self.col_label_cell_kw:
            height = self.col_label_cell_kw["height"]
        else:
            height = 1

        x = 0

        row = Row(cells=[], index=idx)

        for col_idx, (colname, width, _content) in enumerate(
            zip(self.column_names, widths, content)
        ):
            col_def = self.column_definitions[colname]
            textprops = MY_TITLE_TEXT_PRORPS

            # don't apply bbox around text in header
            if "bbox" in textprops:
                textprops.pop("bbox")

            cell = create_cell(
                column_type=ColumnType.STRING,
                xy=(
                    x,
                    idx + 1 - height,
                ),  # if height is different from 1 we need to adjust y
                content=_content,
                row_idx=idx,
                col_idx=col_idx,
                width=width,
                height=height,
                rect_kw=self.col_label_cell_kw,
                textprops=textprops,
                ax=self.ax,
            )

            row.append(cell)
            cell.draw()

            x += width

        return row
    
    def _get_row(self, idx: int, content: List[str | Number], num_lines=0) -> Row:
        widths = self._get_column_widths()

        x = 0

        row = Row(cells=[], index=idx)
        middle = num_lines // 2
        idx -= (idx - middle) * (1 - ROW_HEIGHT)

        for col_idx, (colname, width, _content) in enumerate(
            zip(self.column_names, widths, content)
        ):
            col_def = self.column_definitions[colname]


            if "plot_fn" in col_def:
                plot_fn = col_def.get("plot_fn")
                plot_kw = col_def.get("plot_kw", {})

                cell = create_cell(
                    column_type=ColumnType.SUBPLOT,
                    xy=(x, idx),
                    content=_content,
                    plot_fn=plot_fn,
                    plot_kw=plot_kw,
                    row_idx=idx,
                    col_idx=col_idx,
                    width=width,
                    height=ROW_HEIGHT,
                    rect_kw=self.cell_kw,
                    ax=self.ax,
                )

            else:
                textprops = self._get_column_textprops(col_def)

                cell = create_cell(
                    column_type=ColumnType.STRING,
                    xy=(x, idx),
                    content=_content,
                    row_idx=idx,
                    col_idx=col_idx,
                    width=width,
                    height=ROW_HEIGHT,
                    rect_kw=self.cell_kw,
                    textprops=textprops,
                    ax=self.ax,
                )

            row.append(cell)
            self.columns[colname].append(cell)
            self.cells[(idx, col_idx)] = cell
            cell.draw()

            x += width

        return row


def my_normed_cmap(
    s: pd.Series, cmap: matplotlib.colors.LinearSegmentedColormap, num_stds: float = 2.5
) -> Callable:
    
    vmin, vmax = -15, 15

    norm = matplotlib.colors.Normalize(vmin=vmin, vmax=vmax)
    
    m = myScalarMappable(norm=norm, cmap=cmap)


    return m.to_rgba

class myScalarMappable(matplotlib.cm.ScalarMappable):
    def to_rgba(self, x, alpha=None, bytes=False, norm=True):
        x = np.ma.asarray(x)
        if norm:
            x = self.norm(x)
        rgba = self.cmap(x, alpha=alpha, bytes=bytes)
        return rgba


# # 输出所有可用字体名称及其路径
# print("可用字体及其路径:")
# for font_name, font_path in sorted(font_info):
#     if not "/Users/Markos/Library/" in font_path:
#         continue
#     print(f"{font_name}: {font_path}")


system = platform.system()
if system == "Windows":
    font_type = 'microsoft YaHei'
    font_manager.fontManager.addfont("C:/Users/39727/AppData/Local/Microsoft/Windows/Fonts/LogoSCUnboundedSans-Regular-2.ttf")
elif system == "Darwin":
    font_type = "Microsoft YaHei"
    font_manager.fontManager.addfont("/Users/Markos/Library/Fonts/LogoSCUnboundedSans-Regular-2.ttf")
    font_manager.fontManager.addfont("/Users/Markos/Library/Fonts/微软雅黑粗体.ttf")
matplotlib.rc("font", family=font_type)
plt.rcParams['font.family'] = [font_type]


terms = {
    "name": "姓名",
    "time": "上场时间",
    "scores": "得分",
    "assists": "助攻",
    "rebounds": "篮板",
    "steals": "抢断",
    "blocks": "盖帽",
    "2pts": "2分",
    "3pts": "3分",
    "fts": "罚球",
    "od_rebounds": "后场+前场篮板",
    "def_rebounds": "后场篮板",
    "off_rebounds": "前场篮板",
    "fouls": "犯规",
    "tos": "失误",
    "make_fouls": "造成犯规",
    "EFF": "效率值",
    "oncourt_per_scores": "在场得分(10回合)",
    "oncourt_per_loses": "在场失分(10回合)",
    "oncourt_scores": "在场得分",
    "oncourt_loses": "在场失分",
    "rounds": "回合数",
    "TS": "真实命中率",
    "USG": "球权使用率",
    "plus_minus": "正负值",
    "oncourt_off_rounds": "在场进攻回合数", 
    "oncourt_def_rounds": "在场防守回合数",
    "oncourt_team_rebounds": "在场篮板数",
    "oncourt_opponent_rebounds": "在场对方篮板数",
    "used_rounds": "回合占有数",
    "games_played": "场次",
    "games_wined": "胜场",
    "blocked": "被盖",
    "atpts": "出手",
    "fts_atpts": "罚球出手",
    "2pts_atpts": "2分球出手", 
    "3pts_atpts": "3分球出手", 
    "mades": "命中",
    "fts_mades": "罚球命中", 
    "2pts_mades": "2分球命中", 
    "3pts_mades": "3分球命中"
}

terms_en = {
    "姓名": "Name",
    "上场时间": "MIN",
    "得分": "PTS",
    "助攻": "AST",
    "篮板": "REB",
    "抢断": "STL",
    "盖帽": "BLK",
    "2分": "2FG",
    "3分": "3FG",
    "罚球": "FT",
    "后场+前场篮板": "DREB+OREB",
    "前场篮板": "OREB",
    "后场篮板": "DREB",
    "犯规": "PF",
    "失误": "TO",
    "造成犯规": "PFD",
    "效率值": "EFF",
    "在场得分(10回合)": "ORtg(10 rounds)",
    "在场失分(10回合)": "DRtg(10 rounds)",
    "真实命中率": "TS%",
    "球权使用率": "USG%",
    "出手": "FGA",
    "罚球出手": "FTA",
    "正负值": "+/-"
}


def linear_map(x, a=0.5, b=0.8, c=0.5, d=0.6):

    return c + (x - a) * (d - c) / (b - a)


def df_filter(data_df, Event=None, Team=None, Player=None, Object=None, Info=None):
    result_df = data_df
    if Event is not None:
        result_df = result_df[result_df.Event == Event]
    if Team is not None:
        result_df = result_df[result_df.Team == Team]
    if Player is not None:
        result_df = result_df[result_df.Player == Player]
    if Object is not None:
        result_df = result_df[result_df.Object == Object]
    if Info is not None:
        result_df = result_df[result_df.Info == Info]

    return result_df

# 需要等所有基础数据都出来之后才能计算的数据
high_level_stats = ["EFF", "USG", "oncourt_per_scores", "oncourt_per_loses", "plus_minus", "games_wined"]


def append(df, row_dict):
    return pd.concat([df, pd.DataFrame([row_dict])], ignore_index=True)

def parse_shoots(shoots):
    shoots = shoots.split("/")
    return int(shoots[1]) - int(shoots[0])

def decimal_to_percent(val: float) -> str:
    if abs(val - 0) < 0.0001:
        return "/"
    elif abs(val - 1) < 0.0001:
        return "100%"
    else:
        return f"{str(round(val * 100))}%"


class BaseStatsModel():
    # True: 检测：助攻必须来自同队、抢断盖帽犯规必须来自其他队
    check_event_team = True
    terms = terms
    terms_en = terms_en
    get_team_stats = False
    def __init__(self, event_data, config):
        self.event_data = event_data
        self.config = config
        self.quarters = self.config["quarters"]
        # self.target_stats = self.config["stats"]
        self.quarter_time = self.config["quarter_time"]
        self.match_date = datetime.strptime(self.config["match_name"].split("_")[0], '%Y%m%d').strftime('%m月%d日')
        try:
            self.court_name = self.config["court"]
        except:
            self.court_name = ""
        try:
            self.match_time = self.config["match_time"]
        except:
            self.match_time = None
        try:
            self.use_en = self.config["english"]
        except:
            self.use_en = False
        try:
            self.user_table_cols = self.config["target_stats"]
        except:
            self.user_table_cols = None

        self.preprocess()
        self.player_stats = None
        self.scores = None

    def check_switch_people(self):
        """友谊赛模型中需要重载该函数检查换人逻辑"""
        return

    def get_team_names(self):
        self.team_names = []
        i = 0
        while len(self.team_names) < self.max_teams:
            name = self.event_data.iloc[i]["Team"]
            if not (name in self.team_names) and (name != ""):
                self.team_names.append(name)
            i += 1

        self.num_teams = len(self.team_names)


    def preprocess(self):
        # get team names
        self.get_team_names()

        # get player names
        self.player_names = [[] for i in self.team_names]
        event_data_switch = self.event_data[self.event_data.Event == "换人"]
        for i, r in event_data_switch.iterrows():
            # print(r)
            team_idx = self.team_names.index(r["Team"])
            if not r["Object"] in self.player_names[team_idx]:
                self.player_names[team_idx].append(r["Object"])
        # get actual match time for each quarter
        self.actual_quarter_times = [0 for i in range(self.quarters)]
        for i, r in self.event_data.iterrows():
            t = r["Time"].split(" - ")
            t_ = t[1].split(" : ")
            q, m, s = int(t[0]), int(t_[0]), int(t_[1])
            time = m * 60 + s
            self.actual_quarter_times[q - 1] = max(self.actual_quarter_times[q - 1], time + 1)

        # get start time for each quarter
        self.quarter_start_times = [0 for i in range(self.quarters)]
        for i, r in self.event_data[self.event_data.Event == "计时开始"].iterrows():
            # print(r)
            self.quarter_start_times[int(r["Object"]) - 1] = int(r["Info"])

        # parse time
        self.event_data["OriginTime"] = self.event_data["Time"]
        self.event_data["OriginQuarterTime"] = self.event_data["Time"].apply(self.parse_origin_quarter_time)
        self.event_data["Quarter"] = self.event_data["Time"].apply(self.parse_quarter)
        self.event_data["Time"] = self.event_data["Time"].apply(self.parse_time)
        self.event_data.sort_values(by=['Time'], ascending=[True])

    def get_stats(self):
        self.check_switch_people()
        self.get_stat_item_dfs()
        columns = [self.terms[stat_item] for stat_item in self.target_stats]
        self.player_stats = [pd.DataFrame(columns=columns) for i in range(self.num_teams)]
        for i, team in enumerate(self.team_names):
            target_names = self.player_names[i]
            for name in target_names:
                row = {self.terms["name"]: name}
                for stat_item in self.target_stats:
                    if stat_item in high_level_stats:
                        continue
                    value = eval("self.get_{}('{}', {})".format(stat_item, name, i))
                    row[self.terms[stat_item]] = value
                # print(row)
                # print(self.player_stats[i].index)
                self.player_stats[i] = append(self.player_stats[i], row)
            if self.get_team_stats:
                row = {self.terms["name"]: team}
                for stat_item in self.target_stats:
                        if stat_item in high_level_stats:
                            continue
                        # print(stat_item)
                        value = eval("self.get_{}('{}', {})".format(stat_item, "all", i))
                        row[self.terms[stat_item]] = value
                self.player_stats[i] = append(self.player_stats[i], row)

        for stat_item in high_level_stats:
            if stat_item in self.target_stats:
                eval("self.get_{}()".format(stat_item))
        for i in range(self.num_teams):
            self.player_stats[i].set_index('姓名', inplace = True)
        # print(self.player_stats)
        scores = self.get_total_scores()
        self.scores = "{}:{}".format(scores[0], scores[1])
        try:
            self.scores = self.config["scores"]
        except:
            pass
        self.scores_rev = "{}:{}".format(scores[1], scores[0])

    def get_total_scores(self):
        
            return sum(list(self.player_stats[0]["得分"])), sum(list(self.player_stats[1]["得分"]))

    def get_background_img(self, wide=False):
        bg_dir = "backgrounds"
        prefix = "background_wide" if wide else "background"
        try:
            background_config = self.config["bg"]
            background_path = f'{prefix}_{background_config}.png'
        except:
            background_path = f'{prefix}.png'
        image = plt.imread(os.path.join(bg_dir, background_path))
        return image

    def plot_stats_single_team(self, team_idx, show=False, save=None, title=None):
        if self.player_stats is None:
            self.get_stats()
        fig, ax = plt.subplots(figsize=(21.1, 10), dpi=80)
        image = self.get_background_img(wide=True)
        background_ax = plt.axes([0, 0, 1, 1])
        background_ax.set_zorder(-1) # set the background subplot behind the others
        background_ax.imshow(image, aspect='auto')

        table = self.plot_table(fig, ax, team_idx, plot_team_name=False, row_height=0.8, wide=False)

        game_scores_txt = "{} {} {}".format(self.team_names[0], self.scores, self.team_names[1])
        team_names_txt = "{} {}".format(self.team_names[0], self.team_names[1])
        info_txt = "{} {}".format(self.match_date, self.court_name)
        # info_txt = "test"

        JUSHOOP_title_txt = self.JUSHOOP_title_txt if title is None else title


        plt.title(label=JUSHOOP_title_txt,
                  fontdict={"family": FONT, "size": 40, "color": "#e7410a"},
                  y=0.92)
        
        

        if len(self.team_names) == 2:
            sub_title_txt = "{}vs{}".format(self.team_names[team_idx], self.team_names[1-team_idx])
        else:
            sub_title_txt = ""

        txt_length = len(sub_title_txt) + len(info_txt)
        blanks = int((52 - txt_length) * 5)
        
        plt.suptitle("{}{}{}".format(sub_title_txt, blanks * " ", info_txt), fontdict={"family": FONT, "color": "#fefefe"}, fontsize=25,
                     x=0.5, y=0.88, fontweight="bold")


        matplotlib.pyplot.subplots_adjust(left=0.02, bottom=0.001, right=0.982, top=0.893)

        if show:
            plt.show()
        if save is not None:
            plt.savefig(os.path.join(save, "{}".format(self.team_names[team_idx])), dpi=300)
        plt.close()


    def plot_stats_both_team(self, show=False, save=None, title=None):
        fig = plt.figure(num=1, figsize=(17.46*1.6, 10*1.6), dpi=80)
        image = self.get_background_img(wide=False)
        background_ax = plt.axes([0, 0, 1, 1])
        background_ax.set_zorder(-1) # set the background subplot behind the others
        background_ax.imshow(image, aspect='auto')

        # # 调整上下两个表格的占用比例
        # lens = [len(self.player_stats[0]), len(self.player_stats[1])]
        # max_height = max([lens[0] / sum(lens), lens[1] / sum(lens)])
        # max_index = [lens[0] / sum(lens), lens[1] / sum(lens)].index(max_height)
        # max_height = linear_map(max_height)
        
        # heights = [0,0]
        # heights[max_index] = max_height
        # heights[1-max_index] = 1 - max_height
        # heights[0] = int(100 * heights[0])

        heights = [50, 50]

        gs = gridspec.GridSpec(100, 1)

        ax1 = plt.subplot(gs[0:heights[0]+1, 0])
        ax2 = plt.subplot(gs[heights[0]-3:-1, 0])


        table1 = self.plot_table(fig, ax1, 0, row_height=1)
        table2 = self.plot_table(fig, ax2, 1, row_height=1)

        game_scores_txt = "{} {} {}".format(self.team_names[0], self.scores, self.team_names[1])
        info_txt = "{} {}".format(self.match_date, self.court_name)

        JUSHOOP_title_txt = self.JUSHOOP_title_txt if title is None else title
        
        plt.title(label=JUSHOOP_title_txt,
                  fontdict={"family": FONT, "size": 50, "color": "#e7410a"},
                  y=2)
        
        txt_length = len(game_scores_txt) + len(info_txt)
        blanks = int((62 - txt_length) * 5)

        # plt.rcParams["text.color"] = "#000000"
        plt.suptitle("{}{}{}".format(game_scores_txt, blanks * " ", info_txt),
                     fontdict={"family": FONT, "color": "#fefefe"}, fontsize=30,
                     x=0.5, y=0.9, fontweight="bold")
        # logo = Image.open('logo1.png')
        # plt.imshow(logo)
        # for font in matplotlib.font_manager.fontManager.ttflist:
        #     print(font.name, '-', font.fname)
        matplotlib.pyplot.subplots_adjust(left=0.02, bottom=0.001, right=0.982, top=0.893)

        if show:
            plt.show()
        if save is not None:
            plt.savefig(os.path.join(save, "{}_vs_{}".format(self.team_names[0], self.team_names[1])), dpi=300)
        plt.close()

    def plot_table(self, fig, ax, team_idx, plot_team_name=True, row_height=1, wide=True):
        ROW_HEIGHT = row_height
        colors = {
            "even": (0.4, 0.4, 0.4, 0.8),
            "bg": (0.2, 0.2, 0.2, 0.8),
            "title": "#123456",
            "text": "#FFFFFF"
        }

        text_color = "#FFFFFF"

        if not wide:
            MY_TITLE_TEXT_PRORPS["fontsize"] = 21
        else:
            MY_TITLE_TEXT_PRORPS["fontsize"] = 26


        # fig.set_facecolor(bg_color)
        ax.set_facecolor(colors["bg"])

        team_title = self.team_names[team_idx] if plot_team_name else ""

        table_col_defs = []
        table_col_defs.append(self.get_col("姓名", team_idx, title=team_title, team_name=self.team_names[team_idx], text_color=colors["text"]))
        if not self.user_table_cols is None:
            self.table_cols = self.user_table_cols
        for stat_name in self.table_cols:
            table_col_defs.append(self.get_col(stat_name, team_idx, team_name=self.team_names[team_idx], text_color=colors["text"]))

        player_stats = self.player_stats[team_idx].copy()
        if self.get_team_stats:
            player_stats["姓名"] = player_stats.index
            player_stats["姓名"][-1] = "全队"
            player_stats.set_index("姓名", inplace=True)

        # ax.set_ylim(-0.5, 1 - 0.5)


        tab = myTable(player_stats,
                    ax=ax,
                    column_definitions=table_col_defs,
                    row_dividers=False,
                    col_label_divider=False,
                    footer_divider=False,
                    columns=self.table_cols,
                    even_row_color=colors["even"],
                    # footer_divider_kw={"color": colors["bg"], "lw": 2},
                    # col_label_divider_kw={"linestyle": "-", "linewidth": 1},
                    # row_divider_kw={"color": colors["bg"], "lw": 2},
                    # column_border_kw={"color": colors["bg"], "lw": 2},
                    textprops={"ha": "center", "weight": "bold"}
                    )
        return tab
    
    def get_col(self, stat_name, team_idx, team_name="", text_color="#FFFFFF", title=None):
        width = 0.5
        formatter = None
        text_cmap = None
        cmap = LinearSegmentedColormap.from_list(
            name="bugw", colors=["#FF0000", "#e0e8df", "#00EE76"], N=256
        )
        cmap_r = LinearSegmentedColormap.from_list(
            name="bugw", colors=["#00EE76", "#e0e8df", "#FF0000"], N=256
        )
        if title is None:
            title = self.terms_en[stat_name] if self.use_en else stat_name
        if stat_name == "姓名":
            return ColDef(stat_name, width=1.3, textprops={"fontsize": 22, "weight": "bold", "color": text_color, "family": "Microsoft YaHei"}, title=team_name)
        elif stat_name in ["上场时间", "后场+前场篮板", "球权使用率", "真实命中率"]:
            width = 1.0
            if "+" in stat_name:
                title = title.replace("+", "\n+")
            if "率" in stat_name:
                formatter=decimal_to_percent
        elif stat_name == "在场得分(10回合)":
            width = 1.0
            title = title.replace("(", "\n(")
            text_cmap = normed_cmap(self.player_stats[team_idx]["在场得分(10回合)"], cmap=cmap, num_stds=1)
        elif stat_name == "正负值":
            # print("hello")
            text_cmap = my_normed_cmap(self.player_stats[team_idx]["正负值"], cmap=cmap, num_stds=1.2)
        elif stat_name == "在场失分(10回合)":
            width = 1.0
            title = title.replace("(", "\n(")
            text_cmap = normed_cmap(self.player_stats[team_idx]["在场失分(10回合)"], cmap=cmap_r, num_stds=1)
        elif stat_name == "效率值":
            text_cmap = normed_cmap(self.player_stats[team_idx]["效率值"], cmap=cmap, num_stds=1.2)

        if len(stat_name) >= 4 and width == 0.5:
            width = 0.7
        elif len(stat_name) == 3 and width == 0.5:
            width = 0.6

        return ColDef(stat_name, width=width, title=title,
                   text_cmap=text_cmap, formatter=formatter, textprops={"fontsize": 20, "color": text_color, "family": "Microsoft YaHei"})
    

    def print_info(self):
        print(self.team_names)
        print(self.player_names)
        print(self.event_data.head(20))
        print(self.event_data.tail(20))
        print(self.match_date)
        print(self.actual_quarter_times)

    # 从比赛开始时为起点计时
    def parse_time(self, time):
        t = time.split(" - ")
        t_ = t[1].split(" : ")

        q, m, s = int(t[0]), int(t_[0]), int(t_[1])
        return sum(self.actual_quarter_times[:q - 1]) + m * 60 + s

    def parse_quarter(self, time):
        t = time.split(" - ")
        t_ = t[1].split(" : ")

        q, m, s = int(t[0]), int(t_[0]), int(t_[1])
        return q

    # 从视频最初开始计时
    def parse_origin_quarter_time(self, time):
        t = time.split(" - ")
        t_ = t[1].split(" : ")

        q, m, s = int(t[0]), int(t_[0]), int(t_[1])
        return m * 60 + s + int(self.quarter_start_times[q - 1])

    def get_stat_item_dfs(self):
        # 一次性筛选好各数据项,避免重复处理
        self.scores_df = self.event_data[(self.event_data.Info == "进球")]

        self.twopts_atpt_df = self.event_data[(self.event_data.Event == "2分球出手")]
        self.threepts_atpt_df = self.event_data[(self.event_data.Event == "3分球出手")]
        self.fts_atpt_df = self.event_data[(self.event_data.Event == "罚球出手")]

        self.rebounds_df = self.event_data[(self.event_data.Event == "篮板")]
        self.assists_df = self.event_data[(self.event_data.Event == "助攻")]
        self.steals_df = self.event_data[(self.event_data.Event == "抢断")]
        self.blocks_df = self.event_data[(self.event_data.Event == "盖帽")]
        self.tos_df = self.event_data[(self.event_data.Event == "失误")]
        self.fouls_df = self.event_data[(self.event_data.Event == "犯规")]



    def df_query(self, Event, Team=None, Player=None, Object=None, Info=None):
        df = eval(f"self.{Event}_df")
        query_str = "1&"
        same_team = True
        if (Object is not None):
            # 要找的是被抢断、被犯规、被盖帽
            # 这些数据，说明要查找的数据项，队伍和目标球员不在一个队
            if Event in ["steals", "blocks", "fouls"]:
                same_team = False
            if Object != "all":
                query_str += f"(df.Object == '{Object}')&"
        if Team is not None:
            # not check_event_team 说明不检测队伍（比如有临时换队情况，这时会出现抢断自己队、助攻别的队等）
            if not self.check_event_team and Event in ["assists", "steals", "blocks", "fouls"]:
                pass
            else:
                equal = "==" if same_team else "!="
                query_str += f"(df.Team {equal} '{Team}')&"
        if Player is not None and Player != "all":
            query_str += f"(df.Player == '{Player}')&"

        if Info is not None:
            query_str += f"(df.Info == '{Info}')&"

        query_str = query_str[:-1] if query_str[-1] == "&" else query_str

        result = df[eval(query_str)]
        # if Event == "blocks":
        #     print((Event, Team, Player, Object, Info))
        #     print(result)
        return result
    

    def get_scores(self, name, team_id):
        team_name = self.team_names[team_id]
        scores = 0
        # 独立进球记录
        scores_df = self.df_query(Event="scores", Team=team_name, Player=name)
        assisted_df = self.df_query(Event="assists", Team=team_name, Object=name)

        scores += len(scores_df[scores_df.Event == "3分球出手"]) * 3 + len(scores_df[scores_df.Event == "2分球出手"]) * 2 + len(scores_df[scores_df.Event == "罚球出手"])
        scores += len(assisted_df[assisted_df.Info == "3分"]) * 3 + len(assisted_df[assisted_df.Info == "2分"]) * 2

        return scores


    def get_TS(self, name, team_id):
        team_name = self.team_names[team_id]
        scores = 0
        scores_df = self.df_query(Event="scores", Team=team_name, Player=name)
        get_assist_df = self.df_query(Event="assists", Team=team_name, Object=name)

        scores += len(scores_df[scores_df.Event == "3分球出手"]) * 3 + len(
            scores_df[scores_df.Event == "2分球出手"]) * 2 + len(
            scores_df[scores_df.Event == "罚球出手"])
        scores += len(get_assist_df[get_assist_df.Info == "3分"]) * 3 + len(
            get_assist_df[get_assist_df.Info == "2分"]) * 2


        twopts_atpt_df = self.df_query(Event="twopts_atpt", Team=team_name, Player=name)
        threepts_atpt_df = self.df_query(Event="threepts_atpt", Team=team_name, Player=name)
        fts_atpt_df = self.df_query(Event="fts_atpt", Team=team_name, Player=name)

        assisted_df = self.df_query(Event="assists", Object=name, Team=team_name)
        blocked_df = self.df_query(Event="blocks", Object=name, Team=team_name)

        atpt = len(twopts_atpt_df) + len(threepts_atpt_df) + len(assisted_df) + len(blocked_df)
        ft_atpt = len(fts_atpt_df)

        if scores == 0:
            return 0

        return round(scores / (2 * (atpt + 0.44 * ft_atpt)), 3)

    def get_rebounds(self, name, team_id):
        team_name = self.team_names[team_id]
        rebounds_df = self.df_query(Event="rebounds", Player=name, Team=team_name)
        return len(rebounds_df)
    

    
    def get_off_rebounds(self, name, team_id):
        team_name = self.team_names[team_id]
        rebounds_df = self.df_query(Event="rebounds", Player=name, Team=team_name, Info="前场")
        return len(rebounds_df)
    
    def get_def_rebounds(self, name, team_id):
        team_name = self.team_names[team_id]
        rebounds_df = self.df_query(Event="rebounds", Player=name, Team=team_name, Info="后场")
        return len(rebounds_df)

    def get_assists(self, name, team_id):
        team_name = self.team_names[team_id]
        assists_df = self.df_query(Event="assists", Player=name, Team=team_name)
        return len(assists_df)

    def get_time(self, name, team_id):
        team_name = self.team_names[team_id]


        if name == "all":
            get_on_arr = [0]
            get_off_arr = []
        else:
            get_on_arr = sorted(list(self.event_data[(self.event_data.Team == team_name) & (self.event_data.Object == name) & (self.event_data.Event == "换人")]["Time"]))
            get_off_arr = sorted(list(self.event_data[(self.event_data.Team == team_name) & (self.event_data.Player == name) & (self.event_data.Event == "换人")]["Time"]))
        

        assert (len(get_on_arr) == len(get_off_arr)) or (len(get_on_arr) == len(get_off_arr) + 1)

        if len(get_on_arr) > len(get_off_arr):
            get_off_arr.append(sum(self.actual_quarter_times))

        time = 0
        if len(get_on_arr):
            for i in range(len(get_on_arr)):
                time += get_off_arr[i] - get_on_arr[i]

        time *= (float(self.quarter_time) / (float(sum(self.actual_quarter_times)) / 60. / self.quarters))
        time = int(time)

        return "{:0>2d}:{:0>2d}".format(int(time / 60), time % 60)

    def get_steals(self, name, team_id):
        team_name = self.team_names[team_id]
        steals_df = self.df_query(Event="steals", Player=name, Team=team_name)
        return len(steals_df)

    def get_blocks(self, name, team_id):
        team_name = self.team_names[team_id]
        blocks_df = self.df_query(Event="blocks", Player=name, Team=team_name)
        return len(blocks_df)
    
    def get_blocked(self, name, team_id):
        team_name = self.team_names[team_id]
        blocked_df = self.df_query(Event="blocks", Object=name, Team=team_name)
        return len(blocked_df)

    def get_atpts(self, name, team_id):
        team_name = self.team_names[team_id]

        twopts_atpt_df = self.df_query(Event="twopts_atpt", Player=name, Team=team_name)
        threepts_atpt_df = self.df_query(Event="threepts_atpt", Player=name, Team=team_name)
        assisted_df = self.df_query(Event="assists", Object=name, Team=team_name)
        blocked_df = self.df_query(Event="blocks", Object=name, Team=team_name)

        # print(name, len(twopts_atpt_df), len(threepts_atpt_df), len(assisted_df), len(blocked_df))

        return len(twopts_atpt_df) + len(threepts_atpt_df) + len(assisted_df) + len(blocked_df)
    

    def get_mades(self, name, team_id):
        team_name = self.team_names[team_id]

        twopts_made_df = self.df_query(Event="twopts_atpt", Player=name, Team=team_name, Info="进球")
        threepts_made_df = self.df_query(Event="threepts_atpt", Player=name, Team=team_name, Info="进球")
        assisted_df = self.df_query(Event="assists", Object=name, Team=team_name)

        return len(twopts_made_df) + len(threepts_made_df) + len(assisted_df)
    
    
    def get_2pts_atpts(self, name, team_id):
        team_name = self.team_names[team_id]
        twopts_atpt_df = self.df_query(Event="twopts_atpt", Player=name, Team=team_name)
        assisted_df = self.df_query(Event="assists", Object=name, Team=team_name, Info="2分")
        blocked_df = self.df_query(Event="blocks", Object=name, Team=team_name, Info="2分")

        return len(twopts_atpt_df) + len(assisted_df) + len(blocked_df)
    

    def get_2pts_mades(self, name, team_id):
        team_name = self.team_names[team_id]
        twopts_made_df = self.df_query(Event="twopts_atpt", Player=name, Team=team_name, Info="进球")
        assisted_df = self.df_query(Event="assists", Object=name, Team=team_name, Info="2分")

        return len(twopts_made_df) + len(assisted_df)
    

    def get_2pts(self, name, team_id):
        team_name = self.team_names[team_id]
        twopts_made_df = self.df_query(Event="twopts_atpt", Player=name, Team=team_name, Info="进球")
        twopts_atpt_df = self.df_query(Event="twopts_atpt", Player=name, Team=team_name)

        twopts_assisted_df = self.df_query(Event="assists", Object=name, Info="2分", Team=team_name)
        twopts_blocked_df = self.df_query(Event="blocks", Object=name, Info="2分", Team=team_name)
        return "{}/{}".format(len(twopts_made_df) + len(twopts_assisted_df), len(twopts_atpt_df)+ len(twopts_assisted_df) + len(twopts_blocked_df))


    def get_3pts_atpts(self, name, team_id):
        team_name = self.team_names[team_id]
        threepts_atpt_df = self.df_query(Event="threepts_atpt", Player=name, Team=team_name)
        assisted_df = self.df_query(Event="assists", Object=name, Team=team_name, Info="3分")
        blocked_df = self.df_query(Event="blocks", Object=name, Team=team_name, Info="3分")

        return len(threepts_atpt_df) + len(assisted_df) + len(blocked_df)


    def get_3pts_mades(self, name, team_id):
        team_name = self.team_names[team_id]
        twopts_atpt_df = self.df_query(Event="threepts_atpt", Player=name, Team=team_name, Info="进球")
        assisted_df = self.df_query(Event="assists", Object=name, Team=team_name, Info="3分")

        return len(twopts_atpt_df) + len(assisted_df)


    def get_3pts(self, name, team_id):
        team_name = self.team_names[team_id]

        threepts_atpt_df = self.df_query(Event="threepts_atpt", Player=name, Team=team_name)
        threepts_made_df = threepts_atpt_df[threepts_atpt_df.Info == "进球"]

        threepts_assisted_df = self.df_query(Event="assists", Object=name, Team=team_name, Info="3分")
        threepts_blocked_df = self.df_query(Event="blocks", Object=name, Team=team_name, Info="3分")
        
        return "{}/{}".format(len(threepts_made_df) + len(threepts_assisted_df), len(threepts_atpt_df) + len(threepts_assisted_df) + len(threepts_blocked_df))


    def get_fts(self, name, team_id):
        team_name = self.team_names[team_id]
        fts_atpt_df = self.df_query(Player=name, Event="fts_atpt", Team=team_name)
        fts_made_df = fts_atpt_df[fts_atpt_df.Info == "进球"]
        
        return "{}/{}".format(len(fts_made_df), len(fts_atpt_df))
    
    def get_fts_atpts(self, name, team_id):
        team_name = self.team_names[team_id]
        fts_atpt_df = self.df_query(Event="fts_atpt", Player=name, Team=team_name)

        return len(fts_atpt_df)
    
    def get_fts_mades(self, name, team_id):
        team_name = self.team_names[team_id]
        fts_atpt_df = self.df_query(Event="fts_atpt", Player=name, Team=team_name, Info="进球")

        return len(fts_atpt_df)


    def get_od_rebounds(self, name, team_id):
        team_name = self.team_names[team_id]
        rebounds_df = self.df_query(Team=team_name, Player=name, Event="rebounds")

        return "{}+{}".format(len(rebounds_df[rebounds_df.Info == "后场"]), len(rebounds_df[rebounds_df.Info == "前场"]))


    def get_tos(self, name, team_id):
        team_name = self.team_names[team_id]

        TOs_df = self.df_query(Event="tos", Player=name, Team=team_name)

        stealed_df = self.df_query(Event="steals", Object=name, Team=team_name)

        off_fouls_df = self.df_query(Player=name, Event="fouls", Info="进攻犯规", Team=team_name)

        return len(TOs_df) + len(stealed_df) + len(off_fouls_df)

    def get_fouls(self, name, team_id):
        team_name = self.team_names[team_id]
        fouls_df = self.df_query(Player=name, Event="fouls", Team=team_name)

        return len(fouls_df)

    def get_make_fouls(self, name, team_id):
        team_name = self.team_names[team_id]
        make_fouls_df = self.df_query(Event="fouls", Team=team_name, Object=name)

        return len(make_fouls_df)
    

    def get_assisted(self, name, team_id):
        team_name = self.team_names[team_id]
        assists_df = self.df_query(Event="assists", Object=name, Team=team_name)
        return len(assists_df)
    

    def get_assists_2pts(self, name, team_id):
        team_name = self.team_names[team_id]
        assists_df = self.df_query(Event="assists", Object=name, Team=team_name, Info="2分")
        return len(assists_df)
    

    def get_assists_3pts(self, name, team_id):
        team_name = self.team_names[team_id]
        assists_df = self.df_query(Event="assists", Object=name, Team=team_name, Info="3分")
        return len(assists_df)

    def get_EFF(self):
        for idx, team in enumerate(self.team_names):
            for i, r in self.player_stats[idx].iterrows():
                EFF = 0
                EFF += (int(r["得分"]) + int(r["篮板"]) + int(r["助攻"]) + int(r["抢断"]) + int(
                    r["盖帽"] - int(r["失误"])))
                EFF -= (parse_shoots(r["2分"]) + parse_shoots(r["3分"]) + parse_shoots(r["罚球"]))
                self.player_stats[idx].loc[i, "效率值"] = round(EFF, 1)

    def get_USG(self):
        for idx, team in enumerate(self.team_names):
            for i, r in self.player_stats[idx].iterrows():
                self.player_stats[idx].loc[i, "球权使用率"] = round(r["回合占有数"]/r["回合数"], 3)


    def get_rounds(self, name, team_id):
        team_name = self.team_names[team_id]
        team_name_op = self.team_names[1 - team_id]

        if name == "all":
            get_on_arr = [0]
            get_off_arr = []
        else:
            get_on_arr = sorted(list(
                self.event_data[(self.event_data.Team == team_name) & (self.event_data.Object == name) & (self.event_data.Event == "换人")]["Time"]))
            get_off_arr = sorted(list(
                self.event_data[(self.event_data.Team == team_name) & (self.event_data.Player == name) & (self.event_data.Event == "换人")]["Time"]))

        assert (len(get_on_arr) == len(get_off_arr)) or (len(get_on_arr) == len(get_off_arr) + 1)

        if len(get_on_arr) > len(get_off_arr):
            get_off_arr.append(sum(self.actual_quarter_times))


        rounds = 0
        for i in range(len(get_on_arr)):
            filtered_event_data = self.event_data[(self.event_data.Time >= get_on_arr[i]) & (self.event_data.Time <= get_off_arr[i])]

            stealed_rounds = len(df_filter(filtered_event_data, Team=team_name_op, Event="抢断"))

            off_foul_rounds = len(df_filter(filtered_event_data, Team=team_name, Info="进攻犯规")) + \
                              len(df_filter(filtered_event_data, Team=team_name, Info="违体进攻犯规"))
            
            atpt_rounds = len(df_filter(filtered_event_data, Event="2分球出手", Team=team_name)) +\
                          len(df_filter(filtered_event_data, Event="3分球出手", Team=team_name)) +\
                          len(df_filter(filtered_event_data, Event="助攻", Team=team_name))
            
            TO_rounds = len(df_filter(filtered_event_data, Event="失误", Team=team_name))

            fouled_rounds = len(df_filter(filtered_event_data, Team=team_name_op, Info="普通犯规犯满")) +\
                            len(df_filter(filtered_event_data, Team=team_name_op, Info="投篮犯规"))
            rounds += (stealed_rounds + off_foul_rounds + atpt_rounds + TO_rounds + fouled_rounds)

        if rounds == 0:
            rounds += 1
        return rounds

    def get_used_rounds(self, name, team_id):
        team_name = self.team_names[team_id]
        team_name_op = self.team_names[1 - team_id]

        if name == "all":
            get_on_arr = [0]
            get_off_arr = []
            name = None
        else:
            get_on_arr = sorted(list(
                self.event_data[(self.event_data.Team == team_name) & (self.event_data.Object == name) & (self.event_data.Event == "换人")]["Time"]))
            get_off_arr = sorted(list(
                self.event_data[(self.event_data.Team == team_name) & (self.event_data.Player == name) & (self.event_data.Event == "换人")]["Time"]))

        assert (len(get_on_arr) == len(get_off_arr)) or (len(get_on_arr) == len(get_off_arr) + 1)

        if len(get_on_arr) > len(get_off_arr):
            get_off_arr.append(sum(self.actual_quarter_times))


        rounds = 0
        for i in range(len(get_on_arr)):
            filtered_event_data = self.event_data[(self.event_data.Time >= get_on_arr[i]) & (self.event_data.Time <= get_off_arr[i])]

            stealed_rounds = len(df_filter(filtered_event_data, Team=team_name_op, Event="抢断", Object=name))

            off_foul_rounds = len(df_filter(filtered_event_data, Team=team_name, Info="进攻犯规", Player=name)) + \
                              len(df_filter(filtered_event_data, Team=team_name, Info="违体进攻犯规", Player=name))
            
            atpt_rounds = len(df_filter(filtered_event_data, Event="2分球出手", Team=team_name, Player=name)) +\
                          len(df_filter(filtered_event_data, Event="3分球出手", Team=team_name, Player=name)) +\
                          len(df_filter(filtered_event_data, Event="助攻", Team=team_name, Object=name))
            
            TO_rounds = len(df_filter(filtered_event_data, Event="失误", Team=team_name, Player=name))

            fouled_rounds = len(df_filter(filtered_event_data, Team=team_name_op, Info="普通犯规犯满", Object=name)) +\
                            len(df_filter(filtered_event_data, Team=team_name_op, Info="投篮犯规", Object=name))
            rounds += (stealed_rounds + off_foul_rounds + atpt_rounds + TO_rounds + fouled_rounds)

        # if rounds == 0:
        #     rounds += 1
        return rounds
    

    def get_oncourt_scores(self, name, team_id):
        team_name = self.team_names[team_id]
        team_name_op = self.team_names[1 - team_id]
        # print(team_name, team_name_op)
        # print(self.event_data.head())
        if name == "all":
            get_on_arr = [0]
            get_off_arr = []
        else:
            get_on_arr = sorted(list(
                self.event_data[(self.event_data.Team == team_name) & (self.event_data.Object == name) & (
                            self.event_data.Event == "换人")]["Time"]))
            get_off_arr = sorted(list(
                self.event_data[(self.event_data.Team == team_name) & (self.event_data.Player == name) & (
                            self.event_data.Event == "换人")]["Time"]))

        assert (len(get_on_arr) == len(get_off_arr)) or (len(get_on_arr) == len(get_off_arr) + 1)

        if len(get_on_arr) > len(get_off_arr):
            get_off_arr.append(sum(self.actual_quarter_times))
        time = 0
        if len(get_on_arr):
            for i in range(len(get_on_arr)):
                time += get_off_arr[i] - get_on_arr[i]

        if time == 0:
            return 0

        team_scores = 0
        """计算在场得分与失分"""
        for i in range(len(get_on_arr)):
            scores_df = self.event_data[
                (self.event_data.Time >= get_on_arr[i]) & (self.event_data.Time <= get_off_arr[i]) & (
                        self.event_data.Team == team_name) & (self.event_data.Info == "进球")]
            get_assist_df = self.event_data[
                (self.event_data.Time >= get_on_arr[i]) & (self.event_data.Time <= get_off_arr[i]) & (
                        self.event_data.Team == team_name) & (self.event_data.Event == "助攻")]
            team_scores += (
                    len(scores_df[scores_df.Event == "3分球出手"]) * 3 + len(
                scores_df[scores_df.Event == "2分球出手"]) * 2 + len(
                scores_df[scores_df.Event == "罚球出手"]))
            team_scores += (
                    len(get_assist_df[get_assist_df.Info == "3分"]) * 3 + len(
                get_assist_df[get_assist_df.Info == "2分"]) * 2)
        # print(name, team_scores, rounds)

        return team_scores


    def get_oncourt_loses(self, name, team_id):
        team_name = self.team_names[team_id]
        team_name_op = self.team_names[1 - team_id]
        # print(team_name, team_name_op)
        if name == "all":
            get_on_arr = [0]
            get_off_arr = []
        else:
            get_on_arr = sorted(list(
                self.event_data[(self.event_data.Team == team_name) & (self.event_data.Object == name) & (
                            self.event_data.Event == "换人")]["Time"]))
            get_off_arr = sorted(list(
                self.event_data[(self.event_data.Team == team_name) & (self.event_data.Player == name) & (
                            self.event_data.Event == "换人")]["Time"]))

        assert (len(get_on_arr) == len(get_off_arr)) or (len(get_on_arr) == len(get_off_arr) + 1)

        if len(get_on_arr) > len(get_off_arr):
            get_off_arr.append(sum(self.actual_quarter_times))

        time = 0
        if len(get_on_arr):
            for i in range(len(get_on_arr)):
                time += get_off_arr[i] - get_on_arr[i]
        if time == 0:
            return 0

        op_team_scores = 0
        """计算在场得分与失分"""
        for i in range(len(get_on_arr)):
            op_scores_df = self.event_data[
                (self.event_data.Time >= get_on_arr[i]) & (self.event_data.Time <= get_off_arr[i]) & (
                        self.event_data.Team == team_name_op) & (self.event_data.Info == "进球")]
            op_get_assist_df = self.event_data[
                (self.event_data.Time >= get_on_arr[i]) & (self.event_data.Time <= get_off_arr[i]) & (
                        self.event_data.Team == team_name_op) & (self.event_data.Event == "助攻")]

            op_team_scores += (
                    len(op_scores_df[op_scores_df.Event == "3分球出手"]) * 3 + len(
                op_scores_df[op_scores_df.Event == "2分球出手"]) * 2 + len(
                op_scores_df[op_scores_df.Event == "罚球出手"]))
            op_team_scores += (
                    len(op_get_assist_df[op_get_assist_df.Info == "3分"]) * 3 + len(
                op_get_assist_df[op_get_assist_df.Info == "2分"]) * 2)

        
        return op_team_scores
    

    def get_oncourt_per_scores(self):
        for idx, team in enumerate(self.team_names):
            for i, r in self.player_stats[idx].iterrows():
                ORtg = round(r["在场得分"] / r["回合数"] * 10, 1)

                self.player_stats[idx].loc[i, "在场得分(10回合)"] = round(ORtg, 1)

    def get_oncourt_per_loses(self):
        for idx, team in enumerate(self.team_names):
            for i, r in self.player_stats[idx].iterrows():
                DRtg = round(r["在场失分"] / r["回合数"] * 10, 1)

                self.player_stats[idx].loc[i, "在场失分(10回合)"] = round(DRtg, 1)
    
    def get_plus_minus(self):
        for idx, team in enumerate(self.team_names):
            for i, r in self.player_stats[idx].iterrows():
                # print(r["在场得分"], r["在场失分"])
                plus_minus = round(r["在场得分"] - r["在场失分"], 1)
                sign = "+" if plus_minus >= 0 else "-"
                if plus_minus == 0:
                    sign = ""

                # self.player_stats[idx].loc[i, "正负值_带符号"] = f"{sign}{abs(plus_minus)}"
                self.player_stats[idx].loc[i, "正负值"] = plus_minus
    

    def get_oncourt_off_rounds(self, name, team_id):

        """计算在场回合数
        进攻结束回合标志：被抢断，进攻犯规/违体犯规进攻，失误，进球，对方投篮犯规/普通犯规犯满, 被抢到后场篮板

        #bug 出手后直接出界
        #bug 争球
        #bug 2+1算两回合
        """
        team_name = self.team_names[team_id]
        team_name_op = self.team_names[1 - team_id]
        if name == "all":
            get_on_arr = [0]
            get_off_arr = []
        else:
            get_on_arr = sorted(list(
                self.event_data[(self.event_data.Team == team_name) & (self.event_data.Object == name) & (self.event_data.Event == "换人")]["Time"]))
            get_off_arr = sorted(list(
                self.event_data[(self.event_data.Team == team_name) & (self.event_data.Player == name) & (self.event_data.Event == "换人")]["Time"]))

        assert (len(get_on_arr) == len(get_off_arr)) or (len(get_on_arr) == len(get_off_arr) + 1)

        if len(get_on_arr) > len(get_off_arr):
            get_off_arr.append(sum(self.actual_quarter_times))

        time = 0
        if len(get_on_arr):
            for i in range(len(get_on_arr)):
                time += get_off_arr[i] - get_on_arr[i]

        if time == 0:
            return 0
        rounds = 0
        for i in range(len(get_on_arr)):
            filtered_event_data = self.event_data[(self.event_data.Time >= get_on_arr[i]) & (self.event_data.Time <= get_off_arr[i])]
            stealed_rounds = len(
                filtered_event_data[(filtered_event_data.Team == team_name_op) & (filtered_event_data.Event == "抢断")])
            off_foul_rounds = len(
                filtered_event_data[(filtered_event_data.Team == team_name) & (filtered_event_data.Info == "进攻犯规")]) + len(
                filtered_event_data[(filtered_event_data.Team == team_name) & (filtered_event_data.Info == "违体进攻犯规")])
            scored_rounds = len(
                filtered_event_data[(filtered_event_data.Team == team_name) & (filtered_event_data.Info == "进球")]) + len(
                filtered_event_data[(filtered_event_data.Team == team_name) & (filtered_event_data.Event == "助攻")]) - len(
                filtered_event_data[(filtered_event_data.Team == team_name) & (filtered_event_data.Info == "进球") & (
                        filtered_event_data.Event == "罚球出手")])
            TO_rounds = len(
                filtered_event_data[(filtered_event_data.Team == team_name) & (filtered_event_data.Event == "失误")])
            def_rebounded_rounds = len(
                filtered_event_data[(filtered_event_data.Team == team_name_op) & (filtered_event_data.Info == "后场")])
            fouled_rounds = len(filtered_event_data[(filtered_event_data.Team == team_name_op) & (filtered_event_data.Info == "普通犯规犯满")]) + len(
                filtered_event_data[(filtered_event_data.Team == team_name_op) & (filtered_event_data.Info == "投篮犯规")])

            rounds += (stealed_rounds + off_foul_rounds + scored_rounds + TO_rounds + def_rebounded_rounds + fouled_rounds)

        if rounds == 0:
            rounds += 1

        return rounds

    def get_oncourt_def_rounds(self, name, team_id):
        team_name = self.team_names[team_id]
        team_name_op = self.team_names[1 - team_id]
        if name == "all":
            get_on_arr = [0]
            get_off_arr = []
        else:
            get_on_arr = sorted(list(
                self.event_data[(self.event_data.Team == team_name) & (self.event_data.Object == name) & (self.event_data.Event == "换人")]["Time"]))
            get_off_arr = sorted(list(
                self.event_data[(self.event_data.Team == team_name) & (self.event_data.Player == name) & (self.event_data.Event == "换人")]["Time"]))

        assert (len(get_on_arr) == len(get_off_arr)) or (len(get_on_arr) == len(get_off_arr) + 1)

        if len(get_on_arr) > len(get_off_arr):
            get_off_arr.append(sum(self.actual_quarter_times))

        time = 0
        if len(get_on_arr):
            for i in range(len(get_on_arr)):
                time += get_off_arr[i] - get_on_arr[i]

        if time == 0:
            return 0
        rounds = 0
        for i in range(len(get_on_arr)):
            filtered_event_data = self.event_data[(self.event_data.Time >= get_on_arr[i]) & (self.event_data.Time <= get_off_arr[i])]
            stealed_rounds = len(
                filtered_event_data[(filtered_event_data.Team == team_name) & (filtered_event_data.Event == "抢断")])
            off_foul_rounds = len(
                filtered_event_data[(filtered_event_data.Team == team_name_op) & (filtered_event_data.Info == "进攻犯规")]) + len(
                filtered_event_data[(filtered_event_data.Team == team_name_op) & (filtered_event_data.Info == "违体进攻犯规")])
            scored_rounds = len(
                filtered_event_data[(filtered_event_data.Team == team_name_op) & (filtered_event_data.Info == "进球")]) + len(
                filtered_event_data[(filtered_event_data.Team == team_name_op) & (filtered_event_data.Event == "助攻")]) - len(
                filtered_event_data[(filtered_event_data.Team == team_name_op) & (filtered_event_data.Info == "进球") & (
                        filtered_event_data.Event == "罚球出手")])
            TO_rounds = len(
                filtered_event_data[(filtered_event_data.Team == team_name_op) & (filtered_event_data.Event == "失误")])
            def_rebounded_rounds = len(
                filtered_event_data[(filtered_event_data.Team == team_name) & (filtered_event_data.Info == "后场")])
            fouled_rounds = len(filtered_event_data[(filtered_event_data.Team == team_name) & (
                    filtered_event_data.Info == "普通犯规犯满")]) + len(
                filtered_event_data[(filtered_event_data.Team == team_name) & (filtered_event_data.Info == "投篮犯规")])

            rounds += (
                    stealed_rounds + off_foul_rounds + scored_rounds + TO_rounds + def_rebounded_rounds + fouled_rounds)
        if rounds == 0:
            rounds += 1

        return rounds
    

    def get_oncourt_team_rebounds(self, name, team_id):
        team_name = self.team_names[team_id]
        team_name_op = self.team_names[1 - team_id]

        if name == "all":
            get_on_arr = [0]
            get_off_arr = []
        else:
            get_on_arr = sorted(list(
                self.event_data[(self.event_data.Team == team_name) & (self.event_data.Object == name) & (
                        self.event_data.Event == "换人")]["Time"]))
            get_off_arr = sorted(list(
                self.event_data[(self.event_data.Team == team_name) & (self.event_data.Player == name) & (
                        self.event_data.Event == "换人")]["Time"]))

        assert (len(get_on_arr) == len(get_off_arr)) or (len(get_on_arr) == len(get_off_arr) + 1)

        if len(get_on_arr) > len(get_off_arr):
            get_off_arr.append(sum(self.actual_quarter_times))

        time = 0
        if len(get_on_arr):
            for i in range(len(get_on_arr)):
                time += get_off_arr[i] - get_on_arr[i]
        if time == 0:
            return 0

        team_rebounds = 0
        for i in range(len(get_on_arr)):
            rebounds_df = self.event_data[
                (self.event_data.Time >= get_on_arr[i]) & (self.event_data.Time <= get_off_arr[i]) & (
                        self.event_data.Team == team_name) & (self.event_data.Event == "篮板")]

            team_rebounds += len(rebounds_df)

        return team_rebounds


    def get_oncourt_opponent_rebounds(self, name, team_id):
        team_name = self.team_names[team_id]
        team_name_op = self.team_names[1 - team_id]
        if name == "all":
            get_on_arr = [0]
            get_off_arr = []
        else:
            get_on_arr = sorted(list(
                self.event_data[(self.event_data.Team == team_name) & (self.event_data.Object == name) & (
                        self.event_data.Event == "换人")]["Time"]))
            get_off_arr = sorted(list(
                self.event_data[(self.event_data.Team == team_name) & (self.event_data.Player == name) & (
                        self.event_data.Event == "换人")]["Time"]))

        assert (len(get_on_arr) == len(get_off_arr)) or (len(get_on_arr) == len(get_off_arr) + 1)

        if len(get_on_arr) > len(get_off_arr):
            get_off_arr.append(sum(self.actual_quarter_times))

        time = 0
        if len(get_on_arr):
            for i in range(len(get_on_arr)):
                time += get_off_arr[i] - get_on_arr[i]
        if time == 0:
            return 0

        op_team_rebounds = 0
        for i in range(len(get_on_arr)):
            rebounds_df = self.event_data[
                (self.event_data.Time >= get_on_arr[i]) & (self.event_data.Time <= get_off_arr[i]) & (
                        self.event_data.Team == team_name_op) & (self.event_data.Event == "篮板")]

            op_team_rebounds += len(rebounds_df)

        return op_team_rebounds
        
    def get_games_played(self, name, team_id):
        return 1
    
    def get_games_wined(self, name, team_id):
        # print(self.player_stats[0].head)
        scores = (sum(list(self.player_stats[0]["得分"])), sum(list(self.player_stats[1]["得分"])))
        return scores.index(max(scores)) == team_id


if __name__ == '__main__':
    config = json.load(open("/Users/Markos/Desktop/basketball-stats-web-tool/GameStatsData/20230825_PURDUE_TG/config.json"))
    event_data = pd.read_csv("/Users/Markos/Desktop/basketball-stats-web-tool/GameStatsData/20230825_PURDUE_TG/events.csv")
    event_data = event_data.fillna("")

    print(config)


            
import numpy as np
from plottable import Table, ColDef
import matplotlib
import matplotlib.pyplot as plt
import argparse
import json
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from plottable.cmap import normed_cmap
from PIL import Image
import matplotlib.font_manager as font_manager

terms = {
    "name": "姓名",
    "time": "上场时间",
    "scores": "得分",
    "assists": "助攻",
    "rebounds": "篮板",
    "steals": "抢断",
    "blocks": "盖帽",
    "2PTs": "2分",
    "3PTs": "3分",
    "FTs": "罚球",
    "OD_rebounds": "后场+前场篮板",
    "fouls": "犯规",
    "TOs": "失误",
    "make_fouls": "造成犯规",
    "EFF": "效率值",
    "oncourt_per_scores": "在场得分(10回合)",
    "oncourt_per_loses": "在场失分(10回合)"
}

high_level_stats = ["EFF"]

start_round_events = ["抢断", "后场篮板"]
end_round_events = []

parser = argparse.ArgumentParser(description='Run Example')
parser.add_argument('config_file', type=str, help='path of config file')
parser.add_argument('event_data', type=str, help='path of config file')
args = parser.parse_args()

config = json.load(open(args.config_file))
quarter_time = config["quarter_time"]
scores = config["scores"]
actual_quarter_time = 21
quarters = config["quarters"]
event_data = pd.read_csv(args.event_data,)
event_data = event_data.fillna("")


def append(df, row_dict):
    return pd.concat([df, pd.DataFrame([row_dict])], ignore_index=True)

def parse_time(time):
    t = time.split(" - ")
    t_ = t[1].split(" : ")

    q, m, s = int(t[0]), int(t_[0]), int(t_[1])
    return (q-1) * actual_quarter_time * 60 + m * 60 + s

event_data["Time"] = event_data["Time"].apply(parse_time)


team_names = list(config["team_players"].keys())
players_A = config["team_players"][team_names[0]]
players_B = config["team_players"][team_names[1]]
player_names_A = [player["name"] for player in players_A]
player_names_B = [player["name"] for player in players_B]

print(event_data)
print(event_data[(event_data.Event=="换人")&(event_data.Time<2000)])
print(team_names)
print(player_names_A)
print(config["stats"])

columns = [terms[stat_item] for stat_item in config["stats"]]

player_stats_A = pd.DataFrame(columns=columns)
player_stats_B = pd.DataFrame(columns=columns)
# player_stats_A = append(player_stats_A, {"name":"test"})
# print(player_stats_A)

scores_df = event_data[(event_data.Player == "A1") & (event_data.Info == "进球")]
get_assist_df = event_data[(event_data.Object == "A1") & (event_data.Event == "助攻")]
print(len(scores_df))
print(len(get_assist_df))

# t = event_data[(event_data.Team == team_names[0]) & (event_data.Object == "A1") & (event_data.Event == "换人")]["Time"][0]
# print(t.split(" - ")[1].split(":"))


def stats():
    for name in player_names_A:
        row = {terms["name"]:name}
        for stat_item in config["stats"]:
            if stat_item in high_level_stats:
                continue
            value = eval("get_{}('{}', {})".format(stat_item, name, 0))
            row[terms[stat_item]] = value
        global player_stats_A
        player_stats_A = append(player_stats_A, row)

    for name in player_names_B:
        row = {terms["name"]:name}
        for stat_item in config["stats"]:
            if stat_item in high_level_stats:
                continue
            value = eval("get_{}('{}', {})".format(stat_item, name, 1))
            row[terms[stat_item]] = value
        global player_stats_B
        player_stats_B = append(player_stats_B, row)

    get_EFF()



def get_scores(name, team_id):
    team_name = team_names[team_id]
    scores = 0
    # 独立进球记录
    scores_df = event_data[(event_data.Team == team_name) & (event_data.Player == name) & (event_data.Info == "进球")]
    # 受助攻记录
    get_assist_df = event_data[(event_data.Team == team_name) & (event_data.Object == name) & (event_data.Event == "助攻")]
    scores += len(scores_df[scores_df.Event == "3分球出手"]) * 3 + len(scores_df[scores_df.Event == "2分球出手"]) * 2 + len(scores_df[scores_df.Event == "罚球出手"])
    scores += len(get_assist_df[get_assist_df.Info == "3分"]) * 3 + len(get_assist_df[get_assist_df.Info == "2分"]) * 2

    return scores


def get_rebounds(name, team_id):
    team_name = team_names[team_id]
    rebounds_df = event_data[(event_data.Team == team_name) & (event_data.Player == name) & (event_data.Event == "篮板")]
    return len(rebounds_df)


def get_assists(name, team_id):
    team_name = team_names[team_id]
    assists_df = event_data[(event_data.Team == team_name) & (event_data.Player == name) & (event_data.Event == "助攻")]
    return len(assists_df)

def get_time(name, team_id):
    team_name = team_names[team_id]
    get_on_arr = sorted(list(event_data[(event_data.Team == team_name) & (event_data.Object == name) & (event_data.Event == "换人")]["Time"]))
    get_off_arr = sorted(list(event_data[(event_data.Team == team_name) & (event_data.Player == name) & (event_data.Event == "换人")]["Time"]))

    # print(name)
    # print(len(get_on_arr), len(get_off_arr))
    assert (len(get_on_arr) == len(get_off_arr)) or (len(get_on_arr) == len(get_off_arr) + 1)


    if len(get_on_arr) > len(get_off_arr):
        get_off_arr.append(actual_quarter_time * quarters * 60)

    time = 0
    if len(get_on_arr):
        for i in range(len(get_on_arr)):
            time += get_off_arr[i] - get_on_arr[i]

    time *= (float(quarter_time) / float(actual_quarter_time))
    time = int(time)

    return "{:0>2d}:{:0>2d}".format(int(time/60), time%60)


def get_steals(name, team_id):
    team_name = team_names[team_id]
    steals_df = event_data[(event_data.Team == team_name) & (event_data.Player == name) & (event_data.Event == "抢断")]
    return len(steals_df)


def get_blocks(name, team_id):
    team_name = team_names[team_id]
    blocks_df = event_data[(event_data.Team == team_name) & (event_data.Player == name) & (event_data.Event == "盖帽")]
    return len(blocks_df)


def get_2PTs(name, team_id):
    team_name = team_names[team_id]
    team_name_op = team_names[1 - team_id]
    twopts_atpt_df = event_data[(event_data.Team == team_name) & (event_data.Player == name) & (event_data.Event == "2分球出手")]
    twopts_made_df = twopts_atpt_df[twopts_atpt_df.Info == "进球"]
    twopts_assisted_df = event_data[(event_data.Team == team_name) & (event_data.Object == name) & (event_data.Event == "助攻") & (event_data.Info == "2分")]
    twopts_blocked_df = event_data[(event_data.Team == team_name_op) & (event_data.Object == name) & (event_data.Event == "盖帽") & (event_data.Info == "2分")]
    return "{}/{}".format(len(twopts_made_df) + len(twopts_blocked_df) + len(twopts_assisted_df), len(twopts_atpt_df)+ len(twopts_assisted_df))


def get_3PTs(name, team_id):
    team_name = team_names[team_id]
    team_name_op = team_names[1 - team_id]
    threepts_atpt_df = event_data[(event_data.Team == team_name) & (event_data.Player == name) & (event_data.Event == "3分球出手")]
    threepts_made_df = threepts_atpt_df[threepts_atpt_df.Info == "进球"]
    threepts_assisted_df = event_data[(event_data.Team == team_name) & (event_data.Object == name) & (event_data.Event == "助攻") & (event_data.Info == "3分")]
    threepts_blocked_df = event_data[(event_data.Team == team_name_op) & (event_data.Object == name) & (event_data.Event == "盖帽") & (event_data.Info == "3分")]
    return "{}/{}".format(len(threepts_made_df) + len(threepts_blocked_df) + len(threepts_assisted_df), len(threepts_atpt_df) + len(threepts_assisted_df))


def get_FTs(name, team_id):
    team_name = team_names[team_id]
    fts_atpt_df = event_data[(event_data.Team == team_name) & (event_data.Player == name) & (event_data.Event == "罚球出手")]
    fts_made_df = fts_atpt_df[fts_atpt_df.Info == "进球"]
    return "{}/{}".format(len(fts_made_df), len(fts_atpt_df))


def get_OD_rebounds(name, team_id):
    team_name = team_names[team_id]
    rebounds_df = event_data[(event_data.Team == team_name) & (event_data.Player == name) & (event_data.Event == "篮板")]
    return "{}+{}".format(len(rebounds_df[rebounds_df.Info == "后场"]), len(rebounds_df[rebounds_df.Info == "前场"]))


def get_TOs(name, team_id):
    team_name = team_names[team_id]
    team_name_op = team_names[1 - team_id]
    TOs_df = event_data[(event_data.Team == team_name) & (event_data.Player == name) & (event_data.Event == "失误")]
    stealed_df = event_data[(event_data.Team == team_name_op) & (event_data.Object == name) & (event_data.Event == "抢断")]
    off_fouls_df = event_data[(event_data.Team == team_name) & (event_data.Player == name) & (event_data.Info == "进攻犯规")]

    return len(TOs_df) + len(stealed_df) + len(off_fouls_df)


def get_fouls(name, team_id):
    team_name = team_names[team_id]
    fouls_df = event_data[(event_data.Team == team_name) & (event_data.Player == name) & (event_data.Event == "犯规")]
    return len(fouls_df)


def get_make_fouls(name, team_id):
    team_name_op = team_names[1-team_id]
    make_fouls_df = event_data[(event_data.Team == team_name_op) & (event_data.Object == name) & (event_data.Event == "犯规")]
    return len(make_fouls_df)

def parse_shoots(shoots):
    shoots = shoots.split("/")
    return int(shoots[1]) -int(shoots[0])

def get_EFF():
    for i,r in player_stats_A.iterrows():
        EFF = 0
        EFF += (int(r["得分"]) + int(r["篮板"]) + int(r["助攻"]) + int(r["抢断"]) + int(r["盖帽"] - int(r["失误"])))
        EFF -= (parse_shoots(r["2分"]) + parse_shoots(r["3分"]) + parse_shoots(r["罚球"]))
        player_stats_A.loc[i, "效率值"] = EFF

    for i,r in player_stats_B.iterrows():
        EFF = 0
        EFF += (int(r["得分"]) + int(r["篮板"]) + int(r["助攻"]) + int(r["抢断"]) + int(r["盖帽"] - int(r["失误"])))
        EFF -= (parse_shoots(r["2分"]) + parse_shoots(r["3分"]) + parse_shoots(r["罚球"]))
        player_stats_B.loc[i, "效率值"] = EFF

def get_oncourt_per_scores(name, team_id):
    team_name = team_names[team_id]
    team_name_op = team_names[1 - team_id]
    get_on_arr = sorted(list(
        event_data[(event_data.Team == team_name) & (event_data.Object == name) & (event_data.Event == "换人")]["Time"]))
    get_off_arr = sorted(list(
        event_data[(event_data.Team == team_name) & (event_data.Player == name) & (event_data.Event == "换人")]["Time"]))

    assert (len(get_on_arr) == len(get_off_arr)) or (len(get_on_arr) == len(get_off_arr) + 1)

    if len(get_on_arr) > len(get_off_arr):
        get_off_arr.append(actual_quarter_time * quarters * 60)

    time = 0
    if len(get_on_arr):
        for i in range(len(get_on_arr)):
            time += get_off_arr[i] - get_on_arr[i]

    if time == 0:
        return 0

    team_scores = 0
    rounds = 0
    """计算在场得分与失分"""
    for i in range(len(get_on_arr)):
        scores_df = event_data[(event_data.Time >= get_on_arr[i]) & (event_data.Time <= get_off_arr[i]) & (
                event_data.Team == team_name) & (event_data.Info == "进球")]
        get_assist_df = event_data[(event_data.Time >= get_on_arr[i]) & (event_data.Time <= get_off_arr[i]) & (
                event_data.Team == team_name) & (event_data.Event == "助攻")]
        team_scores += (
                len(scores_df[scores_df.Event == "3分球出手"]) * 3 + len(scores_df[scores_df.Event == "2分球出手"]) * 2 + len(
            scores_df[scores_df.Event == "罚球出手"]))
        team_scores += (
                len(get_assist_df[get_assist_df.Info == "3分"]) * 3 + len(get_assist_df[get_assist_df.Info == "2分"]) * 2)

    """计算在场回合数"""
    """
    进攻结束回合标志：被抢断，进攻犯规/违体犯规进攻，失误，进球，对方投篮犯规/普通犯规犯满, 被抢到后场篮板
    """
    for i in range(len(get_on_arr)):
        filtered_event_data = event_data[(event_data.Time >= get_on_arr[i]) & (event_data.Time <= get_off_arr[i])]
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

    # print(name, team_scores, rounds)

    return round(team_scores / rounds * 10, 1)



def get_oncourt_per_loses(name, team_id):
    team_name = team_names[team_id]
    team_name_op = team_names[1 - team_id]
    get_on_arr = sorted(list(
        event_data[(event_data.Team == team_name) & (event_data.Object == name) & (event_data.Event == "换人")]["Time"]))
    get_off_arr = sorted(list(
        event_data[(event_data.Team == team_name) & (event_data.Player == name) & (event_data.Event == "换人")]["Time"]))

    assert (len(get_on_arr) == len(get_off_arr)) or (len(get_on_arr) == len(get_off_arr) + 1)

    if len(get_on_arr) > len(get_off_arr):
        get_off_arr.append(actual_quarter_time * quarters * 60)

    time = 0
    if len(get_on_arr):
        for i in range(len(get_on_arr)):
            time += get_off_arr[i] - get_on_arr[i]
    if time == 0:
        return 0

    op_team_scores = 0
    rounds = 0
    """计算在场得分与失分"""
    for i in range(len(get_on_arr)):
        op_scores_df = event_data[(event_data.Time >= get_on_arr[i]) & (event_data.Time <= get_off_arr[i]) & (
                event_data.Team == team_name_op) & (event_data.Info == "进球")]
        op_get_assist_df = event_data[(event_data.Time >= get_on_arr[i]) & (event_data.Time <= get_off_arr[i]) & (
                event_data.Team == team_name_op) & (event_data.Event == "助攻")]

        op_team_scores += (
                len(op_scores_df[op_scores_df.Event == "3分球出手"]) * 3 + len(
            op_scores_df[op_scores_df.Event == "2分球出手"]) * 2 + len(
            op_scores_df[op_scores_df.Event == "罚球出手"]))
        op_team_scores += (
                len(op_get_assist_df[op_get_assist_df.Info == "3分"]) * 3 + len(
            op_get_assist_df[op_get_assist_df.Info == "2分"]) * 2)

    """计算在场回合数"""
    """
    进攻结束回合标志：被抢断，进攻犯规/违体犯规进攻，失误，进球，对方投篮犯规/普通犯规犯满, 被抢到后场篮板
    减去进攻篮板数增加的回合
    
    #bug 出手后直接出界
    #bug 争球
    #bug 2+1算两回合
    """
    for i in range(len(get_on_arr)):
        filtered_event_data = event_data[(event_data.Time >= get_on_arr[i]) & (event_data.Time <= get_off_arr[i])]
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

    # print(name, op_team_scores, rounds)

    return round(op_team_scores / rounds * 10, 1)


stats()
player_stats_A.set_index('姓名', inplace = True)
player_stats_B.set_index('姓名', inplace = True)

print(player_stats_A)
print(player_stats_B)

# for i in range(len(player_stats_A)):
#     player_stats_A.loc[i,'得分'] = 0

def plot_table(stats, fig, ax, team_name=""):
    plt.rcParams['font.family'] = ['Arial Unicode MS']  # 用黑体显示中文

    row_colors = {
        "top4": "#2d3636",
        "top6": "#516362",
        "playoffs": "#8d9386",
        "relegation": "#c8ab8d",
        "even": "#627979",
        "odd": "#68817e",
    }

    bg_color = row_colors["odd"]
    text_color = "#FFFFFF"

    # fig, ax = plt.subplots()

    fig.set_facecolor(bg_color)
    ax.set_facecolor(bg_color)

    cmap = LinearSegmentedColormap.from_list(
        name="bugw", colors=["#FF0000", "#e0e8df", "#00EE76"], N=256
    )
    cmap_r = LinearSegmentedColormap.from_list(
        name="bugw", colors=["#00EE76", "#e0e8df", "#FF0000"], N=256
    )

    table_cols = ["上场时间", "得分", "篮板", "助攻", "抢断", "盖帽", "2分", "3分", "罚球",
                  "后场+前场篮板", "犯规", "失误", "造成犯规", "效率值", "在场得分(10回合)", "在场失分(10回合)"]

    table_col_defs = [
        ColDef("姓名", width=1.3, textprops={"ha": "left", "weight": "bold"}, title=team_name),
        ColDef("上场时间", width=0.8),
        ColDef("得分", width=0.5),
        ColDef("助攻", width=0.5),
        ColDef("篮板", width=0.5),
        ColDef("抢断", width=0.5),
        ColDef("盖帽", width=0.5),
        ColDef("2分", width=0.5),
        ColDef("3分", width=0.5),
        ColDef("罚球", width=0.5),
        ColDef("后场+前场篮板", width=0.8, title="后场+\n前场篮板"),
        ColDef("被犯规", width=0.8),
        ColDef("犯规", width=0.5),
        ColDef("失误", width=0.5),
        ColDef("效率值", width=0.5, text_cmap=normed_cmap(stats["效率值"], cmap=cmap, num_stds=2)),
        ColDef("在场得分(10回合)", width=1.0, title="在场得分\n(10回合)",
               text_cmap=normed_cmap(stats["在场得分(10回合)"], cmap=cmap, num_stds=2)),
        ColDef("在场失分(10回合)", width=1.0, title="在场失分\n(10回合)",
               text_cmap=normed_cmap(stats["在场失分(10回合)"], cmap=cmap_r, num_stds=2))
    ]

    tab = Table(stats,
          ax= ax,
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
          textprops={"fontsize": 15, "ha": "center"}, )
    return tab

plt.rcParams["text.color"] = "#e0e8df"
plt.rcParams['font.sans-serif'] = ['MFGeHeiNoncommercial']


# fig = plt.figure(num=1, figsize=(20, 10),dpi=80)
#
# ax1 = fig.add_subplot(2,1,1)
# ax2 = fig.add_subplot(2,1,2)
#
# table1 = plot_table(player_stats_A, fig, ax1, team_names[0])
# table2 = plot_table(player_stats_B, fig, ax2, team_names[1])
#
#
# plt.rcParams['font.sans-serif'] = ['MFGeHeiNoncommercial']
# plt.title(label="{} {} {}\n___________________________________________________________________________________________________".format(team_names[0], scores, team_names[1]),
#           fontsize=25,
#           fontweight="bold",
#           color="#e0e8df",
#           y=2.22)
# # plt.rcParams["text.color"] = "#000000"
# plt.suptitle("8月8日 ABL篮球馆 {} JUSHOOP".format(61 * "   "), fontsize=19, color='#e0e8df', x=0.5, y=0.94, fontweight="bold")
# # logo = Image.open('logo1.png')
# # plt.imshow(logo)
# for font in matplotlib.font_manager.fontManager.ttflist:
#     print(font.name, '-', font.fname)
# matplotlib.pyplot.subplots_adjust(left=0.02, bottom=0.001, right=0.982, top=0.893)


# plt.show()

fig, ax = plt.subplots(figsize=(20, 10),dpi=80)
table = plot_table(player_stats_A, fig, ax, team_names[0])
# table = plot_table(player_stats_B, fig, ax, team_names[1])
plt.rcParams['font.sans-serif'] = ['MFGeHeiNoncommercial']
plt.title(label="{} {} {}\n___________________________________________________________________________________________________".format(team_names[0], scores, team_names[1]),
          fontsize=25,
          fontweight="bold",
          color="#e0e8df",
          y=1)
# plt.rcParams["text.color"] = "#000000"
plt.suptitle("8月25日 ABL篮球馆 {} JUSHOOP".format(61 * "   "), fontsize=19, color='#e0e8df', x=0.5, y=0.94, fontweight="bold")
# logo = Image.open('logo1.png')
# plt.imshow(logo)
# for font in matplotlib.font_manager.fontManager.ttflist:
#     print(font.name, '-', font.fname)
matplotlib.pyplot.subplots_adjust(left=0.02, bottom=0.001, right=0.982, top=0.893)
plt.show()
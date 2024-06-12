import json
import pandas as pd
from stats_model import auto_select_stats_model
from highlight_model import BaseHighlightModelFast
from dewu import DewuVideoUploader, get_tags, get_cookies
# from
import os
import argparse
import shutil
import random


def multi_process_highlight_func(i, data_dir, music_path, font_path, logo_path, target_stats, add_cover=True, video_dir_postfix=""):
    hlc = BaseHighlightModelFast(data_dir, font_path, logo_path, video_dir_postfix=video_dir_postfix)
    num_teams = hlc.basketball_events.num_teams
    if i < num_teams:
        hlc.get_all_players_highlights(i, music_path=music_path, target_stats=target_stats, add_cover=add_cover)
    elif i == num_teams:
        # if hlc.config["match_type"] == "球局":
        #     hlc.get_all_in_one_highlight(music_path=music_path)
        if hlc.config["match_type"] == "友谊赛":
            hlc.get_team_highlight(0, music_path=music_path)
    elif i == num_teams + 1:
        if hlc.config["match_type"] == "友谊赛":
            hlc.get_team_highlight(1, music_path=music_path)
    else:
        pass


def highlight(arg, target_stats=("scores", "assists", "blocks"), add_cover=True, video_dir_postfix=""):
    hlc = BaseHighlightModelFast(arg.data_dir, arg.font_path, arg.logo_path, video_dir_postfix=video_dir_postfix)

    hlc.get_all_highlights(music_path=get_music(args), target_stats=target_stats, add_cover=add_cover)

def get_music(args):
    music_path = args.music_path
    music_dir = args.music_dir

    if music_path == "random":
        musics = os.listdir(music_dir)
        musics = [os.path.join(music_dir, music) for music in musics if music[0] != "."]
        # print(musics)
        return musics
    else:
        return music_path


def multi_process_highlight(arg, target_stats=("scores", "assists", "blocks"), add_cover=True, video_dir_postfix=""):
    import multiprocessing

    processes = []
    for i in range(6):
        p = multiprocessing.Process(target=multi_process_highlight_func,args=(i, arg.data_dir, get_music(args), arg.font_path, arg.logo_path, target_stats, add_cover, video_dir_postfix))
        p.start()
        processes.append(p)

    for p in processes:
        p.join()

def get_stats(args):
    config = json.load(open(os.path.join(args.data_dir, "config.json"), encoding='utf-8'))
    event_data = pd.read_csv(os.path.join(args.data_dir, "events.csv"), )
    event_data = event_data.fillna("")
    stats_model = auto_select_stats_model(event_data, config)
    stats_model.get_stats()
    for i in range(stats_model.num_teams):
        stats_model.plot_stats_single_team(i, show=False, save=args.data_dir)


def dewu_post(video_dir, channels_set):
    dewu_model = DewuVideoUploader()
    video_names = []
    team_video_names = []

    tags = get_tags(["上海村BA开打", "我在得物打篮球", "AllyGo"])
    # tags = get_tags(["AllyGo"])

    court_name = video_dir.split("_")[-1]

    team_names = os.listdir(video_dir)
    team_names = [name for name in team_names if name[0] != '.']
    for team_name in team_names:
        if not os.path.isdir(os.path.join(video_dir, team_name)):
            continue
        if not team_name.endswith("dewu"):
            continue
        video_names_team = os.listdir(os.path.join(video_dir, team_name))
        if video_names_team == '.':
            continue
        print(video_names_team)
        for video_name in video_names_team:
            if video_name[0] == ".":
                continue
            team_video_names.append(team_name)
            video_names.append(video_name)

    # print(video_names)

    for i, video_name in enumerate(video_names):

        # video_name = video_names[i]
        player_name = video_name.split(".")[0].split('_')[-1]
        if player_name == "all":
            continue
        team_name = team_video_names[i]

        file_name = os.path.join(video_dir, team_name, video_name)

        if player_name == team_name:
            continue
        # print("")
        if team_name.endswith("_dewu"):
            team_name = team_name[:-5]
            if team_name in ["黑队", "白队", "Team A", "Team B", "Team C", "Team D"]:
                team_name = f"{court_name}分站赛"
            else:
                team_name = f"{team_name}队"
        title = f"上海村BA来袭! 一起来看{team_name}{player_name}精彩集锦!"

        des = f"一起来看村BA上海赛区{team_name}{player_name}精彩集锦。 村BA上海赛区由AllyGo赞助、JUSHOOP提供AI集锦服务，参与村BA即能免费获得精彩集锦，还能角逐得物提供的球鞋奖励，快来参与吧！"

        cookies = get_cookies(channels_set, "random")


        # print(title)
        # print(des)
        tmp_file = "./tmp.mp4"
        tmp_file = os.path.abspath(tmp_file)
        print(title, des)
        print(file_name, tmp_file)
        shutil.move(file_name, tmp_file)
        # # print(file_name, channel, title, des, tags)
        # # print(os.path.exists(file_name))
        # # print(type(file))
        # # print("\n")
        #
        dewu_model.upload(tmp_file, cookies, title, des, tags)
        shutil.move(tmp_file, file_name)
    dewu_model.close()
        # break



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run Example')
    parser.add_argument('data_dir', type=str, help='path of config file')
    parser.add_argument('-music_path', type=str, default=None, help='path of config file')
    parser.add_argument('-font_path', type=str, default="dream.ttf", help='path of font file')
    parser.add_argument('-logo_path', type=str, default="logo4.png", help='path of logo file')
    parser.add_argument('-single_process', action="store_true", default=False, help='单线程执行')
    parser.add_argument('-no_cover', action="store_true", default=False, help='不生成封面')
    parser.add_argument('-stats', action="store_true", default=False, help='只生成数据')
    parser.add_argument('-highlight', action="store_true", default=False, help='只生成集锦')
    parser.add_argument('-dewu', action="store_true", default=False, help='发布得物视频')
    parser.add_argument("-dewu_club", type=str, default=None, help='本次发布的俱乐部名字')
    parser.add_argument("-music_dir", type=str, default='musics/', help='随机音乐的曲库')
    args = parser.parse_args()

    target_stats = ["scores", "assists", "blocks"] # 个人集锦中展示的内容


    if not args.dewu:
        get_stats(args)
        if args.single_process:
            highlight(args, target_stats, not args.no_cover)
        else:
            multi_process_highlight(args, target_stats, not args.no_cover)
    else:
        if args.music_path is None:
            print("发布得物的视频需要指定音乐, 请用-music_path指定")
            raise ValueError()
        args.logo_path=None
        if args.single_process:
            highlight(args, target_stats, not args.no_cover, video_dir_postfix="_dewu")
        else:
            multi_process_highlight(args, target_stats, not args.no_cover, video_dir_postfix="_dewu")

        channels_set = ["main"]
        # channels_set = ["main", "random"]

        dewu_post(args.data_dir, channels_set)

# tmp = events.event_data[1 & (events.event_data.Player != "MARKO") & (events.event_data.Event == "助攻")]
# print(tmp)
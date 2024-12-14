import json
import pandas as pd
from stats_model import auto_select_stats_model
from highlight_model import BaseHighlightModelFast
from dewu import DewuVideoUploader, get_cookies, descriptions, titles
from cunba_stats import post_stats
# from
import os
import argparse
import shutil
import random
from tqdm import tqdm


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


def highlight(arg, target_stats=("scores", "assists", "blocks"), add_cover=True, video_dir_postfix="", filtrate=False, duration=None):
    hlc = BaseHighlightModelFast(arg.data_dir, arg.font_path, arg.logo_path, video_dir_postfix=video_dir_postfix, duration=duration)
    hlc.get_all_highlights(music_path=get_music(args), target_stats=target_stats, add_cover=add_cover, filtrate=filtrate)
   
    # hlc.get_all_team_tos_highlight()   # 全队失误集锦
    # hlc.get_all_players_missed_highlight()   # 个人打铁集锦
    # hlc.get_all_in_one_highlight()   # 全场集锦
    # hlc.get_special_highlight() # 精彩绝伦&有点小帅


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
    try:
        title = config["title"]
    except:
        title = None
    for i in range(stats_model.num_teams):
        stats_model.plot_stats_single_team(i, show=False, save=args.data_dir, title=title)
    if config["match_type"] == "友谊赛":
        stats_model.plot_stats_both_team(show=False, save=args.data_dir, title=title)
        stats_model.save_table_file(save=args.data_dir)

    if args.post_data:
        post_stats(args.data_dir, config)

def dewu_post(video_dir, channels_set):
    dewu_model = DewuVideoUploader()
    video_names = []
    team_video_names = []

    tags = ['上海就是打球联赛', '专业护膝来袭', '球场上的保护神', '得物看看我是几档球员', '寻找篮球未来之星']


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

        # print("")
        if team_name.endswith("_dewu"):
            team_name = team_name[:-5]
            if team_name in ["黑队", "白队", "Team A", "Team B", "Team C", "Team D"]:
                team_postfix = ""
                team_name = ""
            elif team_name.endswith("队"):
                team_postfix = ""
            else:
                team_postfix = "队"
                # team_name = f"{team_name}队"

        rand_res = random.randint(0, len(titles)-1)
        title = titles[rand_res]
        des = descriptions[rand_res]
        if player_name in team_name: # 球队集锦
            if team_name == "" and team_postfix == "":
                continue
            title += f"一起来看{team_name}{team_postfix}精彩集锦!"
        else:
            title += f"一起来看{team_name}{team_postfix}{player_name}精彩集锦!"


        des += f"参与上海迈克达威-就是打球联赛，你也能获得专属帅气集锦，快来参与吧！"

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

def cunba_batch_highlight(args):
    finished = []

    # 卡住
    # problemed1 = ["20240925_河南沁阳星锐_宁夏吴忠教育", "20240925_宁夏吴忠教育_辽宁大连中源牧业", "20241001_四川成都米兰世家_甘肃肃北雪域先锋", "20240825_湖南道县好百年_吉林好空气", "20240925_辽宁大连中源牧业_黑龙江宝清", "20241002_江西南康家具队_四川成都米兰世家", "20240823_吉林新空气_宁夏吴忠市", "20241002_甘肃临夏州_广西德保矮马", "20241003_山东东营汇东集团_广西德保矮马", "20240925_黑龙江宝清_河北黄儿营"]
    problemed2 = ["20240920_甘肃肃北雪域先锋_安徽芜湖六郎", "20240823_吉林新空气_宁夏吴忠市", "20240925_辽宁大连中源牧业_黑龙江宝清", "20241002_甘肃临夏州_广西德保矮马", "20240810_山西翼城凤翔园林_贵州黑今骑士", 
                  "20241003_山东东营汇东集团_广西德保矮马", "20241002_江西南康家具队_四川成都米兰世家", "20241004_甘肃临夏州_山东东营汇东集团", "20241004_安徽蚌埠胡巷_广西德保矮马",
                  "20241003_甘肃临夏州_安徽蚌埠胡巷", "20240913_广东湾区商学院_浙江千年永宁"] # 视频数据对不上

    problemed = [] + problemed2
    root_dir = args.data_dir
    args.logo_path = "logo8.png"

    for match_name in tqdm(os.listdir(args.data_dir)):
        print(match_name)
        if match_name in (finished + problemed) or match_name.startswith("."):
            continue
        args.data_dir = os.path.join(root_dir, match_name)
        cunba_highlight(args)



    

def cunba_highlight(args):
    from oss import client, M3u8Parser
    import requests
    parser = M3u8Parser()
    config = json.load(open(os.path.join(args.data_dir, "config.json"),encoding='utf-8'))
    match_id = config['match_id']

    r = eval(requests.get(url=f"http://jushoop1977.com/api/get-inside-id/{match_id}").text)

    code = r['code']
    match_id = r["data"]

    play_list = client.get_play_list(f"{match_id}", "vod")
    if play_list is None:
        print("获取播放列表失败")
        print(args.data_dir)
        return
    parser.parse_string(play_list, merge=False)
    parser.export_file(os.path.join(args.data_dir, "1.m3u8"), f'http://jushoop-live-videos.oss-cn-shanghai-internal.aliyuncs.com/{match_id}/', export_type="vod")

    args.logo_path = "logo8.png"
    highlight(args, target_stats, not args.no_cover, filtrate=True, duration=int(parser.duration))
    



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run Example')
    parser.add_argument('data_dir', type=str, help='path of config file')
    parser.add_argument('-music_path', type=str, default=None, help='path of config file')
    parser.add_argument('-font_path', type=str, default="dream.ttf", help='path of font file')
    parser.add_argument('-logo_path', type=str, default="logo.png", help='path of logo file')
    parser.add_argument('-single_process', action="store_true", default=False, help='单线程执行')
    parser.add_argument('-no_cover', action="store_true", default=False, help='不生成封面')
    parser.add_argument('-stats', action="store_true", default=False, help='只生成数据')
    parser.add_argument('-highlight', action="store_true", default=False, help='只生成集锦')
    parser.add_argument('-cunba', action="store_true", default=False, help='贵州村ba，云端下载视频')
    parser.add_argument('-cunba_batch', action="store_true", default=False, help='贵州村ba批量处理，云端下载视频')
    parser.add_argument('-dewu', action="store_true", default=False, help='发布得物视频')
    parser.add_argument('-dewu_no_run', action="store_true", default=False, help='直接发布得物视频，不重新生成')
    parser.add_argument('-dewu_no_run_batch', action="store_true", default=False, help='批量发布得物视频，不重新生成')
    parser.add_argument("-music_dir", type=str, default='musics/', help='随机音乐的曲库')
    parser.add_argument("-post_data", action="store_true", default=False, help='随机音乐的曲库')
    args = parser.parse_args()

    target_stats = ["scores", "assists", "blocks"] # 个人集锦中展示的内容

    if args.cunba:
        cunba_highlight(args)
        exit()
    if args.cunba_batch:
        cunba_batch_highlight(args)
        exit()
    if (not args.dewu and not args.dewu_no_run and not args.dewu_no_run_batch):
        if not args.highlight:
            get_stats(args)
        if not args.stats:
            if args.single_process:
                highlight(args, target_stats, not args.no_cover)
            else:
                multi_process_highlight(args, target_stats, not args.no_cover)
    else:
        args.music_path = "random"
        # channels_set = ["test"]
        channels_set = ["main", "random"]

        if args.dewu:
            highlight(args, target_stats, not args.no_cover, video_dir_postfix="_dewu", filtrate=False)
            dewu_post(args.data_dir, channels_set)
        elif args.dewu_no_run:
            file_names = os.listdir(args.data_dir)
            for file_name in file_names:
                print(file_name)
                if os.path.isdir(os.path.join(args.data_dir, file_name)):
                    os.rename(os.path.join(args.data_dir, file_name), os.path.join(args.data_dir, f"{file_name}_dewu"))
            dewu_post(args.data_dir, channels_set)
        elif args.dewu_no_run_batch:
            target_dirs = os.listdir(args.data_dir)
            for target_dir in target_dirs:
                target_dir = os.path.join(args.data_dir, target_dir)
                if os.path.isdir(target_dir):
                    file_names = os.listdir(target_dir)
                    for file_name in file_names:
                        print(file_name)
                        if os.path.isdir(os.path.join(target_dir, file_name)):
                            os.rename(os.path.join(target_dir, file_name), os.path.join(target_dir, f"{file_name}_dewu"))
                    dewu_post(target_dir, channels_set)

        
        


# tmp = events.event_data[1 & (events.event_data.Player != "MARKO") & (events.event_data.Event == "助攻")]
# print(tmp)
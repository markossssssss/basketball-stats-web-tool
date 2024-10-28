import json
import pandas as pd
from moviepy.editor import VideoFileClip
import os
from stats_model import auto_select_stats_model
from PIL import ImageDraw, ImageFont, Image, ImageEnhance
import subprocess
import bisect
import random
from better_ffmpeg_progress import FfmpegProcess



HIGHLIGHT_PLAYTIME_DICT = {"进球": (6, 2), "盖帽": (3, 2), "助攻": (7, 3), "抢断": (2, 3), "3分": (4, 4), "4分": (4, 4), "2分": (4, 4),
                           "篮板": (3, 3), "不进": (6, 3), "失误": (4, 3), "囧": (4, 4)}

DATA_ON_COVER_BASELINE = {"得分": 1, "助攻": 1, "篮板": 1, "抢断": 1, "盖帽": 1, "真实命中率": 0.45, "效率值": 8}

class BaseHighlightModelFast():
    def __init__(self, game_dir, font_path=None, logo_path=None, video_dir_postfix=""):
        self.config = json.load(open(os.path.join(game_dir, "config.json"),encoding='utf-8'))
        self.game_dir = game_dir

        event_data = pd.read_csv(os.path.join(game_dir, "events.csv"))
        event_data = event_data.fillna("")
        self.basketball_events = auto_select_stats_model(event_data, self.config)
        self.basketball_events.get_stats()
        
        self.quarter_video_lens = []
        self.videos = []

        self.font_path = font_path
        self.logo_path = logo_path

        video_postfixes = ['mp4', 'mov', 'MP4', 'MOV', 'avi', 'AVI']
        self.postfix = None
        for postfix in video_postfixes:
            if os.path.exists(os.path.join(game_dir, f"1.{postfix}")):
                self.postfix = postfix
                break
        
        if self.postfix is None:
            raise Exception("请检查视频名".format(game_dir))
        
        self.target_postfix = self.postfix
        
        for i in range(1, self.config["quarters"] + 1):
            tmp_clip = os.path.join(game_dir, f"{i}.{self.postfix}")
            self.videos.append(tmp_clip)
            self.quarter_video_lens.append(get_video_duration(tmp_clip))

        check_video_info_and_reencode(self.videos)
        
        self.default_target_stats = ["scores", "assists", "blocks"]

        
        self.team_names = self.basketball_events.team_names
        self.num_teams = len(self.team_names)

        self.init_team_highlight_data()
        self.init_player_highlight_data()
        self.init_negative_stats()
        self.init_fool_data()

        self.negative_data = event_data[(event_data.Info == "不进") | (event_data.Event == "失误") | (event_data.Event == "抢断") | (event_data.Event == "盖帽")]
        self.highlight_data = event_data[(event_data.Event == "囧") |
            (event_data.Event == "抢断") | (event_data.Event == "篮板") | (event_data.Event == "盖帽") | (
                    event_data.Event == "助攻") | ((event_data.Info == "进球") & (event_data.Event == "4分球出手")) | ((event_data.Info == "进球") & (event_data.Event == "3分球出手")) | (
                    (event_data.Info == "进球") & (event_data.Event == "2分球出手"))]
        self.delete_data = event_data[(event_data.Event == "highlight") | (event_data.Info == "bad")]

        self.parse_team_highlight()
        self.parse_negative_highlight()
        self.parse_fool_highlight()

        self.last_parsed_stats = None
        self.video_dir_postfix = video_dir_postfix


        for i in range(self.num_teams):
            if not os.path.exists(os.path.join(self.game_dir, f"{self.team_names[i]}{self.video_dir_postfix}")):
                        os.mkdir(os.path.join(self.game_dir, f"{self.team_names[i]}{self.video_dir_postfix}"))


    def init_team_highlight_data(self):
        self.collections_whole_team = [TeamHighLightCollection(self.team_names[i]) for i in range(self.num_teams)]
        self.highlight_all_teams = TeamHighLightCollection(self.team_names[0])
        
    def init_fool_data(self):
        self.fool_highlight_whole_team = TeamHighLightCollection(self.team_names[0])

    def init_player_highlight_data(self):
        self.collections_team_players = [
            {name: PlayerHighLightCollection(self.team_names[i], name) for name in self.basketball_events.player_names[i]} for i in range(self.num_teams)]

    def init_negative_stats(self):
        self.missed_collections_team_players = [
            {name: PlayerHighLightCollection(self.team_names[i], name) for name in self.basketball_events.player_names[i]} for i in range(self.num_teams)]
        self.missed_collections_whole_team = [TeamHighLightCollection(self.team_names[i]) for i in range(self.num_teams)]

        self.tos_collections_team_players = [
            {name: PlayerHighLightCollection(self.team_names[i], name) for name in self.basketball_events.player_names[i]} for i in range(self.num_teams)]
        self.tos_collections_whole_team = [TeamHighLightCollection(self.team_names[i]) for i in range(self.num_teams)]



    def parse_fool_highlight(self):
        for i, r in self.highlight_data.iterrows():
            if r["Event"] == "囧":
                self.fool_highlight_whole_team.add(HighLight(r["Event"], r["Quarter"], r["OriginQuarterTime"]))
           
                
    def parse_team_highlight(self):
        for i, r in self.highlight_data.iterrows():
            # print(r)
            team_idx = self.team_names.index(r["Team"])

            """球队集锦，目前版本默认进球+盖帽，不可选"""

            if r["Info"] == "进球" or r["Event"] == "盖帽":
                self.collections_whole_team[team_idx].add(HighLight(r["Info"], r["Quarter"], r["OriginQuarterTime"]))
                self.highlight_all_teams.add(HighLight(r["Info"], r["Quarter"], r["OriginQuarterTime"]))
            elif r["Event"] == "助攻":
                self.collections_whole_team[team_idx].add(HighLight(r["Info"], r["Quarter"], r["OriginQuarterTime"]))
                self.highlight_all_teams.add(HighLight(r["Info"], r["Quarter"], r["OriginQuarterTime"]))

    def find_team(self, player):
        for team_idx, players in enumerate(self.basketball_events.player_names):
            if player in players:
                return team_idx
        raise Exception

    def parse_player_highlight(self, target_stats=None):
        target_stats = self.get_target_stats(target_stats)
        # print(target_stats)
        if self.last_parsed_stats is None or self.last_parsed_stats != target_stats:
            for i, r in self.highlight_data.iterrows():
                team_idx = self.team_names.index(r["Team"])

                """球队集锦，可选得分、助攻、盖帽、抢断、篮板"""
                try:
                    if r["Info"] == "进球" and "scores" in target_stats:
                        self.collections_team_players[team_idx][r["Player"]].add(
                            HighLight(r["Info"], r["Quarter"], r["OriginQuarterTime"]))

                    if r["Event"] == "助攻" and "assists" in target_stats:
                        self.collections_team_players[team_idx][r["Player"]].add(
                            HighLight(r["Event"], r["Quarter"], r["OriginQuarterTime"]))
    
                    if r["Event"] == "助攻" and "scores" in target_stats:
                        self.collections_team_players[team_idx][r["Object"]].add(
                            HighLight(r["Info"], r["Quarter"], r["OriginQuarterTime"]))
    
                    if r["Event"] == "篮板" and "rebounds" in target_stats:
                        self.collections_team_players[team_idx][r["Player"]].add(
                            HighLight(r["Event"], r["Quarter"], r["OriginQuarterTime"]))
    
                    if r["Event"] == "抢断" and "steals" in target_stats:
                        self.collections_team_players[team_idx][r["Player"]].add(
                            HighLight(r["Event"], r["Quarter"], r["OriginQuarterTime"]))
    
                    if r["Event"] == "盖帽" and "blocks" in target_stats:
                        self.collections_team_players[team_idx][r["Player"]].add(
                            HighLight(r["Event"], r["Quarter"], r["OriginQuarterTime"]))
                except Exception as e:
                    try:
                        # 说明别队的人被本队的人助攻了
                        self.collections_team_players[self.find_team(r["Object"])][r["Object"]].add(
                            HighLight(r["Info"], r["Quarter"], r["OriginQuarterTime"]))
                    except Exception as e:
                        print(e)
                        print("跳过{}集锦片段".format(r["Player"]))
                        print(r)
                        continue

            self.last_parsed_stats = target_stats
    
    def _get_team_idx(self, player_name):
        for i, names in enumerate(self.basketball_events.player_names):
            if player_name in names:
                return i
        
    def parse_negative_highlight(self):
        for i, r in self.negative_data.iterrows():
            team_idx  = self.team_names.index(r["Team"])
            obj_team_idx = self._get_team_idx(r["Object"])
            if r["Info"] == "不进":
                self.missed_collections_team_players[team_idx][r["Player"]].add(
                    HighLight(r["Info"], r["Quarter"], r["OriginQuarterTime"]))
                self.missed_collections_whole_team[team_idx].add(
                    HighLight(r["Info"], r["Quarter"], r["OriginQuarterTime"]))
            if r["Event"] == "失误":
                self.tos_collections_team_players[team_idx][r["Player"]].add(
                    HighLight(r["Event"], r["Quarter"], r["OriginQuarterTime"]))
                self.tos_collections_whole_team[team_idx].add(
                    HighLight(r["Event"], r["Quarter"], r["OriginQuarterTime"]))
            if r["Event"] == "抢断":
                self.tos_collections_team_players[obj_team_idx][r["Object"]].add(
                    HighLight(r["Event"], r["Quarter"], r["OriginQuarterTime"]))
                self.tos_collections_whole_team[obj_team_idx].add(
                    HighLight(r["Event"], r["Quarter"], r["OriginQuarterTime"]))
            if r["Event"] == "盖帽":
                self.missed_collections_team_players[obj_team_idx][r["Object"]].add(
                    HighLight(r["Event"], r["Quarter"], r["OriginQuarterTime"]))
                self.missed_collections_whole_team[obj_team_idx].add(
                    HighLight(r["Event"], r["Quarter"], r["OriginQuarterTime"]))


    def get_target_stats(self, target_stats):
        if target_stats is None:
            return self.default_target_stats
        return target_stats


    def get_team_highlight(self, team_idx, music_path=None):
        if music_path is not None:
            if type(music_path) == list:
                music_path = random.choice(music_path)
        team = self.team_names[team_idx]
        target_path = os.path.join(self.game_dir, f"{team}{self.video_dir_postfix}", "highlight_{}.mp4".format(team))
        self.collections_whole_team[team_idx].download_highlight(self.videos, self.quarter_video_lens, music_path, target_path)
        del_file(os.path.join(self.game_dir, self.team_names[team_idx]), "ts", self.video_dir_postfix)
        
    def get_all_in_one_highlight(self, music_path=None):
        if music_path is not None:
            if type(music_path) == list:
                music_path = random.choice(music_path)
        target_path = os.path.join(self.game_dir, f"{self.team_names[0]}{self.video_dir_postfix}", "highlight_all.mp4")
        self.highlight_all_teams.download_highlight(self.videos, self.quarter_video_lens, music_path, target_path)
        del_file(os.path.join(self.game_dir, self.team_names[0]), "ts", self.video_dir_postfix)

        

    def get_fool_highlight(self, music_path=None):
        if music_path is not None:
            if type(music_path) == list:
                music_path = random.choice(music_path)
        target_path = os.path.join(self.game_dir, "fool.mp4")
        self.fool_highlight_whole_team.download_highlight(self.videos, self.quarter_video_lens, music_path, target_path)

    def get_player_highlight(self, team, player, target_stats=None, music_path=None, add_cover=True):
        if music_path is not None:
            if type(music_path) == list:
                music_path = random.choice(music_path)
        self.parse_player_highlight(target_stats)
        target_path = os.path.join(self.game_dir, f"{team}{self.video_dir_postfix}", f"highlight_{player}.{self.target_postfix}")
        team_idx = self.team_names.index(team)
        # print(self.videos, self.quarter_video_lens, music_path, target_path)

        video_path = self.collections_team_players[team_idx][player].download_highlight(self.videos, self.quarter_video_lens, music_path, target_path)
        if video_path:
            self.collections_team_players[team_idx][player].add_video_cover(self.basketball_events.player_stats[team_idx], video_path, get_cover=add_cover, font_path=self.font_path, music_path=music_path, logo_path=self.logo_path, match_date=self.basketball_events.match_date, match_place=self.basketball_events.court_name, match_time=self.basketball_events.match_time)


    def get_player_missed_highlight(self, team, player, music_path=None):
        if music_path is not None:
            if type(music_path) == list:
                music_path = random.choice(music_path)
        target_path = os.path.join(self.game_dir, f"{team}{self.video_dir_postfix}", f"missed_{player}.{self.target_postfix}")
        team_idx = self.team_names.index(team)
        # print(self.videos, self.quarter_video_lens, music_path, target_path)

        self.missed_collections_team_players[team_idx][player].download_highlight(self.videos, self.quarter_video_lens, music_path, target_path)
        del_file(os.path.join(self.game_dir, self.team_names[team_idx]), "ts", self.video_dir_postfix)


    def get_all_team_tos_highlight(self, music_path=None):
        for team in self.team_names:
            target_path = os.path.join(self.game_dir, f"{team}{self.video_dir_postfix}", f"{team}_失误.{self.target_postfix}")
            team_idx = self.team_names.index(team)
            self.tos_collections_whole_team[team_idx].download_highlight(self.videos, self.quarter_video_lens, music_path, target_path)
            del_file(os.path.join(self.game_dir, self.team_names[team_idx]), "ts", self.video_dir_postfix)


    def get_all_teams_highlights(self, music_path=None):
        for i in range(self.num_teams):
            music_path_new=music_path
            if music_path is not None:
                if type(music_path) == list:
                    music_path_new = random.choice(music_path)

            target_path = os.path.join(self.game_dir, f"{self.team_names[i]}{self.video_dir_postfix}", f"highlight_{self.team_names[i]}.{self.target_postfix}")
            self.collections_whole_team[i].download_highlight(self.videos, self.quarter_video_lens, music_path_new, target_path)
        for i in range(len(self.team_names)):
            del_file(os.path.join(self.game_dir, self.team_names[i]), "ts", self.video_dir_postfix)

    def get_all_players_highlights(self, team_id, music_path=None, target_stats=None, add_cover=True):
        self.parse_player_highlight(target_stats)
        # print(team_id)
        # print(self.basketball_events.player_stats)
        if team_id is not None:
            for name in self.collections_team_players[team_id]:
                music_path_new = music_path
                if music_path is not None:
                    if type(music_path) == list:
                        music_path_new = random.choice(music_path)
                target_path = os.path.join(self.game_dir, f"{self.team_names[team_id]}{self.video_dir_postfix}", f"highlight_{name}.{self.target_postfix}")
                video_path = self.collections_team_players[team_id][name].download_highlight(self.videos, self.quarter_video_lens, music_path_new, target_path)
                if video_path:
                    self.collections_team_players[team_id][name].add_video_cover(self.basketball_events.player_stats[team_id], video_path, get_cover=add_cover, font_path=self.font_path, music_path=music_path_new, logo_path=self.logo_path, match_date=self.basketball_events.match_date, match_place=self.basketball_events.court_name, match_time=self.basketball_events.match_time)
        for i in range(len(self.team_names)):
            del_file(os.path.join(self.game_dir, self.team_names[i]), "ts", self.video_dir_postfix)


    def get_all_players_missed_highlight(self):
        for team_id, team in enumerate(self.team_names):
            for player in self.collections_team_players[team_id]:
                target_path = os.path.join(self.game_dir, f"{team}{self.video_dir_postfix}", f"missed_{player}.{self.target_postfix}")
                self.missed_collections_team_players[team_id][player].download_highlight(self.videos, self.quarter_video_lens, None, target_path)
            del_file(os.path.join(self.game_dir, self.team_names[team_id]), "ts", self.video_dir_postfix)


    def get_all_highlights(self, music_path=None, target_stats=None, add_cover=True, filtrate=False):
        if filtrate: 
            target_stats = ["scores", "blocks"]
        self.parse_player_highlight(target_stats)
        for team_id in range(self.num_teams):
            for name in self.collections_team_players[team_id]:
                if filtrate: 
                    if self.basketball_events.player_stats[team_id]["得分"][name] < 6:
                        continue
                music_path_new = music_path
                if music_path is not None:
                    if type(music_path) == list:
                        music_path_new = random.choice(music_path)
                target_path = os.path.join(self.game_dir, f"{self.team_names[team_id]}{self.video_dir_postfix}", f"highlight_{name}.{self.target_postfix}")
                video_path = self.collections_team_players[team_id][name].download_highlight(self.videos, self.quarter_video_lens, music_path_new, target_path)
                if video_path:
                    self.collections_team_players[team_id][name].add_video_cover(self.basketball_events.player_stats[team_id], video_path, get_cover=add_cover, font_path=self.font_path, music_path=music_path_new, logo_path=self.logo_path, match_date=self.basketball_events.match_date, match_place=self.basketball_events.court_name, match_time=self.basketball_events.match_time)

        # if self.config["match_type"] == "球局":
        #     self.get_all_in_one_highlight(music_path=music_path)

        if self.config["match_type"] == "友谊赛":
            self.get_all_teams_highlights(music_path=music_path)
        # self.get_all_team_tos_highlight()
        # self.get_all_players_missed_highlight()
        for i in range(len(self.team_names)):
            del_file(os.path.join(self.game_dir, self.team_names[i]), "ts", self.video_dir_postfix)



class TeamHighLightCollection():
    def __init__(self, team):
        self.data = []
        self.team = team

    def add(self, highlight):
        self.data.append(highlight)

    def __len__(self):
        return len(self.data)
        

    def download_highlight(self, videos, quarter_video_lens, music_path=None, result_path=None):
        if result_path is not None:
            print(f'generating: {result_path}')
        if not (len(self.data)):
            return 0
        
        clips = []
        for highlight in self.data:
            clips.append(highlight.clip_video(videos, quarter_video_lens, os.path.dirname(result_path)))



        final_clip = concatenate_clips(result_path, clips, delete_clips=True)

        return final_clip

class PlayerHighLightCollection(TeamHighLightCollection):
    def __init__(self, team, name):
        super().__init__(team)
        self.name = name

    def get_player_stat_txt(self, data_series):
        txt = []
        txt.append(f"{self.name} 个人集锦")
        txt.append(" \n")
        target_data = []
        keys = ["得分", "篮板", "助攻", "抢断", "盖帽", "真实命中率", "效率值"]
        for key in keys:
            baseline = DATA_ON_COVER_BASELINE[key]
            if data_series[key] >= baseline:
                target_data.append([data_series[key], key])
        current_count = 0
        txt_line = ""
        for i, data in enumerate(target_data):
            data_string = get_data_sting(data[1], data[0])
            current_count += 1
            if len(target_data) >= 4 and current_count == (len(target_data) - len(target_data)//2):
                txt_line += data_string
                txt.append(txt_line)
                txt_line = ""
            else:
                txt_line += f"{data_string} "
        txt.append(txt_line)

        return txt

    def add_video_cover(self, team_data_df, input_video_path, get_cover=True, font_path=None, music_path=None, logo_path=None, match_date=None, match_place=None, match_time=None):
        if get_cover:
            main_txt = self.get_player_stat_txt(team_data_df.loc[self.name])
            top_text = match_date
            if match_time is not None:
                bottom_text = f"{match_place} {match_time}"
            else:
                bottom_text = match_place
            edit_video(input_video_path, add_cover=get_cover, logo_path=logo_path, main_text=main_txt, font_path=font_path, top_text=top_text, bottom_text=bottom_text, add_music=True if music_path is not None else False, music_path=music_path, replace=True)
            
            
def get_data_sting(data_term, value):
    if data_term == "得分":
            return f"{value}分"
    elif data_term == "篮板":
            return f"{value}篮板"
    elif data_term == "助攻":
            return f"{value}助攻"
    elif data_term == "抢断":
            return f"{value}抢断"
    elif data_term == "盖帽":
            return f"{value}盖帽"
    elif data_term == "真实命中率":
            return f"{round(value*100)}%真实命中"
    elif data_term == "效率值":
            return f"{value}效率"

class HighLight():
    def __init__(self, event_type_name, quarter, time):
        self.event_type_name = event_type_name
        self.quarter = quarter

        play_back_time, play_forward_time = HIGHLIGHT_PLAYTIME_DICT[self.event_type_name]
        # print(play_back_time, play_forward_time)

        self.start_time = time - play_back_time
        self.end_time = time + play_forward_time


    def check_time(self, quarter_video_lens):
        self.start_time = max(0, self.start_time)
        self.end_time = min(quarter_video_lens[self.quarter - 1], self.end_time)

    def clip_video(self, videos, quarter_video_lens, dir_name):
        self.check_time(quarter_video_lens)
        start_time, end_time = self.start_time, self.end_time

        output_file = None
        if dir_name is not None:
            output_file = os.path.join(dir_name, f"{os.path.basename(videos[self.quarter - 1]).split('.')[0]}_{start_time}_{end_time}.ts")


        return ffmpeg_clip(videos[self.quarter - 1], start_time, end_time-start_time, output_file)


def get_video_duration(video_path):
    clip = VideoFileClip(video_path)
    duration = clip.duration
    clip.close()
    return duration

def ffmpeg_clip(input_file, start_time, duration, output_file=None):
    # 计算开始和结束时间的小时、分钟和秒
    # print(start_time)
    # print(type(start_time))
    # key_frames = get_key_frames(input_file)
    # end_time = start_time + duration
    # print(start_time, end_time)
    # print(key_frames)
    # start_time = key_frames[bisect.bisect(key_frames, start_time)]
    # print(start_time)
    #
    hours, remainder = divmod(start_time, 3600)
    minutes, seconds = divmod(remainder, 60)
    # print(start_time)
    start_hms = f"{int(hours):02d}:{int(minutes):02d}:{seconds:.6f}"
    # print(start_hms)

    # end_id = min(len(key_frames) - 1, bisect.bisect(key_frames, end_time) + 1)
    # end_time = key_frames[end_id]

    # duration = str(round(end_time - start_time, 1))
    # print(start_time, end_time, duration)
    # print(start_hms)



    if output_file is None:
        output_file = os.path.join(os.path.dirname(input_file), f"{os.path.basename(input_file).split('.')[0]}_{start_time}_{start_time+duration}.ts")
    # 构建FFmpeg命令
    command = [
        'ffmpeg',
        '-ss', start_hms,  # 剪切开始时间
        '-t', f'{duration}',  # 剪切持续时间
        '-i', input_file,  # 先指定输入文件，再指定时间参数，以确保准确 seek
        '-c', 'copy',  # 复制流
        '-avoid_negative_ts', 'make_non_negative',  # 确保输出时间戳非负
        '-loglevel', 'quiet',
        '-y',
        output_file  # 输出文件
    ]

    # 执行FFmpeg命令
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error occurred: {e}")
    # print(output_file)
    return output_file
    

class VideoText(object):
    def __init__(self, font_path, main_text, top_text=None, bottom_text=None, color=None, border_color=None, border_padding=None):
        """
        @param main_text: 主文本, list
        @param top_text: 顶部文本, txt
        @param bottom_text: 底部文本, txt
        """
        self.main_text = main_text
        self.font_path = font_path
        self.top_text = top_text
        self.bottom_text = bottom_text
        self.color = color if color is not None else 'white'
        self.border_color = border_color if border_color is not None else color
        self.border_padding = border_padding if border_padding is not None else 1


# def concatenate_clips(data_dir, output_file, clips):
#     txt_file = os.path.join(data_dir, f"{os.path.basename(output_file)}_temp_concat_clip.txt")
#
#     with open(txt_file, 'w', encoding="utf-8") as f:
#         for i, clip in enumerate(clips):
#             f.write(f"file {clip[0]}\n")
#             f.write(f'inpoint {clip[1]}\n')
#             f.write(f'outpoint {clip[2]}\n')
#
#     command = [
#         'ffmpeg',
#         '-f', 'concat',  # 指定输入格式为concat
#         '-safe', '0',  # 关闭安全模式，防止文件路径解析问题
#         '-i', txt_file,  # 读取包含片段文件名的文本文件
#         '-c', 'copy',  # 复制流
#         '-loglevel', 'quiet',
#         '-y',
#         output_file  # 输出文件
#     ]
#     try:
#         subprocess.run(command, check=True)
#         os.remove(txt_file)
#
#     except subprocess.CalledProcessError as e:
#         print(f"Error occurred: {e}")
#
#     return output_file

def concatenate_clips(output_file, clips, delete_clips=False):
    txt_file = os.path.join(os.path.dirname(output_file), f"{os.path.basename(output_file)}_temp_concat_clip.txt")
    # print(txt_file)

    with open(txt_file, 'w', encoding="utf-8") as f:
        for clip in clips:
            f.write(f"file '{os.path.basename(clip)}'\n")

    command = [
        'ffmpeg',
        '-f', 'concat',  # 指定输入格式为concat
        '-safe', '0',    # 关闭安全模式，防止文件路径解析问题
        '-i', txt_file,  # 读取包含片段文件名的文本文件
        '-c', 'copy',      # 复制流
        '-loglevel', 'quiet',
        '-y',
        output_file        # 输出文件
    ]
    try:
        subprocess.run(command, check=True)


        # if delete_clips:
        #     for clip in clips:
        #         os.remove(clip)
        os.remove(txt_file)

    except subprocess.CalledProcessError as e:
        print(f"Error occurred: {e}")

    return output_file

def concatenate_video_with_cover(output_file, clips, origin_video_info, delete_origin=False, music_path=None, target_dir=None, prefix=None):

    target_dir = target_dir if target_dir is not None else os.path.dirname(output_file)
    prefix = prefix if prefix is not None else os.path.basename(output_file)


    txt_file = os.path.join(target_dir, f"{prefix}_temp.txt")
    tmp_file = os.path.join(target_dir, f"{prefix}_tmp_concat.{output_file.split('.')[-1]}")

    video_codec, video_tag, width, height, fps, time_base, audio_codec, sample_rate = origin_video_info

    for clip in clips:
        command = [
        'ffmpeg',
        '-i', clip,  # 指定输入格式为concat
        '-c', 'copy',    # 关闭安全模式，防止文件路径解析问题
        '-y',
        '-loglevel', 'quiet',
        f'{clip}.ts',
        ]
        subprocess.run(command, check=True)
        # print(f'{clip}.ts')
        # print("ts", get_video_info(f'{clip}.ts'))

    with open(txt_file, 'w', encoding='utf-8') as f:
        for clip in clips:
            f.write(f"file '{os.path.basename(clip)}.ts'\n")


    command = [
        'ffmpeg',
        '-f', 'concat',  # 指定输入格式为concat
        '-safe', '0',    # 关闭安全模式，防止文件路径解析问题
        '-i', txt_file,  # 读取包含片段文件名的文本文件
        '-c:v', 'copy',      # 复制流
        '-c:a', 'aac',  # 编码为AAC音频
        '-r', f'{int(fps.split("/")[0])}',
        '-video_track_timescale', f'{time_base.split("/")[-1]}',
        '-y',
        '-loglevel', 'quiet',
        tmp_file        # 输出文件
    ]
    try:
        subprocess.run(command, check=True)

        if music_path is not None:
            mix_audio(tmp_file, music_path, output_file)
            os.remove(tmp_file)
        else:
            os.rename(tmp_file, output_file)

        # if delete_origin:
        #     os.remove(clips[-1])
        os.remove(txt_file)
        for clip in clips:
            os.remove(f'{clip}.ts')

    except subprocess.CalledProcessError as e:
        print(f"Error occurred: {e}")




def mix_audio(input_path, audio_file_path, output_path):
    if audio_file_path is None:
        return
    # 提取m3u8视频的音频
    prefix = os.path.basename(input_path).split('.')[0]
    temp_audio_file = os.path.join(os.path.dirname(input_path), f"{prefix}_audio.aac")
    extract_audio_command = [
        'ffmpeg', 
        '-i', input_path,
        '-vn',  # 忽略视频流
        '-c:a', 'aac',  # 编码为AAC音频
        '-loglevel', 'quiet',
        temp_audio_file
    ]
    subprocess.run(extract_audio_command, check=True)

    # 将背景音乐与m3u8的音频混合
    mixed_audio_file = os.path.join(os.path.dirname(input_path), f"{prefix}_mixed_audio.aac")
    mix_audio_command = [
        'ffmpeg', 
        '-i', temp_audio_file,
        '-i', audio_file_path,
        '-filter_complex',  # 开始定义复杂的滤镜链
        'amix=inputs=2:duration=longest:dropout_transition=2',  # 混合两个音频流
        '-c:a', 'aac',  # 输出AAC音频
        '-loglevel', 'quiet',
        mixed_audio_file
    ]
    subprocess.run(mix_audio_command, check=True)

    new_video_command = [
        'ffmpeg', 
        '-i', input_path,
        '-i', mixed_audio_file,
        '-c:v', 'copy',  # 复制视频流
        '-c:a', 'copy',  # 复制混合后的音频流
        '-map', '0:v:0',  # 保留原视频流
        '-map', '1:a:0',  # 替换音频流
        '-shortest',
        '-y',
        '-loglevel', 'quiet',
        output_path  
    ]
    subprocess.run(new_video_command, check=True)

    # 清理临时文件
    os.remove(temp_audio_file)
    os.remove(mixed_audio_file)

def get_font_size(max_width, font_path):
    initial_font_size = max_width//21
    font = ImageFont.truetype(font_path, initial_font_size)
    small_font = ImageFont.truetype(font_path, initial_font_size//5*2)
    medium_font = ImageFont.truetype(font_path, initial_font_size//4*2)
    
    return font, small_font, medium_font

def get_size(font, line):
    x0, y0, x1, y1 = font.getbbox(line)
    return x1-x0, y1-y0

def draw_text_with_border(draw, pos, text, font, fill, border_color='black', border_padding=3):
    x, y = pos
    shadowcolor = border_color
    for dx, dy in [(-border_padding, 0), (border_padding, 0), (0, -border_padding), (0, border_padding),
                  (-border_padding, -border_padding), (border_padding, -border_padding), 
                  (-border_padding, border_padding), (border_padding, border_padding)]:
        draw.text((x + dx, y + dy), text, font=font, fill=shadowcolor)
    draw.text(pos, text, font=font, fill=fill)

def create_fixed_size_text_image(video_text, text_image_path, font_path, image_size=(500, 400), logo_path=None, base_cover_img_path=None):
    img = Image.new('RGBA', image_size, (0, 0, 0, 255))  # 透明背景
    if base_cover_img_path is not None:
        base_cover_img = Image.open(base_cover_img_path)
        img = base_cover_img.resize(image_size)
        enhancer = ImageEnhance.Brightness(img)  # 注意：PIL本身不直接支持透明度增强，但可以通过亮度调整间接实现透明效果
        img = enhancer.enhance(0.3)  # 调整亮度影响
        
    draw = ImageDraw.Draw(img)
    font, small_font, medium_font = get_font_size(image_size[0], font_path)

    padding = image_size[0]//100
    y_pos = (image_size[1] - sum(get_size(font, line)[1] for line in video_text.main_text)) // 2
    last_height = 0

    if logo_path is not None:
        logo = Image.open(logo_path).convert("RGBA")  # 确保logo为RGBA模式
        logo_width, logo_height = logo.size
        resize_rate = image_size[0] / logo_width
        logo = logo.resize((int(logo_width * resize_rate), int(logo_height * resize_rate)))
        logo_position = (padding, padding)  # 左上角位置
        img.paste(logo, logo_position, logo)

    for line in video_text.main_text:
        line_width, line_height = get_size(font, line)
        if line_height <= 10:
            line_height = last_height
        # print(line_height)
        x_pos = (image_size[0] - line_width) // 2
        draw_text_with_border(draw, (x_pos, y_pos), line, font, fill=video_text.color, border_color=video_text.border_color, border_padding=video_text.border_padding)
        y_pos += line_height
        last_height = line_height

    if video_text.top_text is not None:
        line_width, line_height = get_size(medium_font, video_text.top_text)
        x_pos = (image_size[0] - line_width - padding)
        draw_text_with_border(draw, (x_pos, padding), video_text.top_text, medium_font, fill=video_text.color, border_color=video_text.border_color, border_padding=video_text.border_padding)
    if video_text.bottom_text is not None:
        line_width, line_height = get_size(small_font, video_text.bottom_text)
        y_pos = image_size[1] - line_height - padding
        draw_text_with_border(draw, (padding, y_pos), video_text.bottom_text, small_font, fill=video_text.color, border_color=video_text.border_color, border_padding=video_text.border_padding)
    
    img.save(text_image_path)
    return text_image_path


def get_video_cover(origin_video_info, logo_path, video_text, output_name, font_path=None, text_img_path=None, duration=2, background_color='black', base_cover_img_path=None):
    video_codec, video_tag, width, height, fps, time_base, audio_codec, sample_rate = origin_video_info
    # print(origin_video_info)
    width = int(width)
    height = int(height)

    # print(audio_codec)
    # if "\\" in audio_codec:
    #     print("detected")
    #     audio_codec = audio_codec.split("\\")[0]

    if text_img_path is None:
        text_img_path = "tmp.png"
    create_fixed_size_text_image(video_text, text_img_path, font_path, image_size=(width, height), logo_path=logo_path, base_cover_img_path=base_cover_img_path)
    if logo_path is not None:
        logo_size = Image.open(logo_path).size

        logo_width = width // 8
        logo_height = logo_size[1] * logo_width // logo_size[0]
        # print(duration)
        # print(origin_video_info)

        intro_command = [
            'ffmpeg', 
            '-f', 'lavfi', '-i', f'color=c={background_color}:s={width}x{height}:d={duration}',  # 纯色背景
            '-loop', '1', '-i', logo_path,  # 循环播放logo，设置帧率为10fps
            '-loop', '1', '-i', text_img_path,  # 循环播放logo，设置帧率为10fps
            '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=stereo',  # 使用aevalsrc生成静音音频流
            '-filter_complex',  # 使用复合滤镜处理多个滤镜
            f'[1:v]scale={logo_width}x{logo_height}[logo];' +  # 调整logo尺寸
            f'[2:v]scale={width}x{height}[text];' +
            '[0:v][logo]overlay=(W-w)/150:(H-h)/80[bg];' +  # 将logo叠加到背景上，居中
            f'[bg][text]overlay=(W-w)/2:(H-h)/2[outv]',  # 将文字叠加到背景上，居中
            '-map', '[outv]',  # 映射输出视频流
            '-map', '3:a',  # 尝试映射音频流
            '-c:v', video_codec,  # 使用与原视频相同的视频编码
            '-tag:v', video_tag,
            '-c:a', "aac",  # 使用aac作为音频编码
            '-preset', 'ultrafast',
            '-r', fps,
            '-video_track_timescale', f'{time_base.split("/")[-1]}',
            '-y',
            '-loglevel', 'quiet',
            '-t', str(duration),  # 输出长度与最短的流相同
            output_name
        ]
    else:
        intro_command = [
            'ffmpeg', 
            '-f', 'lavfi', '-i', f'color=c={background_color}:s={width}x{height}:d={duration}',  # 纯色背景
            '-loop', '1', '-i', text_img_path,  # 循环播放logo，设置帧率为10fps
            '-f', 'lavfi', '-i', f'anullsrc=r={sample_rate}:cl=stereo',  # 使用aevalsrc生成静音音频流
            '-filter_complex',  # 使用复合滤镜处理多个滤镜
            f'[1:v]scale={width}x{height}[text];' +
            f'[0:v][text]overlay=(W-w)/2:(H-h)/2[outv]',  # 将文字叠加到背景上，居中
            '-map', '[outv]',  # 映射输出视频流
            '-map', '2:a',  # 尝试映射音频流
            '-c:v', 'h264',  # 使用与原视频相同的视频编码
            '-tag:v', video_tag,
            '-c:a', 'aac',  # 使用aac作为音频编码
            '-y',
            '-r', fps,
            '-video_track_timescale', f'{time_base.split("/")[-1]}',
            '-loglevel', 'quiet',
            '-t', str(duration),  # 输出长度与最短的流相同
            output_name
        ]
    # 执行ffmpeg命令
    subprocess.run(intro_command, check=True)
    # if video_codec != 'h264':
    #     intro_command = [
    #         'ffmpeg',
    #         '-i', output_name,
    #         '-c:v', video_codec,
    #
    #     ]
    if base_cover_img_path:
        os.remove(base_cover_img_path)
    os.remove(text_img_path)

    return output_name



def get_key_frames(video_path):
    # 定义ffprobe的命令
    ffprobe_cmd = [
        'ffprobe',
        '-loglevel', 'error',
        '-select_streams', 'v:0',
        '-show_entries', 'packet=pts_time,flags',
        '-of', 'csv=print_section=0',
        f'{video_path}'
    ]

    frames = subprocess.check_output(ffprobe_cmd).decode().strip().split("\n")
    key_frames = [frame for frame in frames if "K__" in frame]
    key_frames = list(map(lambda x:float(x.split(",")[0]), key_frames))

    return key_frames

def get_video_info(video_path):
    probe_output = subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height,r_frame_rate,codec_name,codec_tag_string,time_base', '-of', 'csv=p=0', video_path]).decode()
    # print(probe_output)
    probe_output = probe_output.strip()
    if probe_output[-1] == ",":
        probe_output = probe_output[:-1]
    video_codec, video_tag, width, height, fps, time_base = probe_output.split(',')
    width = int(width)
    height = int(height)
    audio_probe = subprocess.check_output(['ffprobe',
                                       '-v', 'error',
                                       '-select_streams', 'a:0',
                                       '-show_entries', 'stream=codec_name,sample_rate',
                                       '-of', 'default=nw=1:nk=1',
                                       video_path]).decode().strip()
    # print(audio_probe)

    audio_codec, sample_rate = audio_probe.split("\n")
    # print(audio_codec, sample_rate)

    return video_codec, video_tag, width, height, fps, time_base, audio_codec, sample_rate

def save_first_frame(input_video_path):
    base_name = input_video_path[:-4]
    first_frame_path = f"{base_name}_first_frame.jpg"

    ffmpeg_command = [
        "ffmpeg",
        "-i", input_video_path,  # 输入视频文件路径
        "-vframes", "1",  # 只提取一帧
        '-y',
        first_frame_path  # 输出图片路径
    ]
    
    subprocess.run(ffmpeg_command)
    return first_frame_path



def edit_video(input_video_path, add_music=False, add_cover=False, logo_path=None, main_text=None, output_video_path=None, font_path=None, top_text=None, bottom_text=None, music_path=None, replace=False):
    if add_cover:
        # print(font_path, main_text, top_text, bottom_text)
        video_text = VideoText(font_path=font_path, main_text=main_text, top_text=top_text, bottom_text=bottom_text)
        # print(input_video_path)
        video_base_name_split = os.path.basename(input_video_path).split(".")
        cover_video_name_tmp = os.path.join(os.path.dirname(input_video_path), f'{video_base_name_split[0]}_cover.{video_base_name_split[1]}')
        cover_text_img_name_tmp = os.path.join(os.path.dirname(input_video_path), f'{video_base_name_split[0]}_cover_text.png')
        output_video_path = os.path.join(os.path.dirname(input_video_path), f'{video_base_name_split[0]}_new.{video_base_name_split[1]}') if output_video_path is None else output_video_path
        first_frame_path =  save_first_frame(input_video_path)
        get_video_cover(get_video_info(input_video_path), logo_path, video_text, cover_video_name_tmp, font_path=font_path, text_img_path=cover_text_img_name_tmp, duration=3, base_cover_img_path=first_frame_path)
        if add_music:
            music_path = music_path
        concatenate_video_with_cover(output_video_path, [cover_video_name_tmp, input_video_path], get_video_info(input_video_path), music_path=music_path, delete_origin=False, target_dir=os.path.dirname(input_video_path), prefix=video_base_name_split[0])
        os.remove(cover_video_name_tmp)
        if replace:
            os.remove(input_video_path)
            os.rename(output_video_path, input_video_path)
            return input_video_path
        return output_video_path
    if add_music:
        video_base_name_split = os.path.basename(input_video_path).split(".")
        output_video_path = os.path.join(os.path.dirname(input_video_path), f'{video_base_name_split[0]}_new.{video_base_name_split[1]}') if output_video_path is None else output_video_path
        if music_path is not None:
            mix_audio(input_video_path, music_path, output_video_path)
        if replace:
            os.remove(input_video_path)
            os.rename(output_video_path, input_video_path)
            return input_video_path
        return output_video_path
    
def check_video_info_and_reencode(video_names):
    video_codec_list = []
    fps_list = []
    resolution_list = []
    for i, video_path in enumerate(video_names):
        video_codec, video_tag, width, height, fps, time_base, audio_codec, sample_rate = get_video_info(video_path)
        video_codec_list.append(video_codec)
        fps_list.append(fps)
        resolution_list.append(f"{width}x{height}")
    target_fps = min(fps_list)
    target_resolution = max(resolution_list, key=resolution_list.count)
    target_codec = "h264"
    target_codecs = ["h264", "libx264"]

    print(f"本次视频的目标帧率是{target_fps}")
    print(f"本次视频的目标编码格式是{target_codec}")
    print(f"本次视频的目标分辨率是{target_resolution}")
    print(f"本次视频的编码格式是{max(video_codec_list, key=video_codec_list.count)}")


    for i, video_path in enumerate(video_names):
        if video_codec_list[0] not in target_codecs or fps_list[0] != target_fps or resolution_list[0] != target_resolution:
            print(f"视频{i+1}/{len(video_names)}, 需重新编码. 当前编码格式：{video_codec_list[0]}, 当前帧率：{fps_list[0]}, 当前分辨率：{resolution_list[0]}")
            reencode(video_path, target_codec, target_fps, target_resolution)


def reencode(video, target_codec, target_fps, target_resolution):
    postfix = os.path.basename(video).split('.')[-1]
    print(video, postfix)
    origin_new_name = video.replace(f".{postfix}", f"_origin.{postfix}")
    print(origin_new_name)
    os.rename(video, origin_new_name)
    if target_codec == "h264":
        target_codec = "libx264"
    command = ['ffmpeg', 
               '-i', origin_new_name, 
               '-c:v', target_codec, 
               '-r', str(target_fps), 
               '-s', target_resolution,
               '-preset', 'ultrafast',
               '-pix_fmt', 'yuv420p',
               '-c:a', 'copy', 
               video]
    procress = FfmpegProcess(command)
    procress.run()
    os.remove(origin_new_name)

def del_file(filepath, suffix, video_dir_postfix=""):
    filepath = f"{filepath}{video_dir_postfix}"
    files = os.listdir(filepath)

    for file in files:
        if '.' in file:
            suffix_tmp = file.split('.')[-1]
            if suffix_tmp == suffix:
                os.remove(os.path.join(filepath, file))
        
 

if __name__ == '__main__':
    # music_path = "hello.mp3"
    # input_video = "test.mp4"
    # text = ["3011 个人集锦", " ", "35分 11板 12助攻"]
    # top_text = "2023-05-01"
    # bottom_text = "地点: ABL  时间: 20-22点"
    # logo_path = "logo3.png"
    # font_path = 'dream.ttf'

    cover_test = 'test_cover.mp4'
    video_test = 'test_highlight.mp4'
    concatenate_video_with_cover("test_output1.mp4", [cover_test, video_test], get_video_info(video_test), music_path=None, delete_origin=False)

    # video_info = get_video_info(input_video)
    # video_codec, audio_codec, width, height, fps, audio_codec = video_info

    # edit_video(input_video, add_cover=False, logo_path=logo_path, main_text=text, font_path=font_path, top_text=top_text, bottom_text=bottom_text, add_music=True, music_path=music_path, replace=True)

import numpy as np
from plottable import Table, ColDef
import matplotlib.pyplot as plt
import argparse
import json
import pandas as pd
from moviepy.editor import VideoFileClip, concatenate_videoclips, ImageClip, CompositeVideoClip, CompositeAudioClip, \
    AudioFileClip, afx
from moviepy.video.VideoClip import TextClip
import os
from BasketballEvents import BasketballEvents

HIGHLIGHT_PLAYTIME_DICT = {"进球": (6, 3), "盖帽": (3, 3), "助攻": (6, 3), "抢断": (2, 2), "3分": (3, 4), "2分": (3, 4),
                           "篮板": (3, 3), "不进": (6, 3), "失误": (6, 3)}

class GameHighlightController():
    def __init__(self, game_dir):
        self.config = json.load(open(os.path.join(game_dir, "config.json")))
        self.game_dir = game_dir
        self.quarter_video_lens = []
        self.videos = []
        for i in range(1, self.config["quarters"] + 1):
            tmp_clip = VideoFileClip(os.path.join(game_dir, "q{}.{}".format(i, self.config["video_format"])))
            self.videos.append(tmp_clip)
            self.quarter_video_lens.append(tmp_clip.duration)
        event_data = pd.read_csv(os.path.join(game_dir, "events.csv"))
        event_data = event_data.fillna("")
        self.basketball_events = BasketballEvents(event_data, self.config)
        self.default_target_stats = ["scores", "assists", "blocks"]

        self.team_names = self.basketball_events.team_names

        self.init_team_highlight_data()
        self.init_player_highlight_data()
        self.init_missed_data()

        self.missed_data = event_data[(event_data.Info == "不进") | (event_data.Event == "失误")]
        self.highlight_data = event_data[
            (event_data.Event == "抢断") | (event_data.Event == "篮板") | (event_data.Event == "盖帽") | (
                    event_data.Event == "助攻") | ((event_data.Info == "进球") & (event_data.Event == "3分球出手")) | (
                    (event_data.Info == "进球") & (event_data.Event == "2分球出手"))]
        self.delete_data = event_data[(event_data.Event == "highlight") | (event_data.Info == "bad")]

        self.parse_team_highlight()
        self.parse_missed_highlight()

        self.last_parsed_stats = None

        if not os.path.exists(os.path.join(self.game_dir, self.team_names[0])):
            os.mkdir(os.path.join(self.game_dir, self.team_names[0]))
        if not os.path.exists(os.path.join(self.game_dir, self.team_names[1])):
            os.mkdir(os.path.join(self.game_dir, self.team_names[1]))


    def init_team_highlight_data(self):
        self.collections_whole_team = [TeamHighLightCollection(self.team_names[0]), TeamHighLightCollection(self.team_names[1])]

    def init_player_highlight_data(self):
        self.collections_team_players = [
            {name: PlayerHighLightCollection(self.team_names[0], name) for name in self.basketball_events.player_names[0]},
            {name: PlayerHighLightCollection(self.team_names[1], name) for name in self.basketball_events.player_names[1]}]

    def init_missed_data(self):
        self.missed_collections_team_players = [
            {name: PlayerHighLightCollection(self.team_names[0], name) for name in self.basketball_events.player_names[0]},
            {name: PlayerHighLightCollection(self.team_names[1], name) for name in self.basketball_events.player_names[1]}]


    def parse_team_highlight(self):
        for i, r in self.highlight_data.iterrows():
            team_idx = self.team_names.index(r["Team"])

            """球队集锦，目前版本默认进球+盖帽，不可选"""

            if r["Info"] == "进球" or r["Event"] == "盖帽":
                self.collections_whole_team[team_idx].add(HighLight(r["Info"], r["Quarter"], r["OriginQuarterTime"]))
            elif r["Event"] == "助攻":
                self.collections_whole_team[team_idx].add(HighLight(r["Info"], r["Quarter"], r["OriginQuarterTime"]))


    def parse_player_highlight(self, target_stats=None):
        target_stats = self.get_target_stats(target_stats)
        print(target_stats)
        if self.last_parsed_stats is None or self.last_parsed_stats != target_stats:
            for i, r in self.highlight_data.iterrows():
                team_idx = self.team_names.index(r["Team"])

                """球队集锦，可选得分、助攻、盖帽、抢断、篮板"""

                if r["Info"] == "进球" and "scores" in target_stats:
                    self.collections_team_players[team_idx][r["Player"]].add(
                        HighLight(r["Info"], r["Quarter"], r["OriginQuarterTime"]))

                if r["Event"] == "助攻" and "assists" in target_stats:
                    self.collections_team_players[team_idx][r["Player"]].add(
                        HighLight(r["Info"], r["Quarter"], r["OriginQuarterTime"]))

                if r["Event"] == "助攻" and "scores" in target_stats:
                    self.collections_team_players[team_idx][r["Object"]].add(
                        HighLight(r["Event"], r["Quarter"], r["OriginQuarterTime"]))

                if r["Event"] == "篮板" and "rebounds" in target_stats:
                    self.collections_team_players[team_idx][r["Player"]].add(
                        HighLight(r["Event"], r["Quarter"], r["OriginQuarterTime"]))

                if r["Event"] == "抢断" and "steals" in target_stats:
                    self.collections_team_players[team_idx][r["Player"]].add(
                        HighLight(r["Event"], r["Quarter"], r["OriginQuarterTime"]))

                if r["Event"] == "盖帽" and "blocks" in target_stats:
                    self.collections_team_players[team_idx][r["Player"]].add(
                        HighLight(r["Event"], r["Quarter"], r["OriginQuarterTime"]))
            print(self.collections_team_players[0]["MARKO"].data)
            # print(self.collections_team_players[1])
            self.last_parsed_stats = target_stats


    def parse_missed_highlight(self):
        for i, r in self.missed_data.iterrows():
            team_idx = self.team_names.index(r["Team"])
            if r["Info"] == "不进":
                self.missed_collections_team_players[team_idx][r["Player"]].add(
                    HighLight(r["Info"], r["Quarter"], r["OriginQuarterTime"]))
            if r["Event"] == "失误":
                self.missed_collections_team_players[team_idx][r["Player"]].add(
                    HighLight(r["Event"], r["Quarter"], r["OriginQuarterTime"]))


    def get_target_stats(self, target_stats):
        if target_stats is None:
            return self.default_target_stats
        return target_stats


    def get_team_highlight(self, team, music_path=None):
        target_path = os.path.join(self.game_dir, team, "highlight_{}.mp4".format(team))
        team_idx = self.team_names.index(team)
        self.collections_whole_team[team_idx].download_highlight(self.videos, self.quarter_video_lens, music_path, target_path)


    def get_player_highlight(self, team, player, target_stats=None, music_path=None):
        self.parse_player_highlight(target_stats)
        target_path = os.path.join(self.game_dir, team, "highlight_{}.mp4".format(player))
        team_idx = self.team_names.index(team)
        print(self.videos, self.quarter_video_lens, music_path, target_path)

        self.collections_team_players[team_idx][player].download_highlight(self.videos, self.quarter_video_lens, music_path, target_path)


    def get_all_teams_highlights(self, music_path=None):
        target_path = os.path.join(self.game_dir, self.team_names[0], "highlight_{}.mp4".format(self.team_names[0]))
        self.collections_whole_team[0].download_highlight(self.videos, self.quarter_video_lens, music_path, target_path)
        target_path = os.path.join(self.game_dir, self.team_names[0], "highlight_{}.mp4".format(self.team_names[1]))
        self.collections_whole_team[1].download_highlight(self.videos, self.quarter_video_lens, music_path, target_path)


    def get_all_players_highlights(self, music_path=None, target_stats=None):
        self.parse_player_highlight(target_stats)
        for team_id in range(2):
            for name in collections_team_players[team_id]:
                target_path = os.path.join(self.game_dir, self.team_names[team_id], "highlight_{}.mp4".format(name))
                self.collections_team_players[team_id][name].download_highlight(self.videos, self.quarter_video_lens, music_path, target_path)


class PlayerHighLightCollection():
    def __init__(self, team, name):
        self.data = []
        self.name = name
        self.team = team

    def __len__(self):
        return len(self.data)

    def add(self, highlight):
        self.data.append(highlight)

    def download_highlight(self, videos, quarter_video_lens, music_path=None, result_path=None):
        print("shit")
        if music_path is not None:
            music = AudioFileClip(music_path).volumex(0.5)
        print(self.data)
        if not (len(self.data)):
            return 0
        print("shit")
        clip = self.data[0].clip_video(videos, quarter_video_lens)
        for i, highlight in enumerate(self.data):
            if not i:
                continue
            # if i > 1:
            #     continue
            clip = concatenate_videoclips([clip, highlight.clip_video(videos, quarter_video_lens)])

        logo = (ImageClip("logo1.png")
            .set_duration(clip.duration)  # 水印持续时间
            .resize(height=170)  # 水印的高度，会等比缩放
            .set_pos(("left", "top")))  # 水印的位置

        final_clip = CompositeVideoClip([clip, logo])

        # final_clip = clip
        if music_path is not None:
            video_audio_clip = final_clip.audio.volumex(0.8)
            audio = afx.audio_loop(music, duration=final_clip.duration)
            audio_clip_add = CompositeAudioClip([video_audio_clip, audio])
            final_clip = final_clip.set_audio(audio_clip_add)
        if result_path is None:
            result_path = os.path.join(args.game_path, "highlight_{}.mp4".format(self.name))
        print("shit")
        print(self.data)
        final_clip.write_videofile(result_path,
                                    audio_codec='aac')


class TeamHighLightCollection():
    def __init__(self, team):
        self.data = []
        self.team = team

    def add(self, highlight):
        self.data.append(highlight)

    def __len__(self):
        return len(self.data)

    def download_highlight(self, videos, quarter_video_lens, music_path=None, result_path=None):
        if music_path is not None:
            music = AudioFileClip(music_path).volumex(0.5)
            if not (len(self.data)):
                return 0

        clip = self.data[0].clip_video(videos, quarter_video_lens)
        for i, highlight in enumerate(self.data):
            if not i:
                continue
            clip = concatenate_videoclips([clip, highlight.clip_video(videos, quarter_video_lens)])

        logo = (ImageClip("logo1.png")
            .set_duration(clip.duration)  # 水印持续时间
            .resize(height=170)  # 水印的高度，会等比缩放
            .set_pos(("left", "top")))  # 水印的位置

        final_clip = CompositeVideoClip([clip, logo])

        if music_path is not None:
            video_audio_clip = final_clip.audio.volumex(0.8)
            audio = afx.audio_loop(music, duration=final_clip.duration)
            audio_clip_add = CompositeAudioClip([video_audio_clip, audio])
            final_clip = final_clip.set_audio(audio_clip_add)
        if result_path is None:
            result_path = os.path.join(args.game_path, "highlight_{}.mp4".format(self.team))
        final_clip.write_videofile(result_path,
                                    audio_codec='aac')
        final_clip.write_videofile(result_path,
                                    audio_codec='aac')

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

    def clip_video(self, videos, quarter_video_lens):
        self.check_time(quarter_video_lens)
        return videos[self.quarter - 1].subclip(self.start_time, self.end_time)







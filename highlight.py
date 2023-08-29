import numpy as np
from plottable import Table, ColDef
import matplotlib.pyplot as plt
import argparse
import json
import pandas as pd
from moviepy.editor import VideoFileClip, concatenate_videoclips, ImageClip, CompositeVideoClip, CompositeAudioClip, AudioFileClip, afx
from moviepy.video.VideoClip import TextClip
import os


parser = argparse.ArgumentParser(description='Run Example')
parser.add_argument('game_path', type=str, help='path of game files')
args = parser.parse_args()

config = json.load(open(os.path.join(args.game_path, "config.json")))
quarter_time = config["quarter_time"]

actual_quarter_time = 21 #TODO automatic
quarters = config["quarters"]
event_data = pd.read_csv(os.path.join(args.game_path, "events.csv"))
event_data = event_data.fillna("")

quarter_start_times = list(event_data[event_data.Event=="计时开始"]["Info"])

videos = []
for i in range(1, quarters+1):
    videos.append(VideoFileClip(os.path.join(args.game_path, "q{}.MOV".format(i))))
music = AudioFileClip("Hanging With Wolves.mp3").volumex(0.5)

SHORT_HIGHLIGHT_PLAYBACK = 4
SHORT_HIGHLIGHT_PLAYFORWARD = 3
LONG_HIGHLIGHT_PLAYBACK = 7
LONG_HIGHLIGHT_PLAYFORWARD = 3
HIGHLIGHT_SEARCH_RANGE = 10


def append(df, row_dict):
    return pd.concat([df, pd.DataFrame([row_dict])], ignore_index=True)

def parse_time(time):
    t = time.split(" - ")
    t_ = t[1].split(" : ")

    q, m, s = int(t[0]), int(t_[0]), int(t_[1])
    return (q-1) * actual_quarter_time * 60 + m * 60 + s

def parse_quarter(time):
    t = time.split(" - ")
    t_ = t[1].split(" : ")

    q, m, s = int(t[0]), int(t_[0]), int(t_[1])
    return q

def parse_origin_quarter_time(time):
    t = time.split(" - ")
    t_ = t[1].split(" : ")

    q, m, s = int(t[0]), int(t_[0]), int(t_[1])
    return m * 60 + s + int(quarter_start_times[q-1])

event_data["OriginQuarterTime"] = event_data["Time"].apply(parse_origin_quarter_time)
event_data["Quarter"] = event_data["Time"].apply(parse_quarter)
event_data["Time"] = event_data["Time"].apply(parse_time)

team_names = list(config["team_players"].keys())
players_A = config["team_players"][team_names[0]]
players_B = config["team_players"][team_names[1]]
player_names_A = [player["name"] for player in players_A]
player_names_B = [player["name"] for player in players_B]

highlight_data = event_data[event_data.Event=="highlight"]


assert len(quarter_start_times) == 4


class PlayerHighLightCollection():
    def __init__(self, team, name):
        self.data = []
        self.name = name
        self.team = team

    def __len__(self):
        return len(self.data)

    def add(self, highlight):
        self.data.append(highlight)

    def download_highlight(self, music_path):
        music = AudioFileClip(music_path).volumex(0.5)

        clip = self.data[0].clip_video()
        for i, highlight in enumerate(self.data):
            if not i:
                continue
            clip = concatenate_videoclips([clip, highlight.clip_video()])

        logo = (ImageClip("logo1.png")
            .set_duration(clip.duration)  # 水印持续时间
            .resize(height=170)  # 水印的高度，会等比缩放
            .set_pos(("left", "top")))  # 水印的位置

        final_clip = CompositeVideoClip([clip, logo])

        video_audio_clip = final_clip.audio.volumex(0.8)
        audio = afx.audio_loop(music, duration=final_clip.duration)
        audio_clip_add = CompositeAudioClip([video_audio_clip, audio])
        final_video = final_clip.set_audio(audio_clip_add)

        final_video.write_videofile("result_{}.mp4".format(self.name))

class TeamHighLightCollection():
    def __init__(self, team):
        self.data = []
        self.team = team

    def add(self, highlight):
        self.data.append(highlight)

    def __len__(self):
        return len(self.data)

    def download_highlight(self, music_path):
        music = AudioFileClip(music_path).volumex(0.5)

        clip = self.data[0].clip_video()
        for i, highlight in enumerate(self.data):
            if not i:
                continue
            clip = concatenate_videoclips([clip, highlight.clip_video()])

        logo = (ImageClip("logo1.png")
            .set_duration(clip.duration)  # 水印持续时间
            .resize(height=170)  # 水印的高度，会等比缩放
            .set_pos(("left", "top")))  # 水印的位置

        final_clip = CompositeVideoClip([clip, logo])

        video_audio_clip = final_clip.audio.volumex(0.8)
        audio = afx.audio_loop(music, duration=final_clip.duration)
        audio_clip_add = CompositeAudioClip([video_audio_clip, audio])
        final_video = final_clip.set_audio(audio_clip_add)

        final_video.write_videofile("result_{}.mp4".format(self.team))


class HighLight():
    def __init__(self, event_type_name, quarter, time, lenght_type):
        self.event_type_name = event_type_name
        self.quarter = quarter

        if lenght_type == "short":
            self.start_time = time - SHORT_HIGHLIGHT_PLAYBACK
            self.end_time = time + SHORT_HIGHLIGHT_PLAYFORWARD
        else:
            self.start_time = time - LONG_HIGHLIGHT_PLAYBACK
            self.end_time = time + LONG_HIGHLIGHT_PLAYFORWARD



    def clip_video(self):
        return videos[self.quarter-1].subclip(self.start_time, self.end_time)



collections_whole_team_A = TeamHighLightCollection(team_names[0])
collections_whole_team_B = TeamHighLightCollection(team_names[1])
collections_team_players_A = {name: PlayerHighLightCollection(team_names[0], name) for name in player_names_A}
collections_team_players_B = {name: PlayerHighLightCollection(team_names[1], name) for name in player_names_B}



def search_highlight_owner(time, type="short"):
    # start_time = time - SHORT_HIGHLIGHT_PLAYBACK if (type == "short") else LONG_HIGHLIGHT_PLAYBACK
    # end_time = time + SHORT_HIGHLIGHT_PLAYFORWARD if (type == "short") else LONG_HIGHLIGHT_PLAYFORWARD
    events = event_data[
        (event_data.Time >= time - HIGHLIGHT_SEARCH_RANGE) & (event_data.Time <= time + HIGHLIGHT_SEARCH_RANGE)]
    events = events[(events.Event == "助攻") | (events.Info == "进球")]
    if not (len(events)):
        return 0
    events = events.iloc[(events["Time"] - time).abs().argsort()]
    events = events.to_dict(orient='records')[0]
    return events


for i, r in highlight_data.iterrows():
    highlight_event = search_highlight_owner(r["Time"])
    if highlight_event == 0:
        continue
    highlight_time = highlight_event["Time"]
    if highlight_event["Team"] == team_names[0]:
        collections_whole_team = collections_whole_team_A
        collections_team_players = collections_team_players_A
    else:
        collections_whole_team = collections_whole_team_B
        collections_team_players = collections_team_players_B

    if highlight_event["Info"] == "进球":
        collections_whole_team.add(HighLight(highlight_event["Event"], r["Quarter"], r["OriginQuarterTime"], r["Info"]))
        collections_team_players[highlight_event["Player"]].add(HighLight(highlight_event["Event"], r["Quarter"], r["OriginQuarterTime"], r["Info"]))
    # 助攻
    else:
        collections_whole_team.add(HighLight(highlight_event["Info"], r["Quarter"], r["OriginQuarterTime"], r["Info"]))
        collections_team_players[highlight_event["Player"]].add(
            HighLight(highlight_event["Event"], r["Quarter"], r["OriginQuarterTime"], r["Info"]))
        collections_team_players[highlight_event["Object"]].add(
            HighLight(highlight_event["Info"], r["Quarter"], r["OriginQuarterTime"], r["Info"]))

for name in collections_team_players_A:
    print(name, len(collections_team_players_A[name]))
for name in collections_team_players_B:
    print(name, len(collections_team_players_B[name]))

# collections_whole_team_A.download_highlight("Hanging With Wolves.mp3")
collections_team_players_A["老夏"].download_highlight("Hanging With Wolves.mp3")

# clip1 = VideoFileClip("q1.MOV").subclip(10,20)
# clip2 = VideoFileClip("q1.MOV").subclip(50,60)
# final_clip = concatenate_videoclips([videos[0].subclip(98, 103), videos[1].subclip(50, 55)])
# logo = (ImageClip("logo1.png")
#         .set_duration(final_clip.duration) # 水印持续时间
#         .resize(height=170) # 水印的高度，会等比缩放
#         .set_pos(("left","top"))) # 水印的位置
# # textClip = (TextClip("TOP GUN VS PURDUE", fontsize=30, color='white').set_pos("top").set_duration(final_clip.duration))
# final_clip = CompositeVideoClip([final_clip, logo])
#
# video_audio_clip = final_clip.audio.volumex(0.8)
# audio = afx.audio_loop(music, duration=final_clip.duration)
# audio_clip_add = CompositeAudioClip([video_audio_clip,audio])
# final_video = final_clip.set_audio(audio_clip_add)
#
# final_video.write_videofile("result.mp4")


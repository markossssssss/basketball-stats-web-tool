import numpy as np
from plottable import Table, ColDef
import matplotlib.pyplot as plt
import argparse
import json
import pandas as pd
from moviepy.editor import VideoFileClip, concatenate_videoclips, ImageClip, CompositeVideoClip, CompositeAudioClip, AudioFileClip, afx
from moviepy.video.VideoClip import TextClip
import os
from BasketballEvents import BasketballEvents
from HighlightModel import GameHighlightController, PlayerHighLightCollection, TeamHighLightCollection, HighLight

parser = argparse.ArgumentParser(description='Run Example')
parser.add_argument('data_dir', type=str, help='path of config file')
parser.add_argument('music_path', type=str, help='path of config file')
args = parser.parse_args()

hlc = GameHighlightController(args.data_dir)
hlc.get_player_highlight("JUSHOOP", "MARKO",  target_stats=["scores"], music_path=args.music_path)


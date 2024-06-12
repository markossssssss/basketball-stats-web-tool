# encoding=utf-8
import argparse
import os
from FastHighlightModel import GameHighlightControllerFast
from multiprocessing import Pool
import multiprocessing
import time

def sync_func(i, data_dir, music_path, font_path, logo_path):
    hlc = GameHighlightControllerFast(data_dir, font_path, logo_path)
    if i <= 3:
        hlc.get_all_players_highlights(i, music_path=music_path, target_stats=["scores", "assists", "blocks"])
    elif i == 4:
        hlc.get_all_in_one_highlight(music_path=music_path)
    else:
        pass
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run Example')
    parser.add_argument('data_dir', type=str, help='path of config file')
    parser.add_argument('-music_path', type=str, default=None, help='path of config file')
    parser.add_argument('-font_path', type=str, default="dream.ttf", help='path of font file')
    parser.add_argument('-logo_path', type=str, default="logo3.png", help='path of logo file')
    args = parser.parse_args()
    
    data_dir = args.data_dir
    music_path = args.music_path
    font_path = args.font_path
    logo_path = args.logo_path
    hlc = GameHighlightControllerFast(data_dir, args.font_path, args.logo_path)

    # hlc.basketball_events.get_stats()
    # hlc.get_player_highlight("Team A", "Simon", music_path=music_path)

    t0 = time.time()

    # 多进程执行
    processes = []
    for i in range(5):
        p = multiprocessing.Process(target=sync_func,args=(i, data_dir, music_path, font_path, logo_path))
        p.start()
        processes.append(p)

    for p in processes:
        p.join()


    # 单进程执行
    # # hlc.get_all_in_one_highlight(music_path=args.music_path)
    # for i in range(4):
    #     hlc.get_all_players_highlights(i, music_path=args.music_path, target_stats=["scores", "assists", "blocks"])

    print("总时长: ", time.time()-t0)


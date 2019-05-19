import os
from pydub import AudioSegment
from pydub.silence import detect_silence, detect_nonsilent
from moviepy.editor import VideoFileClip, vfx, concatenate_videoclips

# 0. ARGUMENTS

SILENT_THRESHOLD = -50
SOUNDED_SPEED = 2
SILENT_SPEED = 8
MIN_SILENCE_LENGTH = 1000


def speed_change(audio, speed=1.0):
    # Manually override the frame_rate. This tells the computer how many samples to play per second
    sound_with_altered_frame_rate = audio._spawn(audio.raw_data, overrides={
        "frame_rate": int(audio.frame_rate * speed)
    })
    return sound_with_altered_frame_rate.set_frame_rate(audio.frame_rate)
    # Speed change adapted From stackoverflow.com/questions/51434897


# 1. Change mp4 into audio
currentPath = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
extension_list = ('.mp4')

for video in os.listdir(currentPath):
    if video.lower().endswith(extension_list):
        video_path = currentPath + "\\" + video
        audio = AudioSegment.from_file(video_path, "mp4")
        clip = VideoFileClip(video_path)

        rate = audio.frame_rate

        time_start = 0
        time_end = audio.duration_seconds
        silent_ranges = detect_silence(audio, silence_thresh=SILENT_THRESHOLD,  min_silence_len=MIN_SILENCE_LENGTH)
        non_silent_ranges = detect_nonsilent(audio, silence_thresh=SILENT_THRESHOLD,
                                             min_silence_len=MIN_SILENCE_LENGTH)

        # Used to distinguish silence and sounded
        for array in silent_ranges:
            array.append(1)
        for array in non_silent_ranges:
            array.append(0)

        ranges = silent_ranges + non_silent_ranges
        ranges.sort()

        clips = []
        for i_start, i_end, silence in ranges:
            sub_clip = clip.subclip(i_start/1000, i_end/1000)

            if silence == 0:
                sub_clip = sub_clip.fx(vfx.speedx, SOUNDED_SPEED)
            else:
                sub_clip = sub_clip.fx(vfx.speedx, SILENT_SPEED)
            clips.append(sub_clip)

        output_clip = concatenate_videoclips(clips)
        output_clip.write_videofile(currentPath + "\\output.mp4")

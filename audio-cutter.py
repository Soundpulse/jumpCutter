from moviepy.editor import VideoFileClip, AudioFileClip, vfx, concatenate_videoclips
from pydub.silence import detect_silence, detect_nonsilent
from pydub import AudioSegment
from audiotsm import phasevocoder
from audiotsm.io.wav import WavReader, WavWriter
import shutil
import os

# 0. ARGUMENTS

SILENT_THRESHOLD = -50
SOUNDED_SPEED = 2
SILENT_SPEED = 8
MIN_SILENCE_LENGTH = 1000


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
        silent_chunks = detect_silence(audio, silence_thresh=SILENT_THRESHOLD,  min_silence_len=MIN_SILENCE_LENGTH)
        non_silent_chunks = detect_nonsilent(audio, silence_thresh=SILENT_THRESHOLD,
                                             min_silence_len=MIN_SILENCE_LENGTH)

        # Used to distinguish silence and sounded
        for array in silent_chunks:
            array.append(1)
        for array in non_silent_chunks:
            array.append(0)

        chunks = silent_chunks + non_silent_chunks
        chunks.sort()

        clips = []
        os.mkdir(currentPath + "\\temp")
        i = 0
        for i_start, i_end, silence in chunks:
            i += 1
            if silence == 0:
                speed = SOUNDED_SPEED
            else:
                speed = SILENT_SPEED

            sub_clip = clip.subclip(i_start/1000, i_end/1000)

            sub_clip.write_videofile(currentPath + "\\temp\\sub_clip{0}.mp4".format(i))
            AudioSegment.from_file(currentPath + "\\temp\\sub_clip{0}.mp4".format(i)
                                   ).export(currentPath + "\\temp\\sub_clip{0}.wav".format(i), format='wav')

            src = currentPath + "\\temp\\sub_clip{0}.wav".format(i)
            out = currentPath + "\\temp\\sub_clip-reg{0}.wav".format(i)
            with WavReader(src) as reader:
                with WavWriter(out, reader.channels, reader.samplerate) as writer:
                    tsm = phasevocoder(reader.channels, speed=speed)
                    tsm.run(reader, writer)

            sub_clip = sub_clip.fx(vfx.speedx, speed)
            sub_clip = sub_clip.set_audio(AudioFileClip(out))
            sub_clip.write_videofile(currentPath + "\\temp\\sub_clip-reg{0}.mp4".format(i))

            clips.append(sub_clip)

        output_clip = concatenate_videoclips(clips)
        output_clip.write_videofile(currentPath + "\\output.mp4")

        # DANGEROUS
        shutil.rmtree(currentPath + "\\temp")

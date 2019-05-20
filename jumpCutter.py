from moviepy.editor import VideoFileClip, AudioFileClip, vfx, concatenate_videoclips
from pydub.silence import detect_silence, detect_nonsilent
from pydub import AudioSegment
from audiotsm import phasevocoder
from audiotsm.io.wav import WavReader, WavWriter
import shutil
import os
import time

# 0. ARGUMENTS

SILENT_THRESHOLD = -55
SOUNDED_SPEED = 1.2
SILENT_SPEED = 10
MIN_SILENCE_LENGTH = 1000

# 1. Change mp4 into audio
currentPath = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
inputPath = os.path.join(currentPath, "input")
outputPath = os.path.join(currentPath, "output")

extension_list = ('.mp4', '.avi', '.mkv', '.mov', '.webm', '.ogg')


for video in os.listdir(inputPath):
    if video.lower().endswith(extension_list):
        tik = time.time()
        video_path = os.path.join(inputPath, video)
        print("Reading File: " + video_path)
        print("Reading Audio...")
        audio = AudioSegment.from_file(video_path, "mp4")
        print("Reading Video...")
        clip = VideoFileClip(video_path, audio=False)

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
        # Clean temp
        tempPath = os.path.join(currentPath, "temp")
        if(os.path.isdir(tempPath)):
            shutil.rmtree(tempPath)
        else:
            os.mkdir(tempPath)

        i = 0
        for i_start, i_end, silence in chunks:
            i += 1
            if i_start != i_end:
                if silence == 0:
                    speed = SOUNDED_SPEED
                else:
                    speed = SILENT_SPEED

                sub_clip = clip.subclip(i_start/1000, i_end/1000)

                audio[i_start:i_end].export(os.path.join(tempPath, "sub_clip.wav"), format='wav')

                src = os.path.join(tempPath, "sub_clip.wav")
                out = os.path.join(tempPath, "sub_clip-reg{0}.wav".format(i))
                with WavReader(src) as reader:
                    with WavWriter(out, reader.channels, reader.samplerate) as writer:
                        tsm = phasevocoder(reader.channels, speed=speed)
                        tsm.run(reader, writer)

                sub_clip = sub_clip.fx(vfx.speedx, speed)
                sub_clip = sub_clip.set_audio(AudioFileClip(out))
                clips.append(sub_clip)
                if i % 5 == 0:
                    print("Modifying Chunks: " + str(round((i / len(chunks) * 100), 2)) + "% Complete.")

        output_clip = concatenate_videoclips(clips)
        output_clip.write_videofile(os.path.join(outputPath, video), threads=8, preset='ultrafast')
        print("Success!")
        print("Output is stored in: " + os.path.join(outputPath, video))

        # DANGEROUS
        shutil.rmtree(tempPath)
        tok = time.time()
        print("Took " + str(tok - tik) + " seconds.")

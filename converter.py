import pyrealsense2 as rs
import numpy as np
import cv2
from os import makedirs
from os.path import exists, join
import shutil
import json
from enum import IntEnum


class Preset(IntEnum):
    Custom = 0
    Default = 1
    Hand = 2
    HighAccuracy = 3
    HighDensity = 4
    MediumDensity = 5


def make_clean_folder(path_folder):
    if not exists(path_folder):
        makedirs(path_folder)
    else:
        # user_input = input("%s not empty. Overwrite? (y/n) : " % path_folder)
        # if user_input.lower() == 'y':
        shutil.rmtree(path_folder)
        makedirs(path_folder)
        # else:
        #     exit()


def save_intrinsic_as_json(filename, frame):
    intrinsics = frame.profile.as_video_stream_profile().intrinsics
    with open(filename, 'w') as outfile:
        obj = json.dump(
            {
                'width':
                    intrinsics.width,
                'height':
                    intrinsics.height,
                'intrinsic_matrix': [
                    intrinsics.fx, 0, 0, 0, intrinsics.fy, 0, intrinsics.ppx,
                    intrinsics.ppy, 1
                ]
            },
            outfile,
            indent=4)


def run_convert(output_folder, file_path):
    path_depth = join(output_folder, "depth")
    path_color = join(output_folder, "color")
    print(path_depth, path_color)
    make_clean_folder(output_folder)
    make_clean_folder(path_depth)
    make_clean_folder(path_color)

    # Create a pipeline
    pipeline = rs.pipeline()

    # Create a config and configure the pipeline to stream
    #  different resolutions of color and depth streams
    config = rs.config()
    # note: using 640 x 480 depth resolution produces smooth depth boundaries
    #       using rs.format.bgr8 for color image format for OpenCV based image visualization
    # config.enable_stream(rs.stream.depth, 1280, 720, rs.format.z16, 30)
    # config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
    config.enable_device_from_file(file_path, repeat_playback=False)
    # Start streaming
    profile = pipeline.start(config)
    # depth_sensor = profile.get_device().first_depth_sensor()

    # Using preset HighAccuracy for recording
    # if args.record_rosbag or args.record_imgs:
    #     depth_sensor.set_option(rs.option.visual_preset, Preset.HighAccuracy)

    # Getting the depth sensor's depth scale (see rs-align example for explanation)
    # depth_scale = depth_sensor.get_depth_scale()

    # We will not display the background of objects more than
    #  clipping_distance_in_meters meters away
    # clipping_distance_in_meters = 3  # 3 meter
    # clipping_distance = clipping_distance_in_meters / depth_scale

    # Create an align object
    # rs.align allows us to perform alignment of depth frames to others frames
    # The "align_to" is the stream type to which we plan to align depth frames.
    align_to = rs.stream.color
    align = rs.align(align_to)

    # Streaming loop
    frame_count = 0
    try:
        while True:
            # Get frameset of color and depth
            success, frames = pipeline.try_wait_for_frames(timeout_ms=1000)
            if not success:
                break
            # Align the depth frame to color frame
            aligned_frames = align.process(frames)

            # Get aligned frames
            aligned_depth_frame = aligned_frames.get_depth_frame()
            color_frame = aligned_frames.get_color_frame()

            # Validate that both frames are valid
            if not aligned_depth_frame or not color_frame:
                continue

            depth_image = np.asanyarray(aligned_depth_frame.get_data())
            color_image = np.asanyarray(color_frame.get_data())

            if frame_count == 0:
                save_intrinsic_as_json(
                    join(output_folder, "camera_intrinsic.json"),
                    color_frame)
            cv2.imwrite("%s/%06d.png" % \
                        (path_depth, frame_count), depth_image)
            cv2.imwrite("%s/%06d.jpg" % \
                        (path_color, frame_count), color_image)
            print("Saved color + depth image %06d" % frame_count)
            frame_count += 1

    finally:
        pipeline.stop()


if __name__ == '__main__':
    run_convert("temp/test", "upload/20191123_223819.bag")

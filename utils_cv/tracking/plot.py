# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from collections import OrderedDict
import os.path as osp
from typing import Dict, List, Tuple
import cv2
import numpy as np

from .bbox import TrackingBbox


def plot_results(
    results: Dict[int, List[TrackingBbox]],
    input_video: str,
    output_video: str,
) -> None:
    """ 
    Plot the predicted tracks on the input video. Write the output to {output_path}.
    
    Args:
        results: dictionary mapping frame id to a list of predicted TrackingBboxes
        input_video: path to the input video
        output_video: path to the output video
    """
    _write_video(
        OrderedDict(sorted(results.items())),
        input_video,
        output_video,
    )

    print(f"Output saved to {output_video}.")

    return output_video


def _write_video(
    results: Dict[int, List[TrackingBbox]], input_video: str, output_video: str
) -> None:
    """     
    Args:
        results: dictionary mapping frame id to a list of predicted TrackingBboxes
        input_video: path to the input video
        output_video: path to write out the output video
    """

    # read video and initialize new tracking video
    video = cv2.VideoCapture()
    video.open(input_video)

    image_width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    image_height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fourcc = cv2.VideoWriter_fourcc(*"MP4V")
    frame_rate = int(video.get(cv2.CAP_PROP_FPS))
    writer = cv2.VideoWriter(
        output_video, fourcc, frame_rate, (image_width, image_height)
    )

    # assign bbox color per id
    unique_ids = list(set([bb.track_id for frame in results.values() for bb in frame]))
    color_map = _compute_color_for_all_labels(unique_ids)

    # create images and add to video writer, adapted from https://github.com/ZQPei/deep_sort_pytorch
    frame_idx = 0
    while video.grab():
        _, cur_image = video.retrieve()
        cur_tracks = results[frame_idx]
        if len(cur_tracks) > 0:
            cur_image = _draw_boxes(cur_image, cur_tracks, color_map)
        writer.write(cur_image)
        frame_idx += 1


def _draw_boxes(
    im: np.ndarray,
    cur_tracks: List[TrackingBbox],
    color_map: Dict[int, Tuple[int, int, int]],
) -> np.ndarray:
    """ 
    Overlay bbox and id labels onto the frame
    Args:
        im: raw frame
        cur_tracks: list of bboxes in the current frame
        color_map: dictionary mapping ids to bbox colors
    """

    cur_ids = [bb.track_id for bb in cur_tracks]
    tracks = dict(zip(cur_ids, cur_tracks))

    for tid, bb in tracks.items():
        left = round(bb.left)
        top = round(bb.top)
        right = round(bb.right)
        bottom = round(bb.bottom)

        # box text and bar
        color = color_map[tid]
        label = str(tid)

        # last two args of getTextSize() are font_scale and thickness
        t_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 1, 1)[0]
        cv2.rectangle(im, (left, top), (right, bottom), color, 3)
        cv2.putText(
            im,
            "id_" + label,
            (left, top + t_size[1] - 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            color,
            3,
        )

    return im


def _compute_color_for_all_labels(
    id_list: List[int],
) -> Dict[int, Tuple[int, int, int]]:
    """ 
    Produce corresponding unique color palettes for unique ids
    
    Args:
        id_list: list of track ids 
    """
    palette = (2 ** 11 - 1, 2 ** 15 - 1, 2 ** 20 - 1)

    color_list = []
    id_list2 = list(range(len(id_list)))

    # adapted from https://github.com/ZQPei/deep_sort_pytorch
    for i in id_list2:
        color = [int((p * ((i + 1) ** 5 - i + 1)) % 255) for p in palette]
        color_list.append(tuple(color))

    color_map = dict(zip(id_list, color_list))

    return color_map

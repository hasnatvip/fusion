from functools import lru_cache
from typing import List, Tuple

from facefusion import inference_manager, state_manager
from facefusion.execution import has_execution_provider
from facefusion.common_helper import is_macos
from facefusion.types import DownloadScope, DownloadSet, ExecutionProvider, Fps, InferencePool, ModelSet, VisionFrame

STREAM_COUNTER = 0


@lru_cache()
def create_static_model_set(download_scope : DownloadScope) -> ModelSet:
	return {}


def get_inference_pool() -> InferencePool:
	return inference_manager.get_inference_pool(__name__, [], {})


def clear_inference_pool() -> None:
	pass


def resolve_execution_providers() -> List[ExecutionProvider]:
	if is_macos() and has_execution_provider('coreml'):
		return [ 'cpu' ]
	return state_manager.get_item('execution_providers')


def collect_model_downloads() -> Tuple[DownloadSet, DownloadSet]:
	return {}, {}


def pre_check() -> bool:
	return True


def analyse_stream(vision_frame : VisionFrame, video_fps : Fps) -> bool:
	return False


def analyse_frame(vision_frame : VisionFrame) -> bool:
	return False


@lru_cache()
def analyse_image(image_path : str) -> bool:
	return False


@lru_cache()
def analyse_video(video_path : str, trim_frame_start : int, trim_frame_end : int) -> bool:
	return False


def detect_nsfw(vision_frame : VisionFrame) -> bool:
	return False


import gradio
from typing import Optional, Tuple

from facefusion import state_manager
from facefusion.generators import wan_video
from facefusion.uis.core import register_ui_component
from facefusion.uis import ui_helper

WAN_LOCAL_GENERATOR_SOURCE_IMAGE : Optional[gradio.Image] = None
WAN_LOCAL_GENERATOR_PROMPT_TEXTBOX : Optional[gradio.Textbox] = None
WAN_LOCAL_GENERATOR_MODEL_PATH_TEXTBOX : Optional[gradio.Textbox] = None
WAN_LOCAL_GENERATOR_START_BUTTON : Optional[gradio.Button] = None
WAN_LOCAL_GENERATOR_OUTPUT_VIDEO : Optional[gradio.Video] = None
WAN_LOCAL_GENERATOR_STATUS_LABEL : Optional[gradio.Label] = None

def render() -> None:
	global WAN_LOCAL_GENERATOR_SOURCE_IMAGE
	global WAN_LOCAL_GENERATOR_PROMPT_TEXTBOX
	global WAN_LOCAL_GENERATOR_MODEL_PATH_TEXTBOX
	global WAN_LOCAL_GENERATOR_START_BUTTON
	global WAN_LOCAL_GENERATOR_OUTPUT_VIDEO
	global WAN_LOCAL_GENERATOR_STATUS_LABEL

	with gradio.Group():
		WAN_LOCAL_GENERATOR_SOURCE_IMAGE = gradio.Image(
			label = 'Source Image',
			type = 'filepath'
		)
		WAN_LOCAL_GENERATOR_PROMPT_TEXTBOX = gradio.Textbox(
			label = 'Prompt',
			lines = 3,
			placeholder = 'Describe the motion...'
		)
		WAN_LOCAL_GENERATOR_MODEL_PATH_TEXTBOX = gradio.Textbox(
			label = 'Model Path (Optional)',
			placeholder = 'Path to local model folder (leave empty to download)...'
		)
	WAN_LOCAL_GENERATOR_START_BUTTON = gradio.Button(
		value = 'Generate Video (Local)',
		variant = 'primary'
	)
	WAN_LOCAL_GENERATOR_STATUS_LABEL = gradio.Label(
		value = 'Ready',
		label = 'Status',
		visible = False
	)
	WAN_LOCAL_GENERATOR_OUTPUT_VIDEO = gradio.Video(
		label = 'Generated Video',
		interactive = False
	)

	register_ui_component('wan_local_generator_source_image', WAN_LOCAL_GENERATOR_SOURCE_IMAGE)
	register_ui_component('wan_local_generator_prompt_textbox', WAN_LOCAL_GENERATOR_PROMPT_TEXTBOX)
	register_ui_component('wan_local_generator_model_path_textbox', WAN_LOCAL_GENERATOR_MODEL_PATH_TEXTBOX)
	register_ui_component('wan_local_generator_start_button', WAN_LOCAL_GENERATOR_START_BUTTON)
	register_ui_component('wan_local_generator_output_video', WAN_LOCAL_GENERATOR_OUTPUT_VIDEO)

def listen() -> None:
	WAN_LOCAL_GENERATOR_START_BUTTON.click(
		start, 
		inputs = [ WAN_LOCAL_GENERATOR_SOURCE_IMAGE, WAN_LOCAL_GENERATOR_PROMPT_TEXTBOX, WAN_LOCAL_GENERATOR_MODEL_PATH_TEXTBOX ], 
		outputs = [ WAN_LOCAL_GENERATOR_STATUS_LABEL, WAN_LOCAL_GENERATOR_OUTPUT_VIDEO ]
	)

def start(source_image_path : str, prompt : str, model_path : str) ->  Tuple[gradio.Label, Optional[str]]:
	if not source_image_path or not prompt:
		return gradio.Label(value = 'Missing Input', visible=True), None
	
	output_path = state_manager.get_item('output_path')
	import os
	from facefusion.filesystem import is_directory
	import time
	
	if is_directory(output_path):
		output_path = os.path.join(output_path, f'wan_local_{int(time.time())}.mp4')
	elif not output_path.endswith('.mp4'):
		output_path += '.mp4'

	# We can't easily stream "Downloading 10%" updates from backend to here without a complex yield loop
	# So we just say "Processing..."
	# In a real heavy app we'd use a generator.
	
	if wan_video.generate_video(source_image_path, prompt, output_path, model_path):
		return gradio.Label(value = 'Success', visible=True), output_path
	
	return gradio.Label(value = 'Failed (Check Terminal)', visible=True), None

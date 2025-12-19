from typing import Optional
try:
	import torch
	from diffusers import DiffusionPipeline
except ImportError as exception:
	torch = None
	DiffusionPipeline = None
	print(f"Wan video import failed: {exception}")
from facefusion import logger
from facefusion.filesystem import is_file

# Default model ID - correct Hugging Face repository for Wan 2.1 I2V
MODEL_ID = "Wan-AI/Wan2.1-I2V-14B-720P-Diffusers" 
PIPELINE = None

def load_model(model_id : Optional[str] = None) -> bool:
	global PIPELINE
	if PIPELINE is not None:
		return True
	
	if torch is None or DiffusionPipeline is None:
		logger.error('Wan model dependencies missing. Run: pip install -r requirements.txt', __name__)
		return False

	try:
		device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
		# Use float16 for GPU/MPS, float32 for CPU
		dtype = torch.float16 if device != "cpu" else torch.float32
		
		# On Apple Silicon, bfloat16 is sometimes better, but float16 is widely supported in diffusers for MPS
		logger.info(f'Loading Wan model from {model_id if model_id else MODEL_ID} on {device}. This may take a while...', __name__)
		
		model_id_or_path = model_id if model_id else MODEL_ID
        
		PIPELINE = DiffusionPipeline.from_pretrained(
			model_id_or_path,
			torch_dtype=dtype,
			use_safetensors=True
		)
		
		if device == "cuda":
			PIPELINE.enable_model_cpu_offload()
		else:
			PIPELINE.to(device)

		logger.info(f'Wan model loaded successfully on {device}.', __name__)
		return True
	except Exception as exception:
		logger.error(f'Failed to load Wan model: {exception}', __name__)
		return False

def generate_video(source_image_path : str, prompt : str, output_path : str, model_path : Optional[str] = None) -> bool:
	global PIPELINE
	
	if not load_model(model_path):
		return False

	try:
		from facefusion.vision import read_static_image
		from PIL import Image
		import numpy as np

		# Helper to convert cv2 image (numpy) to PIL
		vision_frame = read_static_image(source_image_path)
		if vision_frame is None:
			logger.error(f'Could not read source image: {source_image_path}', __name__)
			return False
			
		# Convert BGR (cv2) to RGB (PIL)
		source_image = Image.fromarray(vision_frame[:, :, ::-1])

		logger.info(f'Generating video for prompt: {prompt}', __name__)
		
		# Wan I2V generation
		# Note: The exact pipeline args depend on the specific diffusers implementation for Wan.
		# Assuming standard I2V pipeline structure.
		video_frames = PIPELINE(
			image=source_image,
			prompt=prompt,
			height=480, # Defaulting to standard resolutions
			width=832,
			num_frames=81, # ~3-4 seconds at 24fps
			num_inference_steps=50,
			guidance_scale=7.5
		).frames[0]

		# Save video using facefusion's ffmpeg tools or directly export from diffusers helper if available.
		# Here we export quickly using diffusers export_to_video which is common, 
		# or manually write frames. Let's use export_to_video utility.
		from diffusers.utils import export_to_video
		export_to_video(video_frames, output_path, fps=24)
		
		logger.info(f'Video generated successfully: {output_path}', __name__)
		return True

	except Exception as exception:
		logger.error(f'Wan video generation failed: {exception}', __name__)
		return False

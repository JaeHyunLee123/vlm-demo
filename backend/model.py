"""Direct Qwen2.5-VL-3B-Instruct Candidate Refrigerant Type reader."""

from __future__ import annotations

import logging

from PIL import Image

MODEL_ID = "Qwen/Qwen2.5-VL-3B-Instruct"
PROMPT = """Read only the refrigerant designation that is explicitly legible on this air-conditioner outdoor-unit nameplate.
Return exactly one JSON object and no other text: {\"refrigerant_type\": \"R-410A\"}.
Use a designation only when it is directly and confidently readable. If it is absent, unclear, ambiguous, there are multiple possible values, or this is not a nameplate, return {\"refrigerant_type\": null}. Do not infer."""
logger = logging.getLogger(__name__)


class QwenCandidateReader:
    """Loads the Inference Model once and returns its raw structured response."""

    def __init__(self) -> None:
        import torch
        from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration

        self._model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
            MODEL_ID,
            torch_dtype=torch.float16,
            device_map="auto",
        )
        self._processor = AutoProcessor.from_pretrained(MODEL_ID)
        self._first_analysis = True

    def __call__(self, image: Image.Image) -> str:
        from qwen_vl_utils import process_vision_info

        if self._first_analysis:
            logger.info("Cold Analysis: first request on this GPU worker")
            self._first_analysis = False
        else:
            logger.info("Warm Analysis: model already loaded on this GPU worker")

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": image},
                    {"type": "text", "text": PROMPT},
                ],
            }
        ]
        prompt = self._processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        image_inputs, video_inputs = process_vision_info(messages)
        inputs = self._processor(
            text=[prompt],
            images=image_inputs,
            videos=video_inputs,
            padding=True,
            return_tensors="pt",
        ).to("cuda")
        generated_ids = self._model.generate(**inputs, max_new_tokens=32, do_sample=False)
        completion_ids = [
            output_ids[len(input_ids) :]
            for input_ids, output_ids in zip(inputs.input_ids, generated_ids, strict=True)
        ]
        return self._processor.batch_decode(completion_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)[0]

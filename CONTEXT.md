# Refrigerant Nameplate Analysis

This context identifies the refrigerant stated on an air-conditioner outdoor-unit nameplate. It distinguishes confirmed reading results from every form of non-confirmation so the demo never invents a refrigerant type.

## Language

**Nameplate Image**:
An uploaded photograph of an air-conditioner outdoor unit's specification label.
_Avoid_: Air-conditioner image, equipment photo

**Refrigerant Type**:
The refrigerant designation explicitly legible on a Nameplate Image, such as R-32 or R-410A.
_Avoid_: Gas type, coolant type

**Analysis Success**:
A result in which the Refrigerant Type is explicitly and confidently read from the Nameplate Image.
_Avoid_: Best guess, inferred result

**Analysis Failure**:
A result in which no Refrigerant Type can be confidently read, including an unreadable image, absent designation, or non-nameplate image.
_Avoid_: Unknown refrigerant

**Analysis Time**:
The elapsed server time after receiving a Nameplate Image to run model inference and validate its result.
_Avoid_: Upload time, total request time

**Shared API Key**:
The single six-character secret required to submit a Nameplate Image to the demo API.
_Avoid_: User API key, account token

**Cold Analysis**:
An analysis that starts a GPU worker and loads the model because no warm worker is available.
_Avoid_: Standard analysis

**Warm Analysis**:
An analysis performed by a worker that already has the model loaded.
_Avoid_: Cached result

**Inference Model**:
The fixed open-weight VLM that reads a Nameplate Image and produces a candidate Refrigerant Type. The initial model is Qwen2.5-VL-3B-Instruct.
_Avoid_: OCR engine, external AI API

**Supported Image**:
A JPEG, PNG, or WebP Nameplate Image no larger than 10 MB, normalized to a longest edge of at most 1,920 pixels before inference.
_Avoid_: Raw upload

**Candidate Refrigerant Type**:
A single refrigerant designation produced by the Inference Model before the server determines whether it satisfies Analysis Success.
_Avoid_: Result, confirmed refrigerant

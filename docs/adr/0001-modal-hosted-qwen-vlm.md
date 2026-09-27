# Host Qwen2.5-VL-3B-Instruct on Modal GPU workers

The demo will run the open-weight Qwen2.5-VL-3B-Instruct model directly on Modal T4 GPU workers, rather than call an external VLM API or operate an EC2 instance. Modal's Python-native deployment meets the no-Docker-development constraint, scales to zero to control POC cost, and provides the deployment logs and usage visibility needed for the demo.

## Considered Options

- External VLM API: rejected because it would not measure the cost and latency of directly operating the model.
- GPU EC2: rejected for the demo because manual server operation would add setup and monitoring work.
- Modal L4 GPU: retained as a fallback only if T4 accuracy or latency tests on the sample images are inadequate.

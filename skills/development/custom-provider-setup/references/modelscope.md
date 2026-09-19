# ModelScope Provider Notes

## Endpoint

- Base URL: `https://api-inference.modelscope.cn/v1`
- Auth: `Authorization: Bearer <MODELSCOPE_API_KEY>` (standard OpenAI-compatible)
- API keys generated at: https://modelscope.cn/my/myaccesstoken

## Account Binding Requirement

ModelScope's inference API requires users to bind an Alibaba Cloud account before any
chat completions work. Without binding:

- `/v1/models` returns data successfully (auth passes)
- `/v1/chat/completions` returns:
  `{"error":{"message":"Please bind your Alibaba Cloud account before use."}}`

Fix: user must log in at https://modelscope.cn, go to profile settings, and complete
"绑定阿里云账号" (Bind Alibaba Cloud Account). Alibaba Cloud account creation:
https://account.alibabacloud.com/register/register.htm

This is NOT a config error or invalid key — do not retry or debug further.

## Available Models (sample, as of 2026-09)

- Qwen/Qwen3-235B-A22B, Qwen/Qwen3-8B, Qwen/Qwen3-14B, Qwen/Qwen3-30B-A3B
- Qwen/Qwen3-235B-A22B-Thinking-2507, Qwen/Qwen3-Coder-30B-A3B-Instruct
- Qwen/Qwen3-VL-235B-A22B-Instruct, Qwen/Qwen3.5-122B-A10B
- deepseek-ai/DeepSeek-V4-Pro, deepseek-ai/DeepSeek-V4-Flash-0731
- MiniMax/MiniMax-M3, mistralai/Mistral-Large-Instruct-2407
- OpenGVLab/InternVL3_5-241B-A28B

Model IDs use the `namespace/model-name` format (HuggingFace-style).

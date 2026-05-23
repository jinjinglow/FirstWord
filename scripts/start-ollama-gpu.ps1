param(
    [string]$GpuId = "0",
    [string]$HostUrl = "127.0.0.1:11434"
)

$env:CUDA_VISIBLE_DEVICES = $GpuId
$env:OLLAMA_HOST = $HostUrl

Write-Host "Starting Ollama with CUDA_VISIBLE_DEVICES=$GpuId and OLLAMA_HOST=$HostUrl"
Write-Host "Leave this window open while using the app."
Write-Host "After Qwen is used, verify with: ollama ps"
Write-Host "The PROCESSOR column should show GPU or CPU/GPU."

ollama serve

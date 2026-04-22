$env:OPENAI_API_KEY="sk-proj-...your_key_here..."
$headers = @{ Authorization = "Bearer $env:OPENAI_API_KEY" }
Invoke-RestMethod https://api.openai.com/v1/models -Headers $headers

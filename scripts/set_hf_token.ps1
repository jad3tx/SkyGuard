# PowerShell script to set Hugging Face token as a user environment variable
# This makes it persistent across sessions

param(
    [Parameter(Mandatory=$false)]
    [string]$Token
)

if (-not $Token) {
    Write-Host "Usage: .\scripts\set_hf_token.ps1 -Token 'your_token_here'"
    Write-Host ""
    Write-Host "Or run interactively:"
    $Token = Read-Host -Prompt "Enter your Hugging Face token (input will be hidden)" -AsSecureString
    $TokenPtr = [System.Runtime.Interopservices.Marshal]::SecureStringToBSTR($Token)
    $Token = [System.Runtime.Interopservices.Marshal]::PtrToStringAuto($TokenPtr)
}

# Set as user environment variable (persistent)
[System.Environment]::SetEnvironmentVariable('HF_TOKEN', $Token, [System.EnvironmentVariableTarget]::User)

Write-Host "✅ HF_TOKEN environment variable set successfully!"
Write-Host ""
Write-Host "The token will be available in all future PowerShell sessions."
Write-Host "To verify, run: echo `$env:HF_TOKEN"
Write-Host ""
Write-Host "Note: You may need to restart your terminal for it to take effect."


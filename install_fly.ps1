$response = Invoke-RestMethod -Uri "https://api.github.com/repos/superfly/flyctl/releases/latest"
$asset = $response.assets | Where-Object { $_.name -like "*Windows_x86_64.zip" } | Select-Object -First 1
$url = $asset.browser_download_url
Write-Host "Downloading $url"
Invoke-WebRequest -Uri $url -OutFile "$env:USERPROFILE\flyctl.zip"
Expand-Archive -Path "$env:USERPROFILE\flyctl.zip" -DestinationPath "$env:USERPROFILE\.fly\bin" -Force
Get-ChildItem -Path "$env:USERPROFILE\.fly\bin"

param()

$packRoot = "C:\Users\Edia\Documents\Project-mc\plugins\story\resourcepack"
$zipOut = "C:\Users\Edia\Documents\Project-mc\plugins\story\resourcepack\MalamSMP_StoryVN.zip"

if (Test-Path $zipOut) {
    Remove-Item -Force $zipOut
}

$tempFolder = Join-Path $env:TEMP ("vn_pack_" + [System.IO.Path]::GetRandomFileName())
New-Item -ItemType Directory -Path $tempFolder | Out-Null

Copy-Item -Path (Join-Path $packRoot "pack.mcmeta") -Destination $tempFolder
Copy-Item -Path (Join-Path $packRoot "pack.png") -Destination $tempFolder
Copy-Item -Path (Join-Path $packRoot "assets") -Destination $tempFolder -Recurse

Compress-Archive -Path (Join-Path $tempFolder "*") -DestinationPath $zipOut -Force
Remove-Item -Path $tempFolder -Recurse -Force

Write-Output ("Packaged: " + (Get-Item $zipOut).Length + " bytes at " + $zipOut)


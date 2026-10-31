param()

$src = "C:\Users\Edia\Documents\Project-mc\plugins\story\resourcepack"
$destFolder = "C:\ATLauncher\instances\262\resourcepacks\MalamSMP_StoryVN"
$destZip = "C:\ATLauncher\instances\262\resourcepacks\MalamSMP_StoryVN.zip"

if (Test-Path $destFolder) {
    Remove-Item -Recurse -Force $destFolder
}
New-Item -ItemType Directory -Force -Path $destFolder | Out-Null

Copy-Item -Path (Join-Path $src "pack.mcmeta") -Destination $destFolder
Copy-Item -Path (Join-Path $src "pack.png") -Destination $destFolder
Copy-Item -Path (Join-Path $src "assets") -Destination $destFolder -Recurse

Copy-Item -Path (Join-Path $src "MalamSMP_StoryVN.zip") -Destination $destZip -Force

Write-Output "Successfully installed MalamSMP_StoryVN to ATLauncher!"


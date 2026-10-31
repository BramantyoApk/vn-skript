param()

$packRoot = "C:\Users\Edia\Documents\Project-mc\plugins\story\resourcepack"
$atlauncherFolder = "C:\ATLauncher\instances\262\resourcepacks\MalamSMP_StoryVN"
$atlauncherZip = "C:\ATLauncher\instances\262\resourcepacks\MalamSMP_StoryVN.zip"
$localZip = Join-Path $packRoot "MalamSMP_StoryVN.zip"


Write-Output "--- [1/2] Deploying Folder to ATLauncher ($atlauncherFolder) ---"
if (Test-Path $atlauncherFolder) {
    Remove-Item -Recurse -Force $atlauncherFolder
}
New-Item -ItemType Directory -Force -Path $atlauncherFolder | Out-Null

Copy-Item -Path (Join-Path $packRoot "pack.mcmeta") -Destination $atlauncherFolder -Force
Copy-Item -Path (Join-Path $packRoot "pack.png") -Destination $atlauncherFolder -Force
Copy-Item -Path (Join-Path $packRoot "assets") -Destination $atlauncherFolder -Recurse -Force

Write-Output "--- [2/2] Compressing to ZIP Archive ($atlauncherZip) ---"
if (Test-Path $localZip) { Remove-Item -Force $localZip }
if (Test-Path $atlauncherZip) { Remove-Item -Force $atlauncherZip }

$tempFolder = Join-Path $env:TEMP ("malam_pack_" + [System.IO.Path]::GetRandomFileName())
New-Item -ItemType Directory -Path $tempFolder | Out-Null

Copy-Item -Path (Join-Path $packRoot "pack.mcmeta") -Destination $tempFolder
Copy-Item -Path (Join-Path $packRoot "pack.png") -Destination $tempFolder
Copy-Item -Path (Join-Path $packRoot "assets") -Destination $tempFolder -Recurse

Compress-Archive -Path (Join-Path $tempFolder "*") -DestinationPath $localZip -Force
Copy-Item -Path $localZip -Destination $atlauncherZip -Force
Remove-Item -Path $tempFolder -Recurse -Force

# Clean up older redundant standalone zips if present
$oldZips = @("MalamSMP_StoryVN.zip", "MalamSMP_StoryVN")
foreach ($old in $oldZips) {
    $p = "C:\ATLauncher\instances\262\resourcepacks\$old"
    if (Test-Path $p) {
        Remove-Item -Recurse -Force $p -ErrorAction SilentlyContinue
    }
}

Write-Output "MalamSMP_StoryVN successfully deployed to ATLauncher!"
Write-Output "Folder: $atlauncherFolder"
Write-Output "Zip: $atlauncherZip"


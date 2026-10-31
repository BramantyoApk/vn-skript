param()

$fontSrc = "C:\Users\Edia\Documents\Project-mc\plugins\story\resourcepack\assets\minecraft\textures\font"
$msmpFontDest = "C:\ATLauncher\instances\262\resourcepacks\MalamSMP_StoryVN\assets\minecraft\textures\font"

if (-not (Test-Path $msmpFontDest)) {
    New-Item -ItemType Directory -Force -Path $msmpFontDest | Out-Null
}

Get-ChildItem -Path $fontSrc -Filter "*.png" | ForEach-Object {
    Copy-Item -Path $_.FullName -Destination $msmpFontDest -Force
    Write-Output ("Copied " + $_.Name + " to MalamSMP_StoryVN textures/font/")
}

$msmpJsonPath = "C:\ATLauncher\instances\262\resourcepacks\MalamSMP_StoryVN\assets\minecraft\font\default.json"
$mergedJson = @'
{
  "providers": [
    {
      "type": "bitmap",
      "file": "minecraft:font/ruby.png",
      "ascent": 7,
      "height": 8,
      "chars": [
        "\uE201"
      ]
    },
    {
      "type": "bitmap",
      "file": "minecraft:font/ruby.png",
      "ascent": 7,
      "height": 8,
      "chars": [
        "\uE200"
      ]
    },
    {
      "type": "bitmap",
      "file": "minecraft:font/ruby.png",
      "ascent": 7,
      "height": 8,
      "chars": [
        "\uE001"
      ]
    },
    {
      "type": "bitmap",
      "file": "minecraft:font/dialogue_box.png",
      "ascent": -10,
      "height": 64,
      "chars": [
        "\uE101"
      ]
    },
    {
      "type": "bitmap",
      "file": "minecraft:font/nameplate.png",
      "ascent": -30,
      "height": 20,
      "chars": [
        "\uE102"
      ]
    },
    {
      "type": "bitmap",
      "file": "minecraft:font/portrait_luna.png",
      "ascent": -10,
      "height": 48,
      "chars": [
        "\uE110"
      ]
    },
    {
      "type": "bitmap",
      "file": "minecraft:font/portrait_bob.png",
      "ascent": -10,
      "height": 48,
      "chars": [
        "\uE111"
      ]
    },
    {
      "type": "bitmap",
      "file": "minecraft:font/portrait_ghost.png",
      "ascent": -10,
      "height": 48,
      "chars": [
        "\uE112"
      ]
    },
    {
      "type": "space",
      "advances": {
        " ": 4,
        "\uF801": -1,
        "\uF802": -2,
        "\uF803": -3,
        "\uF804": -4,
        "\uF805": -5,
        "\uF806": -6,
        "\uF807": -7,
        "\uF808": -8,
        "\uF809": -16,
        "\uF80A": -32,
        "\uF80B": -64,
        "\uF80C": -128,
        "\uF80D": -256,
        "\uF80E": -512,
        "\uF821": 1,
        "\uF822": 2,
        "\uF823": 3,
        "\uF824": 4,
        "\uF825": 5,
        "\uF826": 6,
        "\uF827": 7,
        "\uF828": 8,
        "\uF829": 16,
        "\uF82A": 32,
        "\uF82B": 64,
        "\uF82C": 128,
        "\uF82D": 256
      }
    }
  ]
}
'@

Set-Content -Path $msmpJsonPath -Value $mergedJson -Encoding UTF8
Write-Output "default.json in MalamSMP_StoryVN updated successfully!"

# Clean up redundant MalamSMP_StoryVN in ATLauncher to prevent red tag confusion
$oldPackFolder = "C:\ATLauncher\instances\262\resourcepacks\MalamSMP_StoryVN"
$oldPackZip = "C:\ATLauncher\instances\262\resourcepacks\MalamSMP_StoryVN.zip"
if (Test-Path $oldPackFolder) { Remove-Item -Recurse -Force $oldPackFolder }
if (Test-Path $oldPackZip) { Remove-Item -Force $oldPackZip }
Write-Output "Old stand-alone pack cleaned up!"


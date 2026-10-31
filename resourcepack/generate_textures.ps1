Add-Type -AssemblyName System.Drawing

$fontDir = "C:\Users\Edia\Documents\Project-mc\plugins\story\resourcepack\assets\minecraft\textures\font"
if (-not (Test-Path $fontDir)) {
    New-Item -ItemType Directory -Force -Path $fontDir | Out-Null
}

$bgBrush = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(210, 16, 20, 28))
$goldPen = [System.Drawing.Pen]::new([System.Drawing.Color]::FromArgb(255, 218, 165, 32), 2)
$gemBrush = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(255, 0, 220, 255))

# 1. Dialogue Box: 256 x 64
$bmpBox = [System.Drawing.Bitmap]::new(256, 64)
$g = [System.Drawing.Graphics]::FromImage($bmpBox)
$g.Clear([System.Drawing.Color]::Transparent)
$g.FillRectangle($bgBrush, 4, 4, 248, 56)
$g.DrawRectangle($goldPen, 4, 4, 248, 56)
$innerPen = [System.Drawing.Pen]::new([System.Drawing.Color]::FromArgb(180, 255, 215, 0), 1)
$g.DrawRectangle($innerPen, 6, 6, 244, 52)
$g.FillRectangle($gemBrush, 3, 3, 4, 4)
$g.FillRectangle($gemBrush, 249, 3, 4, 4)
$g.FillRectangle($gemBrush, 3, 57, 4, 4)
$g.FillRectangle($gemBrush, 249, 57, 4, 4)
$g.Dispose()
$bmpBox.Save((Join-Path $fontDir "dialogue_box.png"), [System.Drawing.Imaging.ImageFormat]::Png)
$bmpBox.Dispose()

# 2. Nameplate: 80 x 20
$bmpName = [System.Drawing.Bitmap]::new(80, 20)
$gn = [System.Drawing.Graphics]::FromImage($bmpName)
$gn.Clear([System.Drawing.Color]::Transparent)
$gn.FillRectangle($bgBrush, 2, 2, 76, 16)
$gn.DrawRectangle($goldPen, 2, 2, 76, 16)
$gn.Dispose()
$bmpName.Save((Join-Path $fontDir "nameplate.png"), [System.Drawing.Imaging.ImageFormat]::Png)
$bmpName.Dispose()

# 3. Portrait Luna: 48 x 48
$bmpLuna = [System.Drawing.Bitmap]::new(48, 48)
$gl = [System.Drawing.Graphics]::FromImage($bmpLuna)
$gl.Clear([System.Drawing.Color]::Transparent)
$gl.FillRectangle([System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(220, 25, 30, 40)), 2, 2, 44, 44)
$gl.DrawRectangle($goldPen, 2, 2, 44, 44)
$gl.FillEllipse([System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(255, 60, 110, 165)), 8, 8, 32, 34)
$gl.FillEllipse([System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(255, 255, 224, 189)), 14, 14, 20, 22)
$gl.FillEllipse([System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(255, 235, 195, 100)), 13, 11, 22, 12)
$gl.FillRectangle([System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(255, 46, 139, 87)), 18, 22, 3, 4)
$gl.FillRectangle([System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(255, 46, 139, 87)), 27, 22, 3, 4)
$gl.FillRectangle([System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(255, 205, 110, 110)), 22, 29, 4, 2)
$gl.Dispose()
$bmpLuna.Save((Join-Path $fontDir "portrait_luna.png"), [System.Drawing.Imaging.ImageFormat]::Png)
$bmpLuna.Dispose()

# 4. Portrait Bob: 48 x 48
$bmpBob = [System.Drawing.Bitmap]::new(48, 48)
$gb = [System.Drawing.Graphics]::FromImage($bmpBob)
$gb.Clear([System.Drawing.Color]::Transparent)
$gb.FillRectangle([System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(220, 25, 30, 40)), 2, 2, 44, 44)
$gb.DrawRectangle($goldPen, 2, 2, 44, 44)
$gb.FillEllipse([System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(255, 218, 165, 32)), 6, 8, 36, 14)
$gb.FillEllipse([System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(255, 180, 130, 20)), 12, 4, 24, 12)
$gb.FillEllipse([System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(255, 240, 200, 160)), 14, 16, 20, 22)
$gb.FillRectangle([System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(255, 50, 40, 30)), 18, 22, 3, 3)
$gb.FillRectangle([System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(255, 50, 40, 30)), 27, 22, 3, 3)
$gb.FillRectangle([System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(255, 100, 60, 25)), 19, 28, 10, 3)
$gb.Dispose()
$bmpBob.Save((Join-Path $fontDir "portrait_bob.png"), [System.Drawing.Imaging.ImageFormat]::Png)
$bmpBob.Dispose()

# 5. Portrait Ghost: 48 x 48
$bmpGhost = [System.Drawing.Bitmap]::new(48, 48)
$gg = [System.Drawing.Graphics]::FromImage($bmpGhost)
$gg.Clear([System.Drawing.Color]::Transparent)
$gg.FillRectangle([System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(220, 15, 10, 25)), 2, 2, 44, 44)
$ghostPen = [System.Drawing.Pen]::new([System.Drawing.Color]::FromArgb(255, 138, 43, 226), 2)
$gg.DrawRectangle($ghostPen, 2, 2, 44, 44)
$gg.FillEllipse([System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(255, 35, 35, 45)), 12, 10, 24, 26)
$cyanBrush = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(255, 0, 255, 230))
$gg.FillRectangle($cyanBrush, 17, 20, 4, 4)
$gg.FillRectangle($cyanBrush, 27, 20, 4, 4)
$gg.FillRectangle($cyanBrush, 21, 28, 6, 2)
$gg.Dispose()
$bmpGhost.Save((Join-Path $fontDir "portrait_ghost.png"), [System.Drawing.Imaging.ImageFormat]::Png)
$bmpGhost.Dispose()

$bgBrush.Dispose()
$goldPen.Dispose()
$ghostPen.Dispose()
$gemBrush.Dispose()
$cyanBrush.Dispose()

Write-Output "Textures Generated Successfully!"

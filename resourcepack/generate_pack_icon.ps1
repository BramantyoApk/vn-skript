Add-Type -AssemblyName System.Drawing

$packPng = "C:\Users\Edia\Documents\Project-mc\plugins\story\resourcepack\pack.png"
$bmp = [System.Drawing.Bitmap]::new(128, 128)
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.Clear([System.Drawing.Color]::FromArgb(255, 20, 24, 35))

# Golden border
$pen = [System.Drawing.Pen]::new([System.Drawing.Color]::FromArgb(255, 218, 165, 32), 4)
$g.DrawRectangle($pen, 4, 4, 120, 120)

# Inner book / dialogue box icon
$boxBrush = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(255, 35, 42, 60))
$g.FillRectangle($boxBrush, 16, 20, 96, 70)
$innerPen = [System.Drawing.Pen]::new([System.Drawing.Color]::FromArgb(255, 255, 215, 0), 2)
$g.DrawRectangle($innerPen, 16, 20, 96, 70)

# Cyan glowing gem in center
$gemBrush = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(255, 0, 240, 255))
$g.FillEllipse($gemBrush, 56, 45, 16, 16)

# Text banner area
$textBrush = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(255, 255, 215, 0))
$font = [System.Drawing.Font]::new([System.Drawing.FontFamily]::GenericSansSerif, 10, [System.Drawing.FontStyle]::Bold)
$format = [System.Drawing.StringFormat]::new()
$format.Alignment = [System.Drawing.StringAlignment]::Center
$g.DrawString("STORY VN HUD", $font, $textBrush, 64, 98, $format)

$g.Dispose()
$bmp.Save($packPng, [System.Drawing.Imaging.ImageFormat]::Png)
$bmp.Dispose()
$pen.Dispose()
$boxBrush.Dispose()
$innerPen.Dispose()
$gemBrush.Dispose()
$textBrush.Dispose()
$font.Dispose()
$format.Dispose()

Write-Output "pack.png created successfully!"

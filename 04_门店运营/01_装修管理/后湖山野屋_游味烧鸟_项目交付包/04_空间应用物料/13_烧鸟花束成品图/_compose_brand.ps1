Add-Type -AssemblyName System.Drawing

$basePath = Join-Path $PSScriptRoot '02_烧鸟花束_去手美化版_无字.png'
$logoPath = Join-Path $PSScriptRoot '..\..\03_VI视觉系统\01_Logo文件_待放入\00_当前采用_V2_标准组合_透明底.png'
$outPath = Join-Path $PSScriptRoot '03_烧鸟花束_去手美化版_品牌海报.png'

$base = [System.Drawing.Bitmap]::FromFile($basePath)
$logo = [System.Drawing.Bitmap]::FromFile($logoPath)
$canvas = New-Object System.Drawing.Bitmap($base.Width, $base.Height, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
$graphics = [System.Drawing.Graphics]::FromImage($canvas)
$graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
$graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
$graphics.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
$graphics.DrawImage($base, 0, 0, $base.Width, $base.Height)

$badgeWidth = [int]($base.Width * 0.60)
$badgeHeight = [int]($badgeWidth * 0.43)
$badgeX = [int](($base.Width - $badgeWidth) / 2)
$badgeY = [int]($base.Height * 0.035)
$badgeRect = New-Object System.Drawing.Rectangle($badgeX, $badgeY, $badgeWidth, $badgeHeight)
$badgeBrush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(235, 237, 219, 188))
$graphics.FillRectangle($badgeBrush, $badgeRect)

$logoInset = [int]($badgeWidth * 0.055)
$logoRect = New-Object System.Drawing.Rectangle(($badgeX + $logoInset), ($badgeY + [int]($badgeHeight * 0.06)), ($badgeWidth - 2 * $logoInset), [int]($badgeHeight * 0.88))
$graphics.DrawImage($logo, $logoRect)

$canvas.Save($outPath, [System.Drawing.Imaging.ImageFormat]::Png)
$badgeBrush.Dispose()
$graphics.Dispose()
$canvas.Dispose()
$logo.Dispose()
$base.Dispose()

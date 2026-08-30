Add-Type -AssemblyName System.Drawing

$basePath = Join-Path $PSScriptRoot '05_真实串型扩充_VI夜景_无字.png'
$logoPath = Join-Path $PSScriptRoot '..\..\03_VI视觉系统\01_Logo文件_待放入\00_当前采用_V2_标准组合_透明底.png'
$outPath = Join-Path $PSScriptRoot '06_真实串型扩充_VI夜景_品牌版.png'

$base = [System.Drawing.Bitmap]::FromFile($basePath)
$logo = [System.Drawing.Bitmap]::FromFile($logoPath)
$canvas = New-Object System.Drawing.Bitmap($base.Width, $base.Height, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
$graphics = [System.Drawing.Graphics]::FromImage($canvas)
$graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
$graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
$graphics.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
$graphics.DrawImage($base, 0, 0, $base.Width, $base.Height)

$logoWidth = [int]($base.Width * 0.46)
$logoHeight = [int]($logoWidth * $logo.Height / $logo.Width)
$logoX = [int]($base.Width * 0.435)
$logoY = [int]($base.Height * 0.14)
$logoRect = New-Object System.Drawing.Rectangle($logoX, $logoY, $logoWidth, $logoHeight)
$graphics.DrawImage($logo, $logoRect)

$canvas.Save($outPath, [System.Drawing.Imaging.ImageFormat]::Png)
$graphics.Dispose()
$canvas.Dispose()
$logo.Dispose()
$base.Dispose()

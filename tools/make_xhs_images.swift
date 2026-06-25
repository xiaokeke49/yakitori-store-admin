import AppKit
import Foundation

struct Job {
    let source: String
    let output: String
    let title: String?
    let subtitle: String?
    let focusY: CGFloat
}

let root = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
let canvas = CGSize(width: 1080, height: 1440)

func url(_ path: String) -> URL {
    root.appendingPathComponent(path)
}

func loadImage(_ path: String) -> NSImage {
    guard let image = NSImage(contentsOf: url(path)) else {
        fatalError("Cannot load image: \(path)")
    }
    return image
}

func drawCoverText(title: String, subtitle: String?) {
    let paragraph = NSMutableParagraphStyle()
    paragraph.alignment = .left
    paragraph.lineBreakMode = .byWordWrapping

    let titleAttrs: [NSAttributedString.Key: Any] = [
        .font: NSFont.systemFont(ofSize: 76, weight: .semibold),
        .foregroundColor: NSColor.white,
        .paragraphStyle: paragraph
    ]
    let subtitleAttrs: [NSAttributedString.Key: Any] = [
        .font: NSFont.systemFont(ofSize: 38, weight: .medium),
        .foregroundColor: NSColor.white.withAlphaComponent(0.92),
        .paragraphStyle: paragraph
    ]

    let x: CGFloat = 72
    let titleRect = CGRect(x: x, y: 1040, width: 820, height: 220)
    NSString(string: title).draw(in: titleRect, withAttributes: titleAttrs)

    if let subtitle, !subtitle.isEmpty {
        let subtitleRect = CGRect(x: x, y: 980, width: 820, height: 70)
        NSString(string: subtitle).draw(in: subtitleRect, withAttributes: subtitleAttrs)
    }
}

func drawGradient() {
    guard let ctx = NSGraphicsContext.current?.cgContext else { return }
    let colors = [
        NSColor.black.withAlphaComponent(0.46).cgColor,
        NSColor.black.withAlphaComponent(0.16).cgColor,
        NSColor.black.withAlphaComponent(0.00).cgColor
    ] as CFArray
    let locations: [CGFloat] = [0, 0.56, 1]
    guard let gradient = CGGradient(colorsSpace: CGColorSpaceCreateDeviceRGB(), colors: colors, locations: locations) else {
        return
    }
    ctx.drawLinearGradient(
        gradient,
        start: CGPoint(x: 0, y: canvas.height),
        end: CGPoint(x: 0, y: canvas.height * 0.48),
        options: []
    )
}

func sourceRect(for image: NSImage, focusY: CGFloat) -> CGRect {
    let src = image.size
    let targetRatio = canvas.width / canvas.height
    let srcRatio = src.width / src.height

    if srcRatio > targetRatio {
        let width = src.height * targetRatio
        let x = max(0, (src.width - width) / 2)
        return CGRect(x: x, y: 0, width: width, height: src.height)
    }

    let height = src.width / targetRatio
    let extra = max(0, src.height - height)
    let y = min(max(extra * focusY, 0), extra)
    return CGRect(x: 0, y: y, width: src.width, height: height)
}

func render(_ job: Job) {
    let image = loadImage(job.source)
    let rep = NSBitmapImageRep(
        bitmapDataPlanes: nil,
        pixelsWide: Int(canvas.width),
        pixelsHigh: Int(canvas.height),
        bitsPerSample: 8,
        samplesPerPixel: 4,
        hasAlpha: true,
        isPlanar: false,
        colorSpaceName: .deviceRGB,
        bytesPerRow: 0,
        bitsPerPixel: 0
    )!

    NSGraphicsContext.saveGraphicsState()
    NSGraphicsContext.current = NSGraphicsContext(bitmapImageRep: rep)
    NSColor.black.setFill()
    CGRect(origin: .zero, size: canvas).fill()

    image.draw(
        in: CGRect(origin: .zero, size: canvas),
        from: sourceRect(for: image, focusY: job.focusY),
        operation: .copy,
        fraction: 1.0
    )

    if let title = job.title {
        drawGradient()
        drawCoverText(title: title, subtitle: job.subtitle)
    }

    NSGraphicsContext.restoreGraphicsState()

    guard let data = rep.representation(using: .jpeg, properties: [.compressionFactor: 0.92]) else {
        fatalError("Cannot encode output: \(job.output)")
    }
    let out = url(job.output)
    try! FileManager.default.createDirectory(at: out.deletingLastPathComponent(), withIntermediateDirectories: true)
    try! data.write(to: out)
}

let jobs: [Job] = [
    Job(source: "output/2026-06-08/小红书/01/images/01_湖边茶饮.jpg", output: "output/2026-06-08/小红书/01/xhs_images/01_封面_后湖茶饮烧鸟.jpg", title: "后湖边\n茶饮 + 烧鸟", subtitle: "傍晚来坐一会儿", focusY: 0.42),
    Job(source: "output/2026-06-08/小红书/01/images/02_湖边座位.jpg", output: "output/2026-06-08/小红书/01/xhs_images/02_湖边座位.jpg", title: nil, subtitle: nil, focusY: 0.5),
    Job(source: "output/2026-06-08/小红书/01/images/03_湖边落日.png", output: "output/2026-06-08/小红书/01/xhs_images/03_湖边落日.jpg", title: nil, subtitle: nil, focusY: 0.56),
    Job(source: ".tmp_xhs_normalized/01_04.jpg", output: "output/2026-06-08/小红书/01/xhs_images/04_烧鸟食材.jpg", title: nil, subtitle: nil, focusY: 0.45),
    Job(source: "output/2026-06-08/小红书/01/images/05_炭火烤制.jpg", output: "output/2026-06-08/小红书/01/xhs_images/05_炭火烤制.jpg", title: nil, subtitle: nil, focusY: 0.46),
    Job(source: "output/2026-06-08/小红书/01/images/06_成品特写.jpg", output: "output/2026-06-08/小红书/01/xhs_images/06_成品特写.jpg", title: nil, subtitle: nil, focusY: 0.45),

    Job(source: ".tmp_xhs_normalized/02/01.jpg", output: "output/2026-06-08/小红书/02/xhs_images/01_封面_第一次这样点.jpg", title: "第一次来\n可以这样点", subtitle: "后湖烧鸟点单建议", focusY: 0.48),
    Job(source: ".tmp_xhs_normalized/02/02.jpg", output: "output/2026-06-08/小红书/02/xhs_images/02_食材柜全景.jpg", title: nil, subtitle: nil, focusY: 0.48),
    Job(source: ".tmp_xhs_normalized/02/03.jpg", output: "output/2026-06-08/小红书/02/xhs_images/03_推荐串类.jpg", title: nil, subtitle: nil, focusY: 0.44),
    Job(source: "output/2026-06-08/小红书/02/images/04_烤制过程.jpg", output: "output/2026-06-08/小红书/02/xhs_images/04_烤制过程.jpg", title: nil, subtitle: nil, focusY: 0.46),
    Job(source: "output/2026-06-08/小红书/02/images/05_烧鸟成品.jpg", output: "output/2026-06-08/小红书/02/xhs_images/05_烧鸟成品.jpg", title: nil, subtitle: nil, focusY: 0.45),
    Job(source: "output/2026-06-08/小红书/02/images/06_夜间摊位.jpg", output: "output/2026-06-08/小红书/02/xhs_images/06_夜间摊位.jpg", title: nil, subtitle: nil, focusY: 0.5),

    Job(source: "output/2026-06-08/小红书/03/images/01_夜间摊位.jpg", output: "output/2026-06-08/小红书/03/xhs_images/01_封面_后湖摆摊日记.jpg", title: "后湖边\n摆摊日记", subtitle: "茶饮和烧鸟慢慢来", focusY: 0.5),
    Job(source: "output/2026-06-08/小红书/03/images/02_湖边茶饮.jpg", output: "output/2026-06-08/小红书/03/xhs_images/02_湖边茶饮.jpg", title: nil, subtitle: nil, focusY: 0.45),
    Job(source: ".tmp_xhs_normalized/03/03.jpg", output: "output/2026-06-08/小红书/03/xhs_images/03_备串食材.jpg", title: nil, subtitle: nil, focusY: 0.47),
    Job(source: "output/2026-06-08/小红书/03/images/04_生火烤串.jpg", output: "output/2026-06-08/小红书/03/xhs_images/04_生火烤串.jpg", title: nil, subtitle: nil, focusY: 0.46),
    Job(source: "output/2026-06-08/小红书/03/images/05_湖边落日.png", output: "output/2026-06-08/小红书/03/xhs_images/05_湖边落日.jpg", title: nil, subtitle: nil, focusY: 0.56),
    Job(source: "output/2026-06-08/小红书/03/images/06_成品小吃.jpg", output: "output/2026-06-08/小红书/03/xhs_images/06_成品小吃.jpg", title: nil, subtitle: nil, focusY: 0.45)
]

for job in jobs {
    render(job)
    print(job.output)
}

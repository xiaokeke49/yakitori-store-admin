import AppKit
import Photos
import AVFoundation
import ImageIO

struct ImportFailure: LocalizedError {
    let message: String
    var errorDescription: String? { message }
}
func fail(_ text: String) -> ImportFailure { ImportFailure(message: text) }
func validate(_ directory: URL) throws -> (URL, URL, String) {
    let jpg = directory.appendingPathComponent("Fridge_Live.JPG")
    let mov = directory.appendingPathComponent("Fridge_Live.mov")
    guard FileManager.default.fileExists(atPath: jpg.path), FileManager.default.fileExists(atPath: mov.path),
          let source = CGImageSourceCreateWithURL(jpg as CFURL, nil),
          let props = CGImageSourceCopyPropertiesAtIndex(source, 0, nil) as? [String: Any],
          let maker = props[kCGImagePropertyMakerAppleDictionary as String] as? [String: Any],
          let id = maker["17"] as? String, !id.isEmpty else {
        throw fail("请选择包含配对 Fridge_Live.JPG 与 Fridge_Live.mov 的文件夹；照片缺失或配对标识无效。")
    }
    let asset = AVURLAsset(url: mov)
    let videoID = asset.metadata.first { $0.identifier == .quickTimeMetadataContentIdentifier }?.stringValue
    guard id == videoID else { throw fail("照片与视频的配对标识不一致，未导入。") }
    var complete = false, valid = false
    let request = PHLivePhoto.request(withResourceFileURLs: [jpg, mov], placeholderImage: nil, targetSize: CGSize(width: 270, height: 360), contentMode: .aspectFit) { live, info in
        if (info[PHLivePhotoInfoIsDegradedKey] as? Bool) == true { return }
        valid = live != nil
        complete = true
    }
    let deadline = Date().addingTimeInterval(30)
    while !complete && Date() < deadline { RunLoop.current.run(until: Date().addingTimeInterval(0.05)) }
    if !complete { PHLivePhoto.cancelRequest(withRequestID: request) }
    guard valid else { throw fail("PhotoKit未识别为有效实况照片，未写入图库。") }
    return (jpg, mov, id)
}
func alert(_ title: String, _ text: String, confirm: Bool = false) -> Bool {
    let a = NSAlert(); a.messageText = title; a.informativeText = text
    a.addButton(withTitle: confirm ? "导入一张实况照片" : "好")
    if confirm { a.addButton(withTitle: "取消") }
    return a.runModal() == .alertFirstButtonReturn
}

// Read-only validation: never requests Photos library access or imports.
if CommandLine.arguments.count == 3 && CommandLine.arguments[1] == "--check" {
    do {
        let (_, _, id) = try validate(URL(fileURLWithPath: CommandLine.arguments[2], isDirectory: true))
        print("配对验证通过：\(id)；未申请图库权限、未导入。")
        exit(0)
    } catch { fputs("\(error.localizedDescription)\n", stderr); exit(1) }
}

let direct = CommandLine.arguments.count == 3 && CommandLine.arguments[1] == "--import"
let app = NSApplication.shared
app.setActivationPolicy(.regular)
app.finishLaunching()
app.activate(ignoringOtherApps: true)
let panel = NSOpenPanel()
panel.title = "选择Live Photo成品文件夹"
panel.message = "选择同时包含 Fridge_Live.JPG 与 Fridge_Live.mov 的文件夹。不要选择MP4预览。"
panel.canChooseFiles = false; panel.canChooseDirectories = true; panel.allowsMultipleSelection = false
var chosenDirectory: URL
if direct { chosenDirectory = URL(fileURLWithPath: CommandLine.arguments[2], isDirectory: true) }
else {
    if panel.runModal() != .OK { exit(0) }
    chosenDirectory = panel.url!
}
do {
    let (jpg, mov, id) = try validate(chosenDirectory)
    guard direct || alert("导入Mac照片图库", "将配对照片和视频作为一个实况照片项目写入系统照片图库。不会删除原文件或先前误导入的照片/视频。\n\n需要照片读写权限，以验证新项目的LIVE类型及避免重复导入；不会遍历其他照片。", confirm: true) else { exit(0) }
    var authorization: PHAuthorizationStatus?
    PHPhotoLibrary.requestAuthorization(for: .readWrite) { authorization = $0 }
    while authorization == nil { RunLoop.current.run(until: Date().addingTimeInterval(0.1)) }
    guard authorization == .authorized else { throw fail("没有获得照片读写权限，未导入。可在系统设置→隐私与安全性→照片中允许“冰箱实况导入器”后重试。") }
    let receiptsKey = "importedLiveAssetIDs"
    var receipts = UserDefaults.standard.dictionary(forKey: receiptsKey) as? [String: String] ?? [:]
    if let previous = receipts[id] {
        if let existing = PHAsset.fetchAssets(withLocalIdentifiers: [previous], options: nil).firstObject {
            if existing.mediaSubtypes.contains(.photoLive) {
                _ = alert("已导入，未重复添加", "同一组文件已经导入为实况照片。请在照片App的“媒体类型→实况照片”中查看。")
                exit(0)
            }
            throw fail("之前导入的项目存在，但未识别为LIVE。为避免重复添加，本次停止，请核对照片App。")
        }
        throw fail("已有导入成功记录，但暂时无法读取对应项目。它可能已删除、在另一图库或尚未同步；为避免重复添加，本次停止。")
    }
    var localID: String?
    try PHPhotoLibrary.shared().performChangesAndWait {
        let request = PHAssetCreationRequest.forAsset()
        let photoOptions = PHAssetResourceCreationOptions(); photoOptions.shouldMoveFile = false
        let videoOptions = PHAssetResourceCreationOptions(); videoOptions.shouldMoveFile = false
        request.addResource(with: .photo, fileURL: jpg, options: photoOptions)
        request.addResource(with: .pairedVideo, fileURL: mov, options: videoOptions)
        localID = request.placeholderForCreatedAsset?.localIdentifier
    }
    guard let newID = localID else { throw fail("图库写入完成但未返回项目ID。请先检查照片App，不要立即重复导入。") }
    receipts[id] = newID
    UserDefaults.standard.set(receipts, forKey: receiptsKey)
    let created = PHAsset.fetchAssets(withLocalIdentifiers: [newID], options: nil).firstObject
    guard let created = created, created.mediaSubtypes.contains(.photoLive) else {
        throw fail("图库写入已完成，但LIVE类型未通过回读验证。已保存导入记录防止重复，请在照片App检查。")
    }
    let report: [String: Any] = ["imported": true, "photoLive": true, "localIdentifier": newID, "pairIdentifier": id, "time": ISO8601DateFormatter().string(from: Date())]
    let reportData = try JSONSerialization.data(withJSONObject: report, options: [.prettyPrinted, .sortedKeys])
    try reportData.write(to: chosenDirectory.appendingPathComponent("导入结果.json"), options: .atomic)
    _ = alert("已导入一张实况照片", "已从图库回读确认LIVE类型。\n\n打开照片App→媒体类型→实况照片，找到展示柜照片并播放。然后从照片App隔空投送至iPhone，或使用已启用的iCloud照片同步。\n\n小红书上传预览仍需检查LIVE标识。本程序没有上传或发布。")
} catch { _ = alert("导入未完成或需核对", error.localizedDescription); exit(1) }

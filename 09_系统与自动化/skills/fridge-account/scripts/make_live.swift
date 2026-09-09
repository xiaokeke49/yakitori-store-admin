import AppKit
import Foundation
import AVFoundation
import CoreImage
import ImageIO
import UniformTypeIdentifiers
import Photos

guard CommandLine.arguments.count == 3 else {
    fputs("Usage: make_live INPUT OUTPUT_DIRECTORY\n", stderr)
    exit(2)
}
let source = URL(fileURLWithPath: CommandLine.arguments[1])
let folder = URL(fileURLWithPath: CommandLine.arguments[2], isDirectory: true)
let mov = folder.appendingPathComponent("Fridge_Live.mov")
let jpg = folder.appendingPathComponent("Fridge_Live.JPG")
let identifier = UUID().uuidString
let width = 1080, height = 1440, fps: Int32 = 30, frameCount = 90
let context = CIContext(options: [.cacheIntermediates: false])
guard let original = CIImage(contentsOf: source, options: [.applyOrientationProperty: true]) else { fatalError("Source image unreadable") }
let baseScale = max(CGFloat(width)/original.extent.width, CGFloat(height)/original.extent.height)
func frame(_ n: Int) -> CIImage {
    let seconds = Double(n)/Double(fps)
    let t = min(seconds / 1.05, 1.0)
    let ease = t*t*(3-2*t)
    let settling = exp(-seconds*1.1)
    let scale = baseScale * CGFloat(1.02 + 0.09*ease + 0.0015*sin(seconds*5.1))
    let image = original.transformed(by: CGAffineTransform(scaleX: scale, y: scale))
    let dx = CGFloat(5.0*sin(seconds*6.3)*settling + 1.2*sin(seconds*2.7))
    let dy = CGFloat(3.5*sin(seconds*8.1)*settling + 0.8*sin(seconds*3.1))
    return image.transformed(by: CGAffineTransform(translationX: (CGFloat(width)-image.extent.width)/2-image.extent.origin.x+dx, y: (CGFloat(height)-image.extent.height)/2-image.extent.origin.y+dy)).cropped(to: CGRect(x:0,y:0,width:width,height:height))
}
func saveJPEG(_ image: CIImage, _ url: URL, paired: Bool) {
    let cg = context.createCGImage(image, from: image.extent)!
    let destination = CGImageDestinationCreateWithURL(url as CFURL, UTType.jpeg.identifier as CFString, 1, nil)!
    var properties: [CFString:Any] = [kCGImageDestinationLossyCompressionQuality:0.96]
    if paired { properties[kCGImagePropertyMakerAppleDictionary] = ["17": identifier] }
    CGImageDestinationAddImage(destination, cg, properties as CFDictionary)
    precondition(CGImageDestinationFinalize(destination))
}
saveJPEG(frame(45),jpg,paired:true)
saveJPEG(frame(0),folder.appendingPathComponent("check_start.jpg"),paired:false)
saveJPEG(frame(89),folder.appendingPathComponent("check_end.jpg"),paired:false)
let writer = try AVAssetWriter(outputURL:mov,fileType:.mov)
let input = AVAssetWriterInput(mediaType:.video,outputSettings:[AVVideoCodecKey:AVVideoCodecType.h264,AVVideoWidthKey:width,AVVideoHeightKey:height,AVVideoCompressionPropertiesKey:[AVVideoAverageBitRateKey:10_000_000,AVVideoExpectedSourceFrameRateKey:fps,AVVideoMaxKeyFrameIntervalKey:30]])
input.expectsMediaDataInRealTime=false
let pixels = AVAssetWriterInputPixelBufferAdaptor(assetWriterInput:input,sourcePixelBufferAttributes:[kCVPixelBufferPixelFormatTypeKey as String:kCVPixelFormatType_32BGRA,kCVPixelBufferWidthKey as String:width,kCVPixelBufferHeightKey as String:height,kCVPixelBufferIOSurfacePropertiesKey as String:[:]])
writer.add(input)
let idItem = AVMutableMetadataItem()
idItem.identifier = AVMetadataIdentifier.quickTimeMetadataContentIdentifier
idItem.value = identifier as NSString
writer.metadata = [idItem]
let spec:[String:Any] = [kCMMetadataFormatDescriptionMetadataSpecificationKey_Identifier as String:"mdta/com.apple.quicktime.still-image-time",kCMMetadataFormatDescriptionMetadataSpecificationKey_DataType as String:"com.apple.metadata.datatype.int8"]
var format:CMFormatDescription?
precondition(CMMetadataFormatDescriptionCreateWithMetadataSpecifications(allocator:kCFAllocatorDefault,metadataType:kCMMetadataFormatType_Boxed,metadataSpecifications:[spec] as CFArray,formatDescriptionOut:&format)==noErr)
let metadataInput = AVAssetWriterInput(mediaType:.metadata,outputSettings:nil,sourceFormatHint:format)
let metadata = AVAssetWriterInputMetadataAdaptor(assetWriterInput:metadataInput)
writer.add(metadataInput)
precondition(writer.startWriting())
writer.startSession(atSourceTime:.zero)
let marker = AVMutableMetadataItem()
marker.keySpace = .quickTimeMetadata
marker.key = "com.apple.quicktime.still-image-time" as NSString
marker.value = NSNumber(value:Int8(0))
marker.dataType = "com.apple.metadata.datatype.int8"
precondition(metadata.append(AVTimedMetadataGroup(items:[marker],timeRange:CMTimeRange(start:CMTime(value:45,timescale:fps),duration:CMTime(value:1,timescale:fps)))))
metadataInput.markAsFinished()
for i in 0..<frameCount {
    while !input.isReadyForMoreMediaData {
        if writer.status == .failed { fatalError(writer.error!.localizedDescription) }
        Thread.sleep(forTimeInterval:0.005)
    }
    try autoreleasepool {
        var buffer:CVPixelBuffer?
        precondition(CVPixelBufferPoolCreatePixelBuffer(nil,pixels.pixelBufferPool!,&buffer)==kCVReturnSuccess)
        context.render(frame(i),to:buffer!,bounds:CGRect(x:0,y:0,width:width,height:height),colorSpace:CGColorSpace(name:CGColorSpace.sRGB)!)
        if !pixels.append(buffer!,withPresentationTime:CMTime(value:Int64(i),timescale:fps)) { throw writer.error! }
    }
}
input.markAsFinished()
writer.endSession(atSourceTime:CMTime(value:3,timescale:1))
let done = DispatchSemaphore(value:0)
writer.finishWriting { done.signal() }
done.wait()
precondition(writer.status == .completed,writer.error?.localizedDescription ?? "write failed")
let asset = AVURLAsset(url:mov)
let props=CGImageSourceCopyPropertiesAtIndex(CGImageSourceCreateWithURL(jpg as CFURL,nil)!,0,nil)! as NSDictionary
let photoID = (props[kCGImagePropertyMakerAppleDictionary] as? NSDictionary)?["17"] as? String
let videoID = asset.metadata.first(where:{$0.identifier == .quickTimeMetadataContentIdentifier})?.stringValue
precondition(photoID==identifier && videoID==identifier)
let tracks=asset.tracks(withMediaType:.metadata)
precondition(tracks.count==1)
let reader=try AVAssetReader(asset:asset)
let metaOut=AVAssetReaderTrackOutput(track:tracks[0],outputSettings:nil)
reader.add(metaOut);precondition(reader.startReading())
var stillMarkerTime: Double?
while let sample = metaOut.copyNextSampleBuffer() {
 if let group=AVTimedMetadataGroup(sampleBuffer:sample), !group.items.isEmpty { stillMarkerTime=group.timeRange.start.seconds }
}
precondition(stillMarkerTime != nil && abs(stillMarkerTime!-1.5)<0.001,"Timed metadata marker missing")
let export=AVAssetExportSession(asset:asset,presetName:AVAssetExportPresetHighestQuality)!
export.outputURL=folder.appendingPathComponent("推近效果预览.mp4")
export.outputFileType = .mp4
let exported=DispatchSemaphore(value:0)
export.exportAsynchronously { exported.signal() };exported.wait()
precondition(export.status == .completed)
var result:[String:Any] = ["asset_identifier":identifier,"duration_seconds":asset.duration.seconds,"width":width,"height":height,"frames":frameCount,"zoom":"1.02 to 1.11 in 1.05 seconds, then settle; subtle handheld translation","key_photo_seconds":1.5,"pair_metadata_valid":true,"source":source.path,"xiaohongshu_verified":false]
var validationFinished=false
PHLivePhoto.request(withResourceFileURLs:[jpg,mov],placeholderImage:nil,targetSize:CGSize(width:270,height:360),contentMode:.aspectFit) { live, info in
    if (info[PHLivePhotoInfoIsDegradedKey] as? Bool)==true { return }
    result["photokit_recognized"] = live != nil
    if let error=info[PHLivePhotoInfoErrorKey] { result["photokit_error"]="\(error)" }
    validationFinished=true
}
let deadline=Date().addingTimeInterval(30)
while !validationFinished && Date()<deadline { RunLoop.current.run(until:Date().addingTimeInterval(0.1)) }
if !validationFinished { result["photokit_recognized"] = false; result["photokit_error"]="validation timed out" }
let data=try JSONSerialization.data(withJSONObject:result,options:[.prettyPrinted,.sortedKeys,.withoutEscapingSlashes])
try data.write(to:folder.appendingPathComponent("验证结果.json"))
print(String(data:data,encoding:.utf8)!)

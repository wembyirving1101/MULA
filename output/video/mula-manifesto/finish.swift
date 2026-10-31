import Foundation
import AVFoundation
import ImageIO

let root=CommandLine.arguments[1]
let composition=AVMutableComposition()
let video=AVURLAsset(url:URL(fileURLWithPath:root+"/picture-120fps.mp4"))
let rawAudio=AVURLAsset(url:URL(fileURLWithPath:root+"/soundtrack.wav"))
let audioExport=AVAssetExportSession(asset:rawAudio,presetName:AVAssetExportPresetAppleM4A)!
audioExport.outputURL=URL(fileURLWithPath:root+"/soundtrack.m4a")
audioExport.outputFileType = .m4a
let audioSem=DispatchSemaphore(value:0)
audioExport.exportAsynchronously { audioSem.signal() }
audioSem.wait()
guard audioExport.status == .completed else {fatalError("Audio export failed: \(String(describing:audioExport.error))")}
let audio=AVURLAsset(url:audioExport.outputURL!)
let range=CMTimeRange(start:.zero,duration:CMTime(value:65,timescale:1))
guard let vt=video.tracks(withMediaType:.video).first,let at=audio.tracks(withMediaType:.audio).first else {fatalError("Input tracks missing")}
let cv=composition.addMutableTrack(withMediaType:.video,preferredTrackID:kCMPersistentTrackID_Invalid)!
try cv.insertTimeRange(range,of:vt,at:.zero)
let ca=composition.addMutableTrack(withMediaType:.audio,preferredTrackID:kCMPersistentTrackID_Invalid)!
try ca.insertTimeRange(range,of:at,at:.zero)
// Pass through the encoded picture; the frame rate must remain 120 fps.
let exporter=AVAssetExportSession(asset:composition,presetName:AVAssetExportPresetPassthrough)!
exporter.outputURL=URL(fileURLWithPath:root+"/mula-manifesto-1080p120.mp4")
exporter.outputFileType = .mp4
exporter.shouldOptimizeForNetworkUse=true
let semaphore=DispatchSemaphore(value:0)
exporter.exportAsynchronously { semaphore.signal() }
semaphore.wait()
guard exporter.status == .completed else {fatalError("Mux failed: \(String(describing:exporter.error))")}
let final=AVURLAsset(url:exporter.outputURL!)
let track=final.tracks(withMediaType:.video).first!
let reader=try AVAssetReader(asset:final)
let output=AVAssetReaderTrackOutput(track:track,outputSettings:nil)
reader.add(output)
guard reader.startReading() else {fatalError("Read failed")}
var frames=0
while let sample=output.copyNextSampleBuffer(){frames+=CMSampleBufferGetNumSamples(sample)}
guard reader.status == .completed else {fatalError("Verification failed")}
let report="Duration: \(CMTimeGetSeconds(final.duration)) seconds\nDimensions: \(track.naturalSize)\nNominal frame rate: \(track.nominalFrameRate) fps\nVideo samples: \(frames)\nAudio tracks: \(final.tracks(withMediaType:.audio).count)\n"
print(report)
try report.write(toFile:root+"/verification.txt",atomically:true,encoding:.utf8)
guard frames == 7800,track.nominalFrameRate == 120,track.naturalSize.width == 1920,track.naturalSize.height == 1080 else {fatalError("Output does not match target")}
let generator=AVAssetImageGenerator(asset:final)
generator.appliesPreferredTrackTransform=true
for (i,t) in [6.0,27.5,48.2,64.5].enumerated(){
    let cg=try generator.copyCGImage(at:CMTime(seconds:t,preferredTimescale:120),actualTime:nil)
    let dest=CGImageDestinationCreateWithURL(URL(fileURLWithPath:root+"/assets/encoded-\(i).jpg") as CFURL,"public.jpeg" as CFString,1,nil)!
    CGImageDestinationAddImage(dest,cg,nil);CGImageDestinationFinalize(dest)
}

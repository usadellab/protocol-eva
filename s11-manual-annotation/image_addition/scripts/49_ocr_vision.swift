// OCR with Apple's Vision framework (no extra install): prints one recognised text line per output line.
//   swiftc -O 49_ocr_vision.swift -o /tmp/ocr_vision   then   ocr_vision <image.png> [--rotate]   (--rotate: also read the image turned 90 degrees, for vertical labels)
import Foundation
import Vision
import AppKit

func lines(_ cg: CGImage) -> [String] {
    let req = VNRecognizeTextRequest()
    req.recognitionLevel = .accurate
    req.usesLanguageCorrection = false
    try? VNImageRequestHandler(cgImage: cg, options: [:]).perform([req])
    return (req.results ?? []).compactMap { $0.topCandidates(1).first?.string }
}
func rotated(_ cg: CGImage, clockwise: Bool) -> CGImage? {
    let w = cg.height, h = cg.width
    guard let ctx = CGContext(data: nil, width: w, height: h, bitsPerComponent: 8, bytesPerRow: 0,
                              space: CGColorSpaceCreateDeviceRGB(), bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue) else { return nil }
    ctx.translateBy(x: CGFloat(w) / 2, y: CGFloat(h) / 2)
    ctx.rotate(by: clockwise ? -.pi / 2 : .pi / 2)
    ctx.draw(cg, in: CGRect(x: -CGFloat(cg.width) / 2, y: -CGFloat(cg.height) / 2, width: CGFloat(cg.width), height: CGFloat(cg.height)))
    return ctx.makeImage()
}
let args = CommandLine.arguments
guard args.count >= 2, let img = NSImage(contentsOfFile: args[1]),
      let cg = img.cgImage(forProposedRect: nil, context: nil, hints: nil) else { FileHandle.standardError.write("cannot read image\n".data(using: .utf8)!); exit(2) }
var out = lines(cg)
if args.contains("--rotate") {
    for cw in [true, false] { if let r = rotated(cg, clockwise: cw) { out += lines(r) } }
}
print(out.joined(separator: "\n"))

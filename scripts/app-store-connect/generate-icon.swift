import AppKit
let output = CommandLine.arguments[1]
let context = CGContext(data: nil, width: 1024, height: 1024, bitsPerComponent: 8, bytesPerRow: 4096, space: CGColorSpaceCreateDeviceRGB(), bitmapInfo: CGImageAlphaInfo.noneSkipLast.rawValue)!
NSGraphicsContext.saveGraphicsState()
NSGraphicsContext.current = NSGraphicsContext(cgContext: context, flipped: false)
NSColor(calibratedRed: 40/255, green: 83/255, blue: 62/255, alpha: 1).setFill()
NSBezierPath(rect: NSRect(x: 0, y: 0, width: 1024, height: 1024)).fill()
NSColor(calibratedRed: 245/255, green: 245/255, blue: 232/255, alpha: 1).setFill()
NSBezierPath(ovalIn: NSRect(x: 170, y: 170, width: 684, height: 684)).fill()
let green = NSColor(calibratedRed: 40/255, green: 83/255, blue: 62/255, alpha: 1)
green.withAlphaComponent(0.22).setStroke()
let rim = NSBezierPath(ovalIn: NSRect(x: 228, y: 228, width: 568, height: 568)); rim.lineWidth = 5; rim.stroke()
green.setFill()
func capsule(_ x: CGFloat, _ y: CGFloat, _ w: CGFloat, _ h: CGFloat) {
 NSBezierPath(roundedRect: NSRect(x: x, y: y, width: w, height: h), xRadius: w/2, yRadius: w/2).fill()
}
capsule(395, 324, 34, 315)
for x: CGFloat in [362,395,428] { capsule(x, 577, 20, 130) }
NSBezierPath(roundedRect: NSRect(x: 362, y: 545, width: 86, height: 65), xRadius: 26, yRadius: 26).fill()
capsule(580, 324, 34, 340)
let knife = NSBezierPath(); knife.move(to: NSPoint(x: 614, y: 708)); knife.curve(to: NSPoint(x: 553, y: 531), controlPoint1: NSPoint(x: 558, y: 703), controlPoint2: NSPoint(x: 550, y: 600)); knife.line(to: NSPoint(x: 614, y: 531)); knife.close(); knife.fill()
NSGraphicsContext.restoreGraphicsState()
let bitmap = NSBitmapImageRep(cgImage: context.makeImage()!)
try bitmap.representation(using: .png, properties: [:])!.write(to: URL(fileURLWithPath: output))

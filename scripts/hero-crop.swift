#!/usr/bin/env swift
// hero-crop.swift — 用 macOS Vision 显著度检测识别截图里的「重要元素」，裁剪出焦点封面。
// 用法: swift hero-crop.swift in.png out.png [aspect_w aspect_h]
// 默认输出 16:10 封面；识别不到显著区域时回退到完整图（或顶部 16:10 区域）。
import Foundation
import Vision
import AppKit

let args = CommandLine.arguments
guard args.count >= 3 else {
    FileHandle.standardError.write("usage: hero-crop.swift in.png out.png [aspect_w aspect_h]\n".data(using: .utf8)!)
    exit(1)
}
let inPath = args[1]
let outPath = args[2]
let aspectW: Double = args.count >= 5 ? (Double(args[3]) ?? 16.0) : 16.0
let aspectH: Double = args.count >= 5 ? (Double(args[4]) ?? 10.0) : 10.0

guard let img = NSImage(contentsOfFile: inPath),
      let tiff = img.tiffRepresentation,
      let rep = NSBitmapImageRep(data: tiff),
      let cg = rep.cgImage else {
    FileHandle.standardError.write("ERR: cannot load \(inPath)\n".data(using: .utf8)!)
    exit(2)
}
let W = rep.pixelsWide
let H = rep.pixelsHigh
if W <= 0 || H <= 0 {
    FileHandle.standardError.write("ERR: zero size \(inPath)\n".data(using: .utf8)!)
    exit(2)
}

// 1) 显著度检测（注意力显著度）
var saliencyBox: CGRect? = nil
let handler = VNImageRequestHandler(cgImage: cg, options: [:])
let req = VNGenerateAttentionBasedSaliencyImageRequest()
do {
    try handler.perform([req])
    if let obs = req.results?.first {
        let objs = obs.salientObjects ?? []
        if !objs.isEmpty {
            var minX = 1.0, minY = 1.0, maxX = 0.0, maxY = 0.0
            for o in objs {
                let b = o.boundingBox // 归一化, 原点左下
                minX = min(minX, Double(b.origin.x))
                minY = min(minY, Double(b.origin.y))
                maxX = max(maxX, Double(b.origin.x + b.size.width))
                maxY = max(maxY, Double(b.origin.y + b.size.height))
            }
            saliencyBox = CGRect(x: minX, y: minY, width: maxX - minX, height: maxY - minY)
        }
    }
} catch {
    // 检测失败 → 回退完整图
}

let A = aspectW / aspectH // 目标宽高比

func fullCrop() -> CGRect {
    // 回退：取顶部 16:10（或完整图如果更窄）
    var w = Double(W)
    var h = w / A
    if h > Double(H) { h = Double(H); w = h * A }
    return CGRect(x: (Double(W) - w) / 2, y: 0, width: w, height: h)
}

guard var box = saliencyBox else {
    try save(crop: fullCrop())
    print("fallback full  \(inPath)")
    exit(0)
}

// 2) 归一化 → 像素（左上原点）
var bw = box.width * Double(W)
var bh = box.height * Double(H)
var bcx = (box.midX) * Double(W)
var bcy = (1.0 - box.midY) * Double(H) // 翻转 y

// 3) 加 12% 边距
bw *= 1.12; bh *= 1.12

let area = box.width * box.height
// 若显著区域过小（<6% 面积）或异常，回退完整
if area < 0.06 || bw < 40 || bh < 40 {
    try save(crop: fullCrop())
    print("tiny-saliency fallback  \(inPath)")
    exit(0)
}

// 4) 目标裁剪框：宽 = clamp(saliency 宽*1.25, 70%W, 100%W)，高按比例，再按需收缩
var cw = min(max(bw * 1.25, 0.70 * Double(W)), Double(W))
var ch = cw / A
if ch > Double(H) { ch = Double(H); cw = ch * A }
if ch < bh { ch = min(bh, Double(H)); cw = ch * A } // 保证显著区域高度装得下

var cx = bcx - cw / 2
var cy = bcy - ch / 2
cx = max(0, min(cx, Double(W) - cw))
cy = max(0, min(cy, Double(H) - ch))

let crop = CGRect(x: cx, y: cy, width: cw, height: ch)
try save(crop: crop)
print("ok  \(inPath) -> \(Int(cw))x\(Int(ch)) saliency=\(String(format: "%.2f", box.width))x\(String(format: "%.2f", box.height))")
exit(0)

func save(crop r: CGRect) throws {
    let ir = CGRect(x: Int(r.origin.x), y: Int(r.origin.y), width: Int(r.width), height: Int(r.height))
    guard let cropped = cg.cropping(to: ir) else {
        throw NSError(domain: "crop", code: 1, userInfo: nil)
    }
    let outRep = NSBitmapImageRep(cgImage: cropped)
    guard let data = outRep.representation(using: .png, properties: [:]) else {
        throw NSError(domain: "png", code: 2, userInfo: nil)
    }
    try data.write(to: URL(fileURLWithPath: outPath))
}

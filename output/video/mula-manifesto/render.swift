import AppKit
import AVFoundation
import CoreText
import ImageIO

let root = CommandLine.arguments[1]
let width = 1920
let height = 1080
let fps: Int32 = 120
let ivory = NSColor(srgbRed: 0.976, green: 0.969, blue: 0.949, alpha: 1)
let ink = NSColor(srgbRed: 23/255, green: 27/255, blue: 30/255, alpha: 1)
let clay = NSColor(srgbRed: 207/255, green: 148/255, blue: 122/255, alpha: 1)
let muted = NSColor(srgbRed: 0.48, green: 0.49, blue: 0.48, alpha: 1)
let light = NSColor(srgbRed: 0.87, green: 0.86, blue: 0.83, alpha: 1)
func clamp(_ x: Double) -> Double { return min(1, max(0, x)) }
func ease(_ x: Double) -> Double { let v = clamp(x); return 1-pow(1-v, 3) }
func loadImage(_ path: String) -> CGImage {
    guard let src = CGImageSourceCreateWithURL(URL(fileURLWithPath: path) as CFURL, nil),
          let image = CGImageSourceCreateImageAtIndex(src, 0, nil) else { fatalError("Missing image: \(path)") }
    return image
}
let portrait = loadImage(root + "/assets/nadiem-2018.jpg")
let riders = loadImage(root + "/assets/riders-2022.jpg")
let logo = loadImage("/Users/rafa/Desktop/LARAS/output/branding/mula-logo-bold-sun-11-transparent.png")
var lines: [String: CTLine] = [:]
func text(_ c: CGContext, _ s: String, _ x: Double, _ y: Double, _ size: Double, _ color: NSColor = ink, _ bold: Bool = true, _ centered: Bool = false) {
    let key = "\(s)|\(size)|\(color.description)|\(bold)"
    let line: CTLine
    if let cached = lines[key] { line = cached }
    else {
        var name = "HelveticaNeue"
        if bold { name = "HelveticaNeue-Bold" }
        let font = CTFontCreateWithName(name as CFString, size, nil)
        let a = NSAttributedString(string: s, attributes: [.font: font, .foregroundColor: color])
        line = CTLineCreateWithAttributedString(a)
        lines[key] = line
    }
    var ascent: CGFloat = 0
    let w = CTLineGetTypographicBounds(line, &ascent, nil, nil)
    var xx = x
    if centered { xx -= w/2 }
    c.saveGState(); c.translateBy(x: xx, y: y + ascent); c.scaleBy(x: 1, y: -1)
    c.textPosition = .zero; CTLineDraw(line, c); c.restoreGState()
}
func rect(_ c: CGContext, _ x: Double, _ y: Double, _ w: Double, _ h: Double, _ color: NSColor, _ radius: Double = 0) {
    c.setFillColor(color.cgColor)
    let r = CGRect(x:x,y:y,width:w,height:h)
    if radius > 0 { c.addPath(CGPath(roundedRect:r,cornerWidth:radius,cornerHeight:radius,transform:nil)); c.fillPath() }
    else { c.fill(r) }
}
func dot(_ c: CGContext, _ x: Double, _ y: Double, _ r: Double, _ color: NSColor) {
    c.setFillColor(color.cgColor); c.fillEllipse(in:CGRect(x:x-r,y:y-r,width:r*2,height:r*2))
}
func line(_ c: CGContext, _ x1: Double, _ y1: Double, _ x2: Double, _ y2: Double, _ color: NSColor, _ stroke: Double = 3) {
    c.setStrokeColor(color.cgColor); c.setLineWidth(stroke); c.setLineCap(.round)
    c.move(to:CGPoint(x:x1,y:y1)); c.addLine(to:CGPoint(x:x2,y:y2)); c.strokePath()
}
func image(_ c: CGContext, _ im: CGImage, _ x: Double, _ y: Double, _ w: Double, _ h: Double, _ zoom: Double = 1) {
    c.saveGState(); c.clip(to:CGRect(x:x,y:y,width:w,height:h))
    let scale = max(w/Double(im.width),h/Double(im.height))*zoom
    let iw = Double(im.width)*scale, ih = Double(im.height)*scale
    c.translateBy(x:x+(w-iw)/2,y:y+(h+ih)/2); c.scaleBy(x:1,y:-1)
    c.draw(im,in:CGRect(x:0,y:0,width:iw,height:ih)); c.restoreGState()
}
func title(_ c: CGContext,_ s: String,_ t: Double,_ size: Double = 96,_ color: NSColor = ink,_ yy: Double = 450) {
    c.saveGState(); c.setAlpha(ease(t/0.45))
    text(c,s,960,yy+45*(1-ease(t/0.6)),size,color,true,true); c.restoreGState()
}
func label(_ c: CGContext,_ s: String,_ color: NSColor = muted) { text(c,s,112,82,20,color,false) }
func card(_ c: CGContext,_ x:Double,_ y:Double,_ w:Double,_ h:Double,_ fill:NSColor = .white) {
    c.saveGState(); c.setShadow(offset:CGSize(width:0,height:8),blur:30,color:NSColor.black.withAlphaComponent(0.07).cgColor)
    rect(c,x,y,w,h,fill,18); c.restoreGState()
}
func browser(_ c: CGContext,_ x:Double,_ y:Double,_ w:Double,_ h:Double,_ reveal:Double) {
    card(c,x,y,w,h)
    for i in 0..<3 { dot(c,x+25+Double(i)*18,y+25,4,light) }
    line(c,x+20,y+50,x+w-20,y+50,light,1)
    let p=ease(reveal)
    rect(c,x+30,y+78,(w-60)*p,h*0.36,clay,8)
    rect(c,x+50,y+110,(w-110)*p,12,ivory,4)
    rect(c,x+50,y+137,(w-170)*p,8,ivory,4)
    for i in 0..<3 {
        let cw=(w-80)/3
        rect(c,x+30+Double(i)*(cw+10),y+h*0.58,cw,max(1,h*0.27*p),light,6)
    }
}
func phone(_ c: CGContext,_ x:Double,_ y:Double,_ scale:Double,_ t:Double) {
    c.saveGState();c.translateBy(x:x,y:y);c.scaleBy(x:scale,y:scale)
    rect(c,0,0,320,570,ink,38);rect(c,10,10,300,550,ivory,29)
    rect(c,115,23,90,14,ink,7)
    text(c,"Ke mana hari ini?",30,73,24)
    for i in 0..<7 { line(c,25,150+Double(i)*40,295,150+Double(i)*40,light,2) }
    for i in 0..<5 { line(c,40+Double(i)*57,140,40+Double(i)*57,440,light,2) }
    let q=ease(t/1.5)
    line(c,65,360,65,230,clay,8);line(c,65,230,65+180*q,230,clay,8)
    dot(c,65,360,12,ink);dot(c,65+180*q,230,12,clay)
    rect(c,28,463,264,66,ink,12);text(c,"Terhubung",160,482,22,ivory,true,true)
    c.restoreGState()
}
func render(_ c: CGContext,_ t:Double) {
    c.saveGState();c.translateBy(x:0,y:Double(height));c.scaleBy(x:1,y:-1)
    var bg = ivory
    if t >= 35 && t < 44 { bg = ink }
    if t >= 63 { bg = ink }
    rect(c,0,0,1920,1080,bg)
    if t < 4 {
        if t < 2 { title(c,"Mulai aja.",t,142) }
        else { title(c,"Dua kata. Kok susah, ya?",t-2,66) }
    } else if t < 9 {
        let u=t-4
        label(c,"SEBUAH PERMULAAN / 2010")
        let p=ease(u/0.7)
        image(c,portrait,112-60*(1-p),175,490,660,1+u*0.008)
        text(c,"Nadiem Makarim",112,858,24)
        text(c,"Foto: WEF / Sikarin Thanachaiary · 2018 · CC BY-SA 2.0",112,904,16,muted,false)
        text(c,"2010.",720,175,145)
        text(c,"Nadiem memulai Gojek.",728,354,47)
        if u>1.4 {
            let n=min(20,Int((u-1.4)*22))
            for i in 0..<n { dot(c,752+Double(i%10)*69,493+Double(i/10)*64,13,clay) }
            text(c,"20 pengemudi.",728,604,57)
        }
        if u>3.2 { text(c,"Satu call center.",728,689+25*(1-ease((u-3.2)/0.4)),57) }
    } else if t < 13 {
        let u=t-9
        label(c,"SEBELUM OTOMATISASI")
        let names=["PELANGGAN","OPERATOR","PENGEMUDI"]
        for i in 0..<3 {
            let x=410+Double(i)*550
            dot(c,x,510,79,ink)
            text(c,String(i+1),x,467,64,ivory,true,true)
            text(c,names[i],x,630,24,ink,false,true)
            if i<2 {
                let p=clamp((u-Double(i)*0.65)/0.8)
                line(c,x+100,510,x+100+350*p,510,clay,5)
                dot(c,x+100+350*p,510,9,clay)
            }
        }
        let words=["Telepon masuk.","Cari pengemudi.","Satu per satu."]
        let index=min(2,Int(u/1.25))
        title(c,words[index],u-Double(index)*1.25,66,ink,230)
    } else if t < 16 {
        let u=t-13
        label(c,"WAKTU BERJALAN")
        let year=2010+min(4,Int(u*1.8))
        text(c,String(year),960,285,250,ink,true,true)
        for i in 0..<5 {
            let x=660+Double(i)*150
            dot(c,x,670,7,light)
            if i <= year-2010 { dot(c,x,670,7,clay) }
        }
        text(c,"Bertahun-tahun membangun.",960,784,44,ink,false,true)
    } else if t < 22 {
        let u=t-16
        if u<1.5 {
            title(c,"Lalu, 2015.",u,170)
            rect(c,400,710,1120*ease(u/0.8),9,clay)
        } else {
            label(c,"TITIK BALIK / 2015")
            text(c,"Aplikasi",120,280,108)
            text(c,"hadir.",120,401,108)
            if u>3 {text(c,"Proses mulai diotomatisasi.",125,622,42,ink,false)}
            phone(c,1190+200*(1-ease((u-1.5)/0.8)),205,1.15,u-1.5)
            for i in 0..<14 {
                let x=870+Double(i%2)*120, y=240+Double(i/2)*87
                dot(c,x,y,6,clay)
                let p=clamp((u-2.3-Double(i)*0.035)/0.8)
                line(c,x,y,x+(1170-x)*p,y+(510-y)*p,clay.withAlphaComponent(0.3),1.5)
            }
        }
    } else if t < 29 {
        let u=t-22
        label(c,"PESANAN PER HARI / GOJEK")
        var heading="Cara kerjanya berubah."
        if u>2.6 { heading="Skalanya ikut berubah." }
        text(c,heading,120,145,78)
        let x0=260.0, x1=930.0, x2=1590.0, bottom=812.0, top=330.0
        for v in [0,100000,200000,300000] {
            let y=bottom-Double(v)/300000*(bottom-top)
            line(c,x0,y,1700,y,light,1)
            text(c,String(v/1000)+" rb",120,y-13,22,muted,false)
        }
        let y0=bottom-3000/300000.0*(bottom-top), y1=bottom-(bottom-top)/3
        dot(c,x0,y0,9,clay)
        let a=ease((u-0.6)/1.8), b=ease((u-2.8)/2)
        line(c,x0,y0,x0+(x1-x0)*a,y0+(y1-y0)*a,clay,8)
        if u>2.8 { line(c,x1,y1,x1+(x2-x1)*b,y1+(top-y1)*b,clay,8) }
        text(c,"3.000",x0,860,29,ink,true,true)
        text(c,"→ 100.000",x1,860,29,ink,true,true)
        text(c,"Pertengahan 2015",(x0+x1)/2,912,23,muted,false,true)
        if u>2.8 { dot(c,x2,top,10*b,ink);text(c,"300.000+",x2,260,62,ink,true,true);text(c,"Awal 2016",x2,912,23,muted,false,true) }
        text(c,"Sumber: gojek.github.io/about/ · Perbandingan tonggak; interval waktu tidak berskala.",120,1008,19,muted,false)
    } else if t < 35 {
        let u=t-29
        label(c,"ERA APLIKASI")
        let shift=18*sin(u*0.6)
        image(c,riders,120,190+shift,430,620,1+u*0.007)
        phone(c,1420,195-shift,0.95,u)
        let words=["Satu perubahan.","Begitu banyak","kemungkinan."]
        if u<2.2 { title(c,words[0],u,63,ink,440) }
        else {
            title(c,words[1],u-2.2,57,ink,411)
            title(c,words[2],u-2.35,72,ink,483)
        }
        text(c,"Foto: Hanif Al Husaini · Salatiga, 2022 · CC BY 4.0",120,886,17,muted,false)
    } else if t < 40 {
        let u=t-35
        if u<2.4 { title(c,"Sekarang…",u,76,ivory) }
        else { title(c,"Terjadi lagi.",u-2.4,115,ivory) }
        line(c,760,730,760+400*ease(u/4),730,clay,3)
    } else if t < 44 {
        let u=t-40
        for i in 0..<24 {
            let a=Double(i)*Double.pi/12+u*0.08
            let radius=300+u*30
            let x=960+cos(a)*radius*1.75, y=540+sin(a)*radius
            dot(c,x,y,4+Double(i%3)*2,clay.withAlphaComponent(0.5))
            if i%3==0 { line(c,x,y,960+cos(a)*180,540+sin(a)*120,clay.withAlphaComponent(0.16),1) }
        }
        title(c,"Era AI.",u,200,ivory,395)
    } else if t < 52 {
        let u=t-44
        label(c,"KEMUNGKINAN BARU")
        if u<2.8 {
            title(c,"Lebih cepat membangun.",u,67,ink,160)
            let p=ease(u/1.0)
            browser(c,530,345+130*(1-p),860,510,p)
            for i in 0..<3 {
                let x=180+Double(i)*40
                rect(c,x,365+Double(i)*130,210,83,clay.withAlphaComponent(0.2+Double(i)*0.1),10)
                line(c,x+225,405+Double(i)*130,500,490,clay,2)
            }
        } else if u<5.6 {
            let v=u-2.8
            title(c,"Lebih banyak yang bisa dijalankan.",v,62,ink,160)
            let labels=["PELANGGAN","INVENTARIS","LAPORAN"]
            let details=["Pertanyaan terjawab","Stok diperbarui","Ringkasan siap"]
            for i in 0..<3 {
                let x=150+Double(i)*560, p=ease((v-Double(i)*0.12)/0.65)
                card(c,x,365+90*(1-p),500,400)
                text(c,labels[i],x+35,410+90*(1-p),23,muted)
                for j in 0..<3 { rect(c,x+35,480+Double(j)*48,330*p-Double(j)*40,12,light,6) }
                dot(c,x+52,680,13,clay)
                text(c,details[i],x+80,661,24)
            }
            text(c,"Agen AI membantu. Pemilik menentukan arah.",960,895,27,muted,false,true)
        } else {
            let v=u-5.6
            title(c,"Lebih sedikit hambatan",v,76,ink,320)
            title(c,"untuk mulai.",v-0.15,100,ink,418)
            for i in 0..<9 {
                let x=480+Double(i)*120
                let p=ease((v-Double(i)*0.055)/0.9)
                rect(c,x,720,80,12+100*(1-p),clay,6)
            }
        }
    } else if t < 57 {
        let u=t-52
        for i in 0..<28 {
            let a=Double(i)*2.39996, r=(430+Double(i%4)*75)*(1-ease(u/2.8))
            dot(c,960+cos(a)*r*1.8,600+sin(a)*r,5,clay.withAlphaComponent(1-clamp(u/3)))
        }
        title(c,"Dan ini baru",u,80,ink,355)
        title(c,"permulaan.",u-0.2,108,ink,451)
    } else if t < 61 {
        title(c,"Terus, nunggu apa?",t-57,88)
    } else if t < 63 {
        title(c,"Mulai aja.",t-61,142)
    } else {
        let u=t-63,p=ease(u/0.8)
        c.saveGState();c.setAlpha(p)
        let w=1250.0,h=w*Double(logo.height)/Double(logo.width)
        image(c,logo,(1920-w)/2,540-h/2+65*(1-p),w,h)
        c.restoreGState()
    }
    c.restoreGState()
}

let cs=CGColorSpaceCreateDeviceRGB()
if CommandLine.arguments.contains("--stills") {
    let moments:[Double]=[1,3,6,8.5,11,14.5,17,20,24,27.5,31.5,36.5,41.5,45.5,48.2,50.8,54,59,62,64.5]
    for (i,t) in moments.enumerated() {
        let c=CGContext(data:nil,width:width,height:height,bitsPerComponent:8,bytesPerRow:width*4,space:cs,bitmapInfo:CGImageAlphaInfo.premultipliedLast.rawValue)!
        render(c,t)
        let im=c.makeImage()!
        let dest=CGImageDestinationCreateWithURL(URL(fileURLWithPath:root+"/assets/still-\(i).jpg") as CFURL,"public.jpeg" as CFString,1,nil)!
        CGImageDestinationAddImage(dest,im,nil);CGImageDestinationFinalize(dest)
    }
    print("Rendered review frames")
} else {
    let url=URL(fileURLWithPath:root+"/picture-120fps.mp4")
    let writer=try AVAssetWriter(outputURL:url,fileType:.mp4)
    let input=AVAssetWriterInput(mediaType:.video,outputSettings:[AVVideoCodecKey:AVVideoCodecType.h264,AVVideoWidthKey:width,AVVideoHeightKey:height,AVVideoCompressionPropertiesKey:[AVVideoAverageBitRateKey:18000000,AVVideoExpectedSourceFrameRateKey:fps,AVVideoMaxKeyFrameIntervalKey:240,AVVideoAllowFrameReorderingKey:false,AVVideoProfileLevelKey:AVVideoProfileLevelH264HighAutoLevel]])
    input.expectsMediaDataInRealTime=false
    let adaptor=AVAssetWriterInputPixelBufferAdaptor(assetWriterInput:input,sourcePixelBufferAttributes:[kCVPixelBufferPixelFormatTypeKey as String:kCVPixelFormatType_32ARGB,kCVPixelBufferWidthKey as String:width,kCVPixelBufferHeightKey as String:height,kCVPixelBufferCGImageCompatibilityKey as String:true,kCVPixelBufferCGBitmapContextCompatibilityKey as String:true])
    writer.add(input)
    guard writer.startWriting() else { fatalError("Writer failed: \(String(describing:writer.error))") }
    writer.startSession(atSourceTime:.zero)
    for frame in 0..<(65*Int(fps)) {
        autoreleasepool {
            while !input.isReadyForMoreMediaData {
                if writer.status == .failed {fatalError("Encode failed: \(String(describing:writer.error))")}
                Thread.sleep(forTimeInterval:0.002)
            }
            var pb:CVPixelBuffer?
            guard CVPixelBufferPoolCreatePixelBuffer(nil,adaptor.pixelBufferPool!,&pb)==kCVReturnSuccess,let buffer=pb else {fatalError("Pixel allocation failed")}
            CVPixelBufferLockBaseAddress(buffer,[])
            let c=CGContext(data:CVPixelBufferGetBaseAddress(buffer),width:width,height:height,bitsPerComponent:8,bytesPerRow:CVPixelBufferGetBytesPerRow(buffer),space:cs,bitmapInfo:CGImageAlphaInfo.noneSkipFirst.rawValue)!
            render(c,Double(frame)/Double(fps))
            CVPixelBufferUnlockBaseAddress(buffer,[])
            guard adaptor.append(buffer,withPresentationTime:CMTime(value:Int64(frame),timescale:fps)) else {fatalError("Append failed: \(String(describing:writer.error))")}
        }
        if frame % 600 == 0 {print("Rendered \(frame/Int(fps))/65 seconds");fflush(stdout)}
    }
    input.markAsFinished()
    let sem=DispatchSemaphore(value:0)
    writer.finishWriting{sem.signal()};sem.wait()
    guard writer.status == .completed else {fatalError("Finish failed: \(String(describing:writer.error))")}
    print("Picture complete: \(url.path)")
}

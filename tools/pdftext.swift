// Usage: swift tools/pdftext.swift <pdf> <firstPage> <lastPage>   (1-based, inclusive)
import PDFKit
let a = CommandLine.arguments
let d = PDFDocument(url: URL(fileURLWithPath: a[1]))!
let s = Int(a[2])!, e = min(Int(a[3])!, d.pageCount)
for i in (s - 1)..<e { print("=== page \(i + 1)"); print(d.page(at: i)?.string ?? "") }

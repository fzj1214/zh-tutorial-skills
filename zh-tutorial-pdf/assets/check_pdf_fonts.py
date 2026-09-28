"""检查 PDF 里每一个字体是否都已嵌入。有任何一个没嵌入，返回码为 1。

为什么要查：
    没嵌入的字体，由【读者的机器】负责提供。作者自己的机器装了这个字体，
    渲染出来一切正常；读者没有，那些字就变成空白或方框 —— 而编译过程不报任何错。
    实测案例：ctex 的 fontset=macnew 给等宽中文用 STFangsong，它的授权标志
    禁止嵌入，结果所有代码块、程序输出里的中文在读者那边整片消失。
    "我自己看是好的"证明不了任何事，只有查嵌入状态才算数。

用法:  python check_pdf_fonts.py main.pdf
依赖:  pypdf
"""
import sys

from pypdf import PdfReader


def fonts_of(reader):
    found = {}

    def walk(res, page_no, depth=0):
        if res is None or depth > 8:
            return
        res = res.get_object()
        fonts = res.get("/Font")
        if fonts:
            for _, ref in fonts.get_object().items():
                f = ref.get_object()
                base = str(f.get("/BaseFont", "?"))
                sub = str(f.get("/Subtype"))
                if sub == "/Type3":
                    embedded = True          # Type 3 的字形本身就写在 PDF 里
                else:
                    d = f["/DescendantFonts"][0].get_object() if sub == "/Type0" else f
                    desc = d.get("/FontDescriptor")
                    desc = desc.get_object() if desc is not None else {}
                    embedded = any(k in desc for k in ("/FontFile", "/FontFile2", "/FontFile3"))
                e = found.setdefault(base, {"subtype": sub, "embedded": embedded, "pages": set()})
                e["pages"].add(page_no)
        xobjs = res.get("/XObject")
        if xobjs:
            for _, ref in xobjs.get_object().items():
                x = ref.get_object()
                if x.get("/Subtype") == "/Form":          # 插图 PDF 以 Form XObject 嵌入
                    walk(x.get("/Resources"), page_no, depth + 1)

    for i, page in enumerate(reader.pages, 1):
        walk(page.get("/Resources"), i)
    return found


def main(path):
    found = fonts_of(PdfReader(path))
    bad = {k: v for k, v in found.items() if not v["embedded"]}
    print(f"  {path}：共 {len(found)} 个字体，未嵌入 {len(bad)} 个")
    for base, e in sorted(bad.items()):
        pages = sorted(e["pages"])
        shown = ",".join(map(str, pages[:12])) + ("…" if len(pages) > 12 else "")
        print(f"    未嵌入  {base}  ({e['subtype']})  出现在第 {shown} 页")
    if bad:
        print("  这些字在没有安装对应字体的阅读器里会显示成空白。"
              "查字体的 OS/2 fsType：0x0002 表示授权禁止嵌入，要换字体。")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "main.pdf"))

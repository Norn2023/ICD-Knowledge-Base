import fitz, os
BASE = os.path.dirname(os.path.abspath(__file__))
pdf_path = os.path.join('D:\\Norn_Obsi\\00_Inbox\\按病组（DRG）付费分组方案（2.0 版）.pdf')
doc = fitz.open(pdf_path)

# Search for physical therapy / rehabilitation related pages
for i in range(doc.page_count):
    text = doc[i].get_text()
    # Try different encodings
    if '物理' in text or '康复' in text or '理疗' in text or '运动治疗' in text:
        # Print page number and relevant text snippets
        lines = text.split('\n')
        relevant = [l.strip() for l in lines if '物理' in l or '康复' in l or '理疗' in l or '运动治疗' in l]
        if relevant:
            print(f'=== Page {i+1} (text search) ===')
            for l in relevant[:10]:
                print(l[:200])

doc.close()

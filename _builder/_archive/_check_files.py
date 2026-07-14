import os

files = ['按病组（DRG）付费分组方案（2.0版）.pdf',
         '按病种分值（DIP）付费病种库（2.0版）202407.pdf']

for f in files:
    with open(f, 'rb') as fh:
        sig = fh.read(10)
    is_pdf = sig[:4] == b'%PDF'
    print(f'{f}: {sig[:5]}... -> {"PDF" if is_pdf else "NOT PDF"}')
    print(f'  Size: {os.path.getsize(f):,} bytes')
    print()

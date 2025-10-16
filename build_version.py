# build_version.py
import os

version_path = "version.txt"
output_path = "version_file.txt"

# version.txt에서 문자열 읽기
with open(version_path, "r", encoding="utf-8") as f:
    ver = f.read().strip()

# 버전이 3자리면 .0 추가
parts = ver.split(".")
while len(parts) < 4:
    parts.append("0")
ver_tuple = tuple(map(int, parts[:4]))

# 버전 리소스 내용 자동 생성
content = f"""
# -*- coding: utf-8 -*-
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={ver_tuple},
    prodvers={ver_tuple},
    mask=0x3f,
    flags=0x0,
    OS=0x4,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        '040904B0',
        [
          StringStruct('CompanyName',      'Kwangho Lee'),
          StringStruct('FileDescription',  'Aptitude Tools – Aptitude Practice Toolkit'),
          StringStruct('FileVersion',      '{ver}'),
          StringStruct('InternalName',     'AptitudeTools'),
          StringStruct('LegalCopyright',   '© 2025 Kwangho Lee. All rights reserved.'),
          StringStruct('OriginalFilename', 'AptitudeTools.exe'),
          StringStruct('ProductName',      'Aptitude Tools'),
          StringStruct('ProductVersion',   '{ver}')
        ]
      )
    ]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
""".strip()

with open(output_path, "w", encoding="utf-8") as f:
    f.write(content)

print(f"[+] Generated {output_path} from version {ver}")

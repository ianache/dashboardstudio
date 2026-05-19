import os

src_dir = r"c:\Users\ianache\Desktop\DATA\01-DOCUMENTOS\02-PROYECTOS\102-concesionarias\dashboardstudio\dashboard-app\src"
for root, dirs, files in os.walk(src_dir):
    for file in files:
        if file.endswith(".vue"):
            path = os.path.join(root, file)
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            if "Exportar" in content:
                print(f"Found in: {file}")
                # print lines containing Exportar
                for idx, line in enumerate(content.splitlines()):
                    if "Exportar" in line:
                        print(f"  Line {idx+1}: {line.strip()}")

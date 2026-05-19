with open(r"c:\Users\ianache\Desktop\DATA\01-DOCUMENTOS\02-PROYECTOS\102-concesionarias\dashboardstudio\dashboard-app\src\components\editor\FlowEditorCanvas.vue", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "defineexpose" in line.lower():
        safe_line = line.strip().encode('ascii', errors='replace').decode('ascii')
        print(f"{i+1}: {safe_line}")
        # print subsequent 15 lines
        for j in range(1, 20):
            if i + j < len(lines):
                print(f"{i+j+1}: {lines[i+j].strip()}")

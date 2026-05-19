with open(r"c:\Users\ianache\Desktop\DATA\01-DOCUMENTOS\02-PROYECTOS\102-concesionarias\dashboardstudio\dashboard-app\src\views\FlowEditorView.vue", "r", encoding="utf-8") as f:
    lines = f.readlines()

found = False
count = 0
for i, line in enumerate(lines):
    if "<script" in line:
        found = True
    if found:
        safe_line = line.strip().encode('ascii', errors='replace').decode('ascii')
        print(f"{i+1}: {safe_line}")
        count += 1
        if count > 150:
            break

with open(r"c:\Users\ianache\Desktop\DATA\01-DOCUMENTOS\02-PROYECTOS\102-concesionarias\dashboardstudio\dashboard-app\src\views\FlowEditorView.vue", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx in range(0, min(80, len(lines))):
    safe_line = lines[idx].strip().encode('ascii', errors='replace').decode('ascii')
    print(f"{idx+1}: {safe_line}")

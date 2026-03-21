# ----------------------------
# Propagar screening_view -> full (sem fórmulas)
# ----------------------------
if "wos_full" in wb.sheetnames:
    ws_full = wb["wos_full"]
    ws_view = wb["wos_screening_view"]

    headers_full = [c.value for c in ws_full[1]]
    headers_view = [c.value for c in ws_view[1]]

    cf = {h: i + 1 for i, h in enumerate(headers_full)}
    cv = {h: i + 1 for i, h in enumerate(headers_view)}

    required_view = ["source_record_id", "Label", "Reason to Exclude", "Comment"]
    required_full = ["source_record_id", "Label", "Reason to Exclude", "Comment"]

    for h in required_view:
        if h not in cv:
            raise ValueError(f"Falta coluna '{h}' em wos_screening_view.")
    for h in required_full:
        if h not in cf:
            raise ValueError(f"Falta coluna '{h}' em wos_full.")

    # mapa: source_record_id -> (Label, Reason, Comment)
    m = {}
    for r in range(2, ws_view.max_row + 1):
        k = ws_view.cell(r, cv["source_record_id"]).value
        if k is None or str(k).strip() == "":
            continue
        m[k] = (
            ws_view.cell(r, cv["Label"]).value,
            ws_view.cell(r, cv["Reason to Exclude"]).value,
            ws_view.cell(r, cv["Comment"]).value,
        )

    # escrever no full
    updated_full = 0
    for r in range(2, ws_full.max_row + 1):
        k = ws_full.cell(r, cf["source_record_id"]).value
        if k in m:
            lab, rea, com = m[k]
            ws_full.cell(r, cf["Label"]).value = lab
            ws_full.cell(r, cf["Reason to Exclude"]).value = rea
            ws_full.cell(r, cf["Comment"]).value = com
            updated_full += 1

    print(f"wos_full atualizado (sem fórmulas): {updated_full}")
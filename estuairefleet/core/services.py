import csv
import io
import zipfile
from xml.sax.saxutils import escape


def _rows(statistics):
    labels = {
        "students": "Étudiants actifs",
        "drivers": "Chauffeurs actifs",
        "buses_in_service": "Bus en service",
        "active_signals": "Signaux actifs",
        "open_alerts": "Alertes ouvertes",
        "open_incidents": "Incidents ouverts",
        "average_wait_minutes": "Temps d'attente moyen (minutes)",
        "taken_rate": "Taux de prise en charge (%)",
    }
    return [(label, statistics[key]) for key, label in labels.items()]


def export_csv(statistics):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(("Indicateur", "Valeur"))
    writer.writerows(_rows(statistics))
    return output.getvalue().encode("utf-8-sig")


def export_xlsx(statistics):
    rows = _rows(statistics)
    sheet_rows = [
        '<row r="1"><c r="A1" t="inlineStr"><is><t>Indicateur</t></is></c><c r="B1" t="inlineStr"><is><t>Valeur</t></is></c></row>'
    ]
    for index, (label, value) in enumerate(rows, start=2):
        sheet_rows.append(
            f'<row r="{index}"><c r="A{index}" t="inlineStr"><is><t>{escape(label)}</t></is></c>'
            f'<c r="B{index}"><v>{value}</v></c></row>'
        )
    files = {
        "[Content_Types].xml": '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>',
        "_rels/.rels": '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>',
        "xl/workbook.xml": '<?xml version="1.0"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Statistiques" sheetId="1" r:id="rId1"/></sheets></workbook>',
        "xl/_rels/workbook.xml.rels": '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>',
        "xl/worksheets/sheet1.xml": f'<?xml version="1.0"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>{"".join(sheet_rows)}</sheetData></worksheet>',
    }
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    return output.getvalue()


def export_pdf(statistics):
    lines = [
        "EstuaireFleet — statistiques opérationnelles",
        *[f"{label}: {value}" for label, value in _rows(statistics)],
    ]
    commands = ["BT /F1 12 Tf 50 760 Td"]
    for index, line in enumerate(lines):
        if index:
            commands.append("0 -24 Td")
        commands.append(f"({line.replace('(', '[').replace(')', ']')}) Tj")
    commands.append("ET")
    stream = " ".join(commands).encode("latin-1", "replace")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{index} 0 obj\n".encode() + obj + b"\nendobj\n")
    startxref = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode())
    pdf.extend("".join(f"{offset:010d} 00000 n \n" for offset in offsets[1:]).encode())
    pdf.extend(f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{startxref}\n%%EOF".encode())
    return bytes(pdf)

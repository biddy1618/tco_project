from pathlib import Path
import zipfile
import xml.etree.ElementTree as ET


def main() -> None:
    out = Path('artifacts/testcases_sample.txt')
    workbook = next(Path('data/raw').glob('*.xlsx'))
    ns = {
        'a': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
        'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    }

    with zipfile.ZipFile(workbook) as archive, out.open('w', encoding='utf-8') as handle:
        workbook_xml = ET.fromstring(archive.read('xl/workbook.xml'))
        rels = ET.fromstring(archive.read('xl/_rels/workbook.xml.rels'))
        relmap = {rel.attrib['Id']: rel.attrib['Target'] for rel in rels}

        shared_strings = []
        if 'xl/sharedStrings.xml' in archive.namelist():
            root = ET.fromstring(archive.read('xl/sharedStrings.xml'))
            for item in root.findall('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}si'):
                shared_strings.append(''.join(text.text or '' for text in item.iter('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t')))

        sheet_name = '2. Test Cases'
        sheet_node = next(sheet for sheet in workbook_xml.find('a:sheets', ns) if sheet.attrib['name'] == sheet_name)
        target = 'xl/' + relmap[sheet_node.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']].lstrip('/')
        sheet = ET.fromstring(archive.read(target))

        for row in sheet.findall('.//a:sheetData/a:row', ns)[:25]:
            values = []
            for cell in row.findall('a:c', ns):
                cell_type = cell.attrib.get('t')
                value_node = cell.find('a:v', ns)
                value = '' if value_node is None else (value_node.text or '')
                if cell_type == 's' and value.isdigit():
                    value = shared_strings[int(value)]
                values.append(value)
            if any(values):
                handle.write(f"{row.attrib.get('r')}: {values}\n")


if __name__ == '__main__':
    main()
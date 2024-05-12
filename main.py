from pyscript import document  # type: ignore
from pyodide.ffi import create_proxy  # type: ignore
from js import FileReader  # type: ignore
from io import BytesIO
import pypdf
import os


total_count: int = 0
read_count: int = 0
search_data: list[str | object] = []


def drop_handler(event):
    global total_count
    event.preventDefault()
    event.stopPropagation()
    items = event.dataTransfer.items
    for item in items:
        entry = item.webkitGetAsEntry()
        if entry.isDirectory == True:
            get_directory_entries(entry)
        else:
            if is_pdf(entry.name) == False:
                continue
            total_count += 1
            read_file(entry)


def is_pdf(filename):
    _, ext = os.path.splitext(filename)
    return ext.lower() == ".pdf"


def get_directory_entries(entry):
    entry.createReader().readEntries(create_proxy(get_entries))


def get_entries(entries):
    global total_count
    for entry in entries:
        if entry.isDirectory == True:
            get_directory_entries(entry)
        else:
            if is_pdf(entry.name) == False:
                continue
            total_count += 1
            read_file(entry)


def isEntry(object):
    try:
        object.isFile
        return True
    except:
        return False


def read_file(entry):
    entry.file(create_proxy(read_text))


def read_text(file):
    reader = FileReader.new()

    def onload(e):
        global read_count, total_count, search_data
        pdf_bytes = BytesIO(e.target.result.to_py())
        reader = pypdf.PdfReader(pdf_bytes)
        results: list[str] = []
        for page in reader.pages:
            text: str = page.extract_text()
            if "파이썬".lower() in text.lower():
                results.append(f"페이지 {reader.pages.index(page)+1}: {text}")
        search_data.append(results)
        read_count += 1
        if total_count == read_count:
            print(search_data)
    reader.addEventListener('load', create_proxy(onload))
    reader.readAsArrayBuffer(file)


def dragover_handler(event):
    event.preventDefault()


drop_zone = document.getElementById("drop_zone")
drop_zone.addEventListener('drop', create_proxy(drop_handler))
drop_zone.addEventListener('dragover', create_proxy(dragover_handler))

from pyscript import document  # type: ignore
from pyodide.ffi import create_proxy  # type: ignore
from js import FileReader  # type: ignore
from io import BytesIO
import pypdf


def drop_handler(event):
    event.preventDefault()
    event.stopPropagation()
    items = event.dataTransfer.items
    for item in items:
        entry = item.webkitGetAsEntry()
        if entry.isDirectory == True:
            get_directory_entries(entry)
        else:
            read_file(item)


def get_directory_entries(entry):
    entry.createReader().readEntries(create_proxy(get_entries))


def get_entries(entries):
    for entry in entries:
        if entry.isDirectory == True:
            get_directory_entries(entry)
        else:
            read_file(entry)


def get_directory(item):
    return


def read_file(item):
    file = item.getAsFile()
    reader = FileReader.new()

    def onload(e):
        pdf_bytes = BytesIO(e.target.result.to_py())
        reader = pypdf.PdfReader(pdf_bytes)
        results = []
        for page in reader.pages:
            text = page.extract_text()
            if "파이썬".lower() in text.lower():
                results.append(f"페이지 {reader.pages.index(page)+1}: {text}")

    reader.addEventListener('load', create_proxy(onload))
    reader.readAsArrayBuffer(file)


def dragover_handler(event):
    event.preventDefault()


drop_zone = document.getElementById("drop_zone")
drop_zone.addEventListener('drop', create_proxy(drop_handler))
drop_zone.addEventListener('dragover', create_proxy(dragover_handler))

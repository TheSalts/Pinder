"""

   ___    _             __
  / _ \  (_) ___    ___/ / ___   ____
 / ___/ / / / _ \  / _  / / -_) / __/
/_/    /_/ /_//_/  \_,_/  \__/ /_/


MIT License, Copyright (c) 2024 TheSalt_

한국공학대학교 소프트웨어공학과 파이썬프로그래밍

타입명 앞에 `JS.`이 있으면 자바스크립트 객체이므로 pyscript로 프록시 필요
"""


from pyscript import document  # type: ignore
from pyodide.ffi import create_proxy  # type: ignore
from js import FileReader  # type: ignore
import js  # type: ignore
from io import BytesIO
import pypdf
import os


"""
글로벌 변수
"""
search_data: list[list[dict[str, int | str]]] = []  # 검색어를 검색할 데이터
pdf_data: list[dict] = []


def drop_handler(event) -> None:
    """파일 & 폴더 드롭 수신

    Args:
        event (JS.event): 이벤트
    """
    event.preventDefault()
    event.stopPropagation()
    file_drop.classList.remove("dragover")

    items = event.dataTransfer.items

    for item in items:
        entry = item.webkitGetAsEntry()  # type: ignore
        """
            폴더인지 아닌지 검사 후 폴더면 하위 디렉토리 재검색
            """
        if entry.isDirectory == True:
            entry.createReader().readEntries(create_proxy(get_entries))
        else:
            if is_pdf(entry.name) == False:  # PDF가 아니면 패스
                continue
            entry.file(create_proxy(read_text))


def file_handler(event) -> None:
    """파일 버튼 수신

    Args:
        event (JS.event): 이벤트
    """
    event.preventDefault()
    event.stopPropagation()

    for item in event.target.files:
        read_text(item)


def is_pdf(filename: str) -> bool:
    """파일 이름을 기반으로 파일이 PDF인지 확인

    Args:
        filename (str): 파일명

    Returns:
        bool: PDF 확인 여부
    """
    _, ext = os.path.splitext(filename)
    return ext.lower() == ".pdf"


def get_entries(entries) -> None:
    """DirectoryEntry 객체를 검사해 내부 파일 분류

    Args:
        entries (JS.DirectoryEntry): 폴더 객체
    """
    for entry in entries:
        """
        폴더인지 아닌지 검사 후 폴더면 하위 디렉토리 재검색
        """
        if entry.isDirectory == True:
            entry.createReader().readEntries(create_proxy(get_entries))
        else:
            if is_pdf(entry.name) == False:  # PDF가 아니면 패스
                continue
            entry.file(create_proxy(read_text))


def isEntry(object) -> bool:
    """객체가 Entry인지 아닌지 검사

    Args:
        object (JS.DirectoryEntry | JS.FileEntry | any): 검사할 객체

    Returns:
        bool: 검사여부
    """
    try:
        object.isFile  # Entry가 아니라면 속성이 없으므로 에러 발생 -> except 실행
        return True
    except:
        return False


def read_text(file) -> None:
    """파일 읽기

    Args:
        file (JS.File): 읽을 파일
    """
    reader = FileReader.new()

    def onload(e):
        """파일 읽어서 검색으로 보내기

        Args:
            e (JS.event): 이벤트
        """
        global read_count, total_count, search_data, pdf_data
        pdf_bytes = BytesIO(e.target.result.to_py())  # ArrayBuffer를 Bytes로 변환
        reader = pypdf.PdfReader(pdf_bytes)
        results: list[dict[str, int | str]] = []  # 결과 저장 위치
        for page in reader.pages:
            text: str = page.extract_text()
            obj: dict[str, int | str] = {
                "page": reader.pages.index(page)+1, "text": text, "filename": file.name
            }
            results.append(obj)  # 결과 저장
        js.getPDFImage(e.target.result)
        search_data.append(results)  # 최종 결과에 저장
        search_data_in_pdf(e.target.result, file.name)
        pdf_data.append({"buffer": e.target.result, "filename": file.name})

    reader.addEventListener('load', create_proxy(onload))  # 파일 읽기에 성공하면 이벤트 호출
    reader.readAsArrayBuffer(file)  # JS의 ArrayBuffer로 읽기


def search_data_in_pdf(pdfArrayBuffer, filename) -> None:
    """데이터 검색

    Args:
        pdfArrayBuffer (JS.ArrayBuffer): PDF 버퍼

    data = {
        "page": ${페이지 번호} (int), "text": ${텍스트} (str), "filename": ${파일 이름} (str)
    }
    """
    global search_data
    search_keyword: str = document.getElementById("search-input").value
    if document.getElementById("search-input").value == "":
        return
    total_count: int = 0
    for i in search_data:
        total_count += len(i)
    read_count: int = 0
    found_data: list[dict[str, str | int]] = []
    for data_list in search_data:
        for data in data_list:
            read_count += 1
            searching_data: str = data["text"].lower()   # type: ignore
            found: int = searching_data.find(search_keyword)  # 검색
            if found != -1:  # 검색에 성공
                found_data.append(data)
            if total_count == read_count:
                if found_data == []:
                    return search_fail()
                found_data_file_pages = found_data
                seen = set()
                new_data = []
                for item in found_data_file_pages:
                    # 딕셔너리 아이템을 튜플의 리스트로 변환 후, 다시 튜플로 변환
                    # 딕셔너리가 순서를 보장하지 않으므로, 키를 기준으로 정렬
                    item_tuple = tuple(sorted(item.items()))
                    if item_tuple not in seen:
                        seen.add(item_tuple)
                        new_data.append(item)
                found_data_file_pages = new_data
                for page in found_data_file_pages:
                    if page["filename"] == filename:
                        js.setPDF(pdfArrayBuffer, page["page"])  # pdf 렌더링
                        file_drop.remove()  # 파일 선택 제거
                        file_input.remove()


def search_fail() -> None:
    """검색 실패 예외처리"""
    print("검색 실패  - 이미지 검색 시작")


def dragover_handler(event) -> None:
    """dragover 이벤트 수신"""
    event.preventDefault()
    file_drop.classList.add("dragover")


def dragleave_handler(event) -> None:
    """dragleave 이벤트 수신"""
    event.preventDefault()
    file_drop.classList.remove("dragover")


def search_button_handler(e) -> None:
    """검색 버튼 수신"""
    e.preventDefault()
    global pdf_data
    if pdf_data == []:
        return
    for i in pdf_data:
        search_data_in_pdf(i["buffer"], i["filename"])


"""
JS 이벤트 핸들러
"""
file_drop = document.getElementById("file-drop")
file_drop.addEventListener('drop', create_proxy(drop_handler))
file_drop.addEventListener('dragover', create_proxy(dragover_handler))
file_drop.addEventListener('dragleave', create_proxy(dragleave_handler))

file_input = document.getElementById("file-input")
file_input.addEventListener('change', create_proxy(file_handler))

search_button = document.getElementById("search-button")
search_button.addEventListener('click', create_proxy(search_button_handler))

form = document.querySelector('form')
form.addEventListener('submit', create_proxy(search_button_handler))

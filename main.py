from pyscript import document  # type: ignore
from pyodide.ffi import create_proxy  # type: ignore
from js import FileReader  # type: ignore
from io import BytesIO
import pypdf
import os

"""
프록시로 인해 비동기 사용이 어려운 관계로 마지막 파일을 읽고 나서 search_data 불러오기
"""
total_count: int = 0  # 총 파일 개수
read_count: int = 0  # 읽은 파일 개수
search_data: list[str | object] = []  # 검색어를 검색할 데이터


def drop_handler(event) -> None:
    """파일 드롭 수신

    Args:
        event (event): 이벤트
    """
    global total_count
    event.preventDefault()  # 파일이 열리지 않게 기존 이벤트 취소
    event.stopPropagation()
    items = event.dataTransfer.items
    for item in items:
        entry = item.webkitGetAsEntry()
        """
        폴더인지 아닌지 검사 후 폴더면 하위 디렉토리 재검색
        """
        if entry.isDirectory == True:
            get_directory_entries(entry)
        else:
            if is_pdf(entry.name) == False:  # PDF가 아니면 패스
                continue
            total_count += 1
            read_file(entry)


def is_pdf(filename: str) -> bool:
    """파일 이름을 기반으로 파일이 PDF인지 확인

    Args:
        filename (str): 파일명

    Returns:
        bool: PDF 확인 여부
    """
    _, ext = os.path.splitext(filename)
    return ext.lower() == ".pdf"


def get_directory_entries(entry) -> None:
    """DirectoryEntryList 객체를 list[DirectoryEntry]로 프록시

    Args:
        entry (DirectoryEntryList): 폴더 리스트 객체
    """
    entry.createReader().readEntries(create_proxy(get_entries))


def get_entries(entries) -> None:
    """DirectoryEntry 객체를 검사해 내부 파일 분류

    Args:
        entries (DirectoryEntry): 폴더 객체
    """
    global total_count
    for entry in entries:
        """
        폴더인지 아닌지 검사 후 폴더면 하위 디렉토리 재검색
        """
        if entry.isDirectory == True:
            get_directory_entries(entry)
        else:
            if is_pdf(entry.name) == False:  # PDF가 아니면 패스
                continue
            total_count += 1
            read_file(entry)


def isEntry(object) -> bool:
    """객체가 Entry인지 아닌지 검사

    Args:
        object (DirectoryEntry | FileEntry | any): 검사할 객체

    Returns:
        bool: 검사여부
    """
    try:
        object.isFile  # Entry가 아니라면 속성이 없으므로 에러 발생 -> except 실행
        return True
    except:
        return False


def read_file(entry) -> None:
    """파일 읽기 프록시

    Args:
        entry (FileEntry): 파일
    """
    entry.file(create_proxy(read_text))


def read_text(file) -> None:
    """파일 읽기

    Args:
        file (File): 읽을 파일
    """
    reader = FileReader.new()

    def onload(e):
        global read_count, total_count, search_data
        pdf_bytes = BytesIO(e.target.result.to_py())  # ArrayBuffer를 Bytes로 변환
        reader = pypdf.PdfReader(pdf_bytes)
        results: list[str] = []  # 결과 저장 위치
        for page in reader.pages:
            text: str = page.extract_text()
            if "파이썬".lower() in text.lower():
                results.append(
                    f"페이지 {reader.pages.index(page)+1}: {text}")  # 결과 저장
        search_data.append(results)  # 최종 결과에 저장
        read_count += 1
        if total_count == read_count:
            print(search_data)
    reader.addEventListener('load', create_proxy(onload))  # 파일 읽기에 성공하면 이벤트 호출
    reader.readAsArrayBuffer(file)  # JS의 ArrayBuffer로 읽기


def dragover_handler(event) -> None:
    """Dragover 이벤트 수신

    CSS 활용 또는 제거 예정

    Args:
        event (event): 이벤트
    """
    event.preventDefault()


"""
JS 이벤트 핸들러
"""
drop_zone = document.getElementById("drop_zone")
drop_zone.addEventListener('drop', create_proxy(drop_handler))
drop_zone.addEventListener('dragover', create_proxy(dragover_handler))

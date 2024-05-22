/**
 * PDF를 불러옵니다.
 * @param {ArrayBuffer} arrayBuffer
 * @param {number} page
 */
function setPDF(arrayBuffer, page) {
  let uint8Array = new Uint8Array(arrayBuffer);
  pdfjsLib
    .getDocument(uint8Array)
    .promise.then((pdf) => {
      pdf.getPage(page).then(renderPage);
      console.log("PDF 로드 성공");
    })
    .catch(function (error) {
      console.error("PDF 로드 실패", error);
    });
}
/**
 * PDF 페이지를 렌더링합니다.
 * @param {pdfjslib.PDFPageProxy} page
 */
function renderPage(page) {
  let canvas = document.createElement("canvas");
  canvas.id = `pdf-canvas`;
  let ctx = canvas.getContext("2d");
  let viewport = page.getViewport({ scale: 1.5 });
  canvas.height = viewport.height;
  canvas.width = viewport.width;
  document.getElementById("pdf-container").appendChild(canvas);
  let renderContext = {
    canvasContext: ctx,
    viewport: viewport,
  };
  page.render(renderContext);
}
/**
 * PDF 이미지를 불러옵니다.
 * @param {ArrayBuffer} arrayBuffer
 */
async function getPDFImage(arrayBuffer) {
  let images = [];
  pdfjsLib
    .getDocument(arrayBuffer)
    .promise.then((pdf) => {
      let pages = [];
      for (var i = 1; i <= pdf.numPages; i++) {
        pages.push(i);
      }
      return Promise.all(
        pages.map((pageNum) => {
          return pdf.getPage(pageNum).then((page) => {
            return page.getOperatorList().then((ops) => {
              const fns = ops.fnArray,
                args = ops.argsArray;
              args.forEach((arg, i) => {
                if (fns[i] !== pdfjsLib.OPS.paintJpegXObject) return;
                let imgKey = arg[0];
                page.objs.get(imgKey, (img) => {
                  images.push({ url: img.src, page: page });
                });
              });
            });
          });
        })
      );
    })
    .then(function () {
      readImgListText(images);
    })
    .catch(function (error) {
      console.error("Error: " + error);
    });
}
/**
 * 이미지에 있는 텍스트를 읽고 검색에 성공하면 렌더링
 * @param {[{url:string, page:pdfjsLib.PDFPageProxy}]} imgArray page.url은 Base64
 */
async function readImgListText(imgArray) {
  search_keyword = "데이터"; // 임시
  for (let img of imgArray) {
    await Tesseract.recognize(img.url, "eng+kor")
      .then(({ data: { text } }) => {
        text = text.replace(/\s+/g, "");
        console.log(text);
        if (text.includes(search_keyword)) renderPage(img.page);
        else return;
      })
      .catch((err) => {
        console.error(err);
      });
  }
}

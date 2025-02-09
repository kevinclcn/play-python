import os, sys
import logging
from fpdf import FPDF
from PIL import Image
from playwright.sync_api import Playwright, sync_playwright, expect, APIRequestContext
from urllib.parse import urlparse, parse_qs

def get_and_save_to_img(url: str, filename: str, request: APIRequestContext):
    response = request.get(url)
    if response.ok:
        image_content = response.body()
        with open(filename, 'wb') as file:
            file.write(image_content)
    else:
        logging.error(f"get image failed: {response.status_code}")


def get_pages(url: str, request: APIRequestContext):
    try:
        response = request.get(url)
        if response.ok:
            return response.json()
        else:
            logging.error(f"get page failed: {response.status_code}")
    except Exception as e:
        logging.exception("get page exception: ",e)

def images_in_dir_to_pdf(image_dir, output_pdf_path):
    # 创建一个 PDF 对象
    pdf = FPDF()
    # 支持的图片文件扩展名
    supported_extensions = ('.png', '.jpg', '.jpeg')
    # 获取目录下所有图片文件，并按文件名排序
    image_files = [os.path.join(image_dir, f) for f in os.listdir(image_dir)
                   if f.lower().endswith(supported_extensions)]
    image_files.sort()

    for image_path in image_files:
        try:
            # 打开图片
            img = Image.open(image_path)
            width, height = img.size
            # 将图片尺寸转换为 PDF 单位（毫米）
            width_mm = width * 25.4 / 72
            height_mm = height * 25.4 / 72

            # 添加一个新页面
            pdf.add_page()

            # 计算图片在 PDF 页面上的位置和缩放比例，以适应页面
            if width_mm > pdf.w - 20:
                height_mm = height_mm * (pdf.w - 20) / width_mm
                width_mm = pdf.w - 20
            if height_mm > pdf.h - 20:
                width_mm = width_mm * (pdf.h - 20) / height_mm
                height_mm = pdf.h - 20

            # 将图片添加到 PDF 页面上
            pdf.image(image_path, x=(pdf.w - width_mm) / 2, y=(pdf.h - height_mm) / 2, w=width_mm, h=height_mm, type=img.format)
        except Exception as e:
            # print(f"Error processing {image_path}: {e}")
            logging.exception(e)

    # 保存 PDF 文件
    pdf.output(output_pdf_path)

def crawl_mba_essay(fid: str, filename: str, request):

    if not os.path.exists(filename):
        os.makedirs(filename, exist_ok=True)

    url_template = "https://drm.fudan.edu.cn/read/jumpServlet?page={page_id}&fid={fid}"

    page_id = 0
    processed_pages = set()
    while True: 
        
        url = url_template.format(page_id=page_id,fid=fid,filename=filename)
        pages = get_pages(url, request=request)
        next_id = page_id
        for page in pages["list"]:
            id = int(page["id"])
            if id > next_id:
                next_id = id
            if id in processed_pages:
                continue
            print(f"downloading page {id}")
            processed_pages.add(id)
            get_and_save_to_img(page["src"], f"{filename}/page_{int(page['id']):0{3}d}.jpeg", request)

        if int(next_id) <= page_id:
            break
        page_id = int(next_id)


def run(playwright: Playwright, filename) -> None:
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://thesis.fudan.edu.cn/")
    page.locator("#keyword").click()
    page.locator("#keyword").click()
    page.locator("#keyword").fill(filename)
    page.locator("#searchform a").first.click()
    with page.expect_popup() as page1_info:
        page.locator("iframe[name=\"frame_content\"]").content_frame.get_by_role("row", name="1").locator("a").click()
    page1 = page1_info.value
    with page1.expect_popup() as page2_info:
        page1.get_by_role("link", name="查看全文").click()
    page2 = page2_info.value

    parsed_url = urlparse(page2.url)
    query_params = parse_qs(parsed_url.query)
    fid = query_params["fid"][0]

    crawl_mba_essay(fid, filename, page2.context.request)
    images_in_dir_to_pdf(filename, f"{filename}.pdf")

    # ---------------------
    context.close()
    browser.close()




if __name__ == "__main__":
    arg_count = len(sys.argv) - 1
    if arg_count == 0:
        print("Usage: crawl_mba_essay.py <filename>")
        sys.exit(1)
    
    filename = sys.argv[1]

    with sync_playwright() as playwright:
        run(playwright, filename=filename)


import requests
import fitz
from PIL import Image


def read_image(image_path: str) -> bytes:
    image_bytes = Image.open(image_path)

    return image_bytes


def pdf_to_images(file_bytes: bytes) -> list[bytes]:
    doc = fitz.open(stream=file_bytes, filetype="pdf")

    # Iterate over each page and convert it to an image
    image_list = [
        doc.load_page(n).get_pixmap().pil_tobytes(format="JPEG")
        for n, _ in enumerate(doc.pages())
    ]

    doc.close()

    return image_list


def images_to_display(file_extension: str, file_bytes: bytes) -> list[bytes]:
    # display image
    images_to_display = []
    match file_extension:
        case "pdf":
            images_to_display = pdf_to_images(file_bytes)
        case "jpeg" | "jpg":
            images_to_display.append(file_bytes)

    return images_to_display


def call_authorization(
    url: str, host: str, client_id: str, client_secret: str, grant_type: str
) -> str:
    # Call the api with the file and the api key
    r = requests.post(
        url,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Host": host,
        },
        params={"grant_type": grant_type},
        data={"client_id": client_id, "client_secret": client_secret},
        verify=False,
    )

    return r.json()["access_token"]


def call_api(
    file_bytes: bytes,
    file_extension: str,
    url: str,
    api_key: str,
    params: dict = str,
    access_token: None | str = None,
) -> requests.Response:
    match file_extension:
        case "pdf":
            content_type = "application/pdf"
        case "jpeg" | "jpg":
            content_type = "image/jpeg"

    headers = {
        "x-api-key": api_key,
        "Content-Type": content_type,
        # "Accept": "*/*",
        # "Accept-Encoding": "gzip, deflate, br",
        # "Connection": "keep-alive",
        # "User-Agent": "python-requests/2.25.1",
        # "Host": "real-time-ocr-gateway-3bcpgr34.ew.gateway.dev",
    }

    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"

    # Call the api with the file and the api key
    r = requests.post(url, files={"file": file_bytes}, headers=headers, params=params)

    return r

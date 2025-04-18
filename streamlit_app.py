import logging

import streamlit as st
from benedict import benedict
from streamlit.runtime.uploaded_file_manager import UploadedFile

from sanitize import sanitize_dict
from utils import (
    call_authorization,
    call_bill_api,
    call_doc_api,
    images_to_display,
    read_image,
)


def process_single_upload(file_upload: UploadedFile) -> dict:
    # Process file type
    file_extension = file_upload.name.split(".")[-1].lower()
    match file_extension:
        case "pdf":
            file_content_type = "application/pdf"
        case "jpeg" | "jpg":
            file_content_type = "image/jpeg"
        case "png":
            file_content_type = "image/png"

    # Process file content
    file_bytes = file_upload.getvalue()

    # Process file name
    file_name = file_upload.name

    return {"name": file_name, "bytes": file_bytes, "content_type": file_content_type}


# Load streamlit secrets. The secrets are stored in the .streamlit/secrets.toml file.
# To add a new variable, add it in the secrets.toml file and restart the streamlit server.
api_key = st.secrets["API_KEY"]
apis = {
    "id": {
        "url": st.secrets["API_URL_ID"],
        "response_fields": {
            "campi_documento.nome": "Name :bust_in_silhouette:",
            "campi_documento.cognome": "Surname :busts_in_silhouette:",
            "campi_documento.id_documento": "ID :information_source:",
            "campi_documento.data_scadenza": "Expiration date :calendar:",
            "tipo_documento": "Type of document :bookmark_tabs:",
            "dati_validi": "Document validity :white_check_mark:",
        },
        "accept_multiple_files": True,
    },
    "invoices": {
        "url": st.secrets["API_URL_INVOICES"],
        "response_fields": {
            "output_data.name": "Name :bust_in_silhouette:",
            "output_data.surname": "Surname :busts_in_silhouette:",
            "output_data.odonym_meter_address": "Address (odonym) :house:",
            "output_data.number_meter_address": "Address (street number) :house:",
            "output_data.cap_meter_address": "Postal Code :postbox:",
            "output_data.city_meter_address": "City :cityscape:",
            "output_data.province_meter_address": "Province :mountain:",
            "output_data.cod_fiscale": "Fiscal Code :female-detective:",
        },
        "accept_multiple_files": False,
    },
}

invoice_commodity = ["gas", "luce", "dual"]
invoice_language = ["it", "es"]
favicon_bytes = read_image("assets/favicon.ico")
st.set_page_config(
    layout="wide", page_title="DataLens Demo Web", page_icon=favicon_bytes
)

st.write("# Check document with the selected DataLens solution :mag_right:")
# logo_bytes = read_image("assets/logo.png")
# st.sidebar.image(logo_bytes, clamp=False, channels="RGB", output_format="auto")
st.sidebar.write("## Configure Request :gear:")

# Create two columns with streamlit function st.columns
col1, col2 = st.columns(2)

# Select which API to use
selected_api = st.sidebar.radio("Select API:", ["id", "invoices"])
selected_config = apis[selected_api]

# If invoices add params
params = {}
headers = {}
if selected_api == "invoices":
    selected_commodity = st.sidebar.radio("Select commodity type:", invoice_commodity)
    selected_language = st.sidebar.radio("Select invoice language:", invoice_language)
    params = {"commodity": selected_commodity}
    headers = {"language": selected_language}
    if selected_commodity == "dual":
        selected_config["response_fields"].update(
            {
                "output_data.PDR": "PDR :pushpin:",
                "output_data.use_type": "Gas usage type :diya_lamp:",
                "output_data.gas_total_annual_consumption": "Total annual gas consumption :fire:",
                "output_data.POD": "POD :round_pushpin:",
                "output_data.engaged_power": "Engaged power :electric_plug:",
                "output_data.power_total_annual_consumption": "Total annual power consumption :bulb:",
            }
        )
    elif selected_commodity == "gas":
        selected_config["response_fields"].update(
            {
                "output_data.PDR": "PDR :pushpin:",
                "output_data.use_type": "Gas usage type :diya_lamp:",
                "output_data.gas_total_annual_consumption": "Total annual gas consumption :fire:",
            }
        )
    elif selected_commodity == "luce":
        selected_config["response_fields"].update(
            {
                "output_data.POD": "POD :round_pushpin:",
                "output_data.engaged_power": "Engaged power :electric_plug:",
                "output_data.power_total_annual_consumption": "Total annual power consumption :bulb:",
            }
        )

# Upload the file to send with the request
file_upload = st.sidebar.file_uploader(
    "Choose a file:",
    type=["pdf", "jpeg", "jpg", "png"],
    accept_multiple_files=selected_config["accept_multiple_files"],
)
if file_upload is not None:
    # Process uploads
    if not isinstance(file_upload, list):
        file_upload = [file_upload]
    file_upload = [process_single_upload(file_upload=fu) for fu in file_upload]

    # Display the uploaded files
    col1.write("## Uploaded documents")

    for file in file_upload:
        col1.write(f"Document \"{file['name']}\" ({file['content_type']})")

        # Display images
        for image_bytes in images_to_display(
            content_type=file["content_type"], file_bytes=file["bytes"]
        ):
            col1.image(image_bytes, clamp=False, channels="RGB", output_format="auto")


# Add a button to call the api
call_api_button = st.sidebar.button("Call the API")

# Call the api when the button is clicked
if call_api_button:
    logging.info(f"Calling the API {selected_api}")

    access_token = call_authorization(
        url=st.secrets["AUTH_URL"],
        client_id=st.secrets["AUTH_CLIENT_ID"],
        client_secret=st.secrets["AUTH_CLIENT_SECRET"],
        grant_type="client_credentials",
    )

    match selected_api:
        case "invoices":
            response = call_bill_api(
                file_bytes=file_upload[0]["bytes"],
                file_content_type=file_upload[0]["content_type"],
                url=selected_config["url"],
                api_key=api_key,
                params=params,
                headers=headers,
                access_token=access_token,
            )
        case "id":
            response = call_doc_api(
                file_list=file_upload,
                url=selected_config["url"],
                api_key=api_key,
                params=params,
                headers=headers,
                access_token=access_token,
            )

    col2.write("## Response")
    try:
        data = sanitize_dict(response.json())

        # Pretty print response
        output_data = benedict(data, keypath_separator=".")

        if selected_api == 'id':
            for f_name, f_desc in selected_config["response_fields"].items():
                col2.write(f"#### {f_desc}")
                col2.write(output_data[f_name])
        else:
            for f_name, f_desc in selected_config["response_fields"].items():
                col2.write(f"#### {f_desc}")
                col2.write(output_data['extracted_fields'][f_name.split('.')[1]])


        # Print raw json response
        col2.write(f"### Raw response content (status {response.status_code}):")
        col2.write(f"Response time: {response.elapsed.total_seconds()}s")
        col2.json(data, expanded=True)
    except Exception:
        # Print raw json response
        col2.write(f"### Raw response content (status {response.status_code}):")
        col2.write(f"Response time: {response.elapsed.total_seconds()}s")
        col2.write(sanitize_dict(response.text))

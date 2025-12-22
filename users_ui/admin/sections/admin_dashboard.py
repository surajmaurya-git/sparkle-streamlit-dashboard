import streamlit as st
import pandas as pd

def create_unit(serial_number):
    host=st.secrets["SPARKLE_API_HOST"]
    path="/v1/admin/createUnit"
    url=host+path
    payload={
    "unitName": "1312202502",
    "unitSerialNo": serial_number,
    "connectivityModuleId": "CM-",
    "productId": "019b16e9-1d65-7c40-bbbc-4c4a0c14a1bd",
    "metadata": {},
    "tags": {}
    }
    apikey=st.secrets["SPARKLE_API_KEY"]
    headers={
    'Content-Type': 'application/json',
    'Authorization': f"Bearer {apikey}"
    }
    st.write(url)
    response = st.session_state.http_client.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        st.success("Unit created successfully")
        return True
    else:
        st.error(f"Failed to create unit. Status code: {response.status_code}, Response: {response.text}")
        return False
def list_units():
    host=st.secrets["SPARKLE_API_HOST"]
    path="/v1/admin/listUnits"
    url=host+path
    apikey=st.secrets["SPARKLE_API_KEY"]
    payload={}
    headers={
    'Content-Type': 'application/json',
    'Authorization': f"Bearer {apikey}"
    }
    response = st.session_state.http_client.post(url,json=payload, headers=headers)
    if response.status_code == 200:
        units=response.json().get("units",[])
        return units
    else:
        st.error(f"Failed to fetch units. Status code: {response.status_code}, Response: {response.text}")
        return []
    
def adminDashboard():
    headercols = st.columns([1,0.1, 0.1], gap="small")
    with headercols[0]:
        st.title("Admin Dashboard", anchor=False)
    with headercols[1]:
        on = st.button("Refresh")
        if on:
            st.rerun()
    with headercols[2]:
        logout = st.button("Logout")

    if logout:
        st.session_state.LoggedIn = False
        st.rerun()

    container = st.container(border=True)
    with container:
        # NODES_NAME=st.session_state.nodesId["identifier"]
        st.subheader("Create Unit")
        cols=st.columns(3,gap="large")
        with cols[0]:
            serial_numner = st.text_input("Enter Unit Serial Number",)
            cols_spacer=st.columns(3,gap="large")
            with cols_spacer[2]:
                submit= st.button("Create Unit")

        if submit:
            if serial_numner.strip() == "":
                st.error("Please enter a valid serial number.")
            else:
                create_unit(serial_numner.strip())
    container2 = st.container(border=True)
    with container2:
        st.subheader("Unit List")
        units = list_units()
        # st.write(units)
        if units:
            formatted_data = {
                "Serial Number": [unit["unitSerialNo"] for unit in units],
                "Unit Name": [unit["unitName"] for unit in units],
                "Status": [unit["status"] for unit in units],
                "Created At": [unit["createdAt"] for unit in units],
                "Updated At": [unit["updatedAt"] for unit in units],
            }

            data_df = pd.DataFrame(formatted_data)
            data_df.index += 1

            st.dataframe(
                data_df,
                use_container_width=True,
            )
        else:
            st.write("No units found.")

adminDashboard()
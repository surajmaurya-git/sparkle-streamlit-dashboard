import streamlit as st
from components.ui.unit_ui_components import unit_header
from components.ui.unit_ui_components import unit_details
from components.ui.unit_ui_components import cards_section
from components.ui.unit_ui_components import gauge_section
from components.ui.unit_ui_components import controllers_section
from components.ui.unit_ui_components import graph_section
from components.ui.unit_ui_components import map_section
from components.ui.unit_ui_components import settings_section
from components.ui.unit_ui_components import device_parameters
from cloud.anedya_cloud import Anedya

import os


def draw_unit_1_dashboard():

    file_name = os.path.basename(__file__).split(".")[0]
    pre_name = file_name.split("_")[0].capitalize()
    NODE_NUMBER = int(file_name.split("_")[1])
    
    NUMBER_OF_NODES = len(st.session_state.nodesId)
    if NUMBER_OF_NODES < NODE_NUMBER:
        st.error("Node ID not found")
        st.stop()

    anedya = Anedya()
    NODE_ID = st.session_state.nodesId[f"node_{NODE_NUMBER}"].get("id")
    NODE_NAME=st.session_state.nodesId[f"node_{NODE_NUMBER}"].get("name")
    node = anedya.new_node(st.session_state.anedya_client, nodeId=NODE_ID)
    device_status_res = node.get_deviceStatus()
    values={"water_limit":None,"expiry":None,"water_consumption":None, "left_water_limit": None, "tds_1":None, "tds_2": None} 

    # fetch plan status
    res = node.get_valueStore(key="PlanStatus")
    is_success = res.get("isSuccess")
    d= res.get("value")
    data = str(d) if d is not None else None
    if is_success is True and data is not None:
        data_list = data.split(",")
        if len(data_list) == 2:
            values["water_limit"] = float(data_list[0])
            values["expiry"] =int( data_list[1])
        else:
            st.error("Invalid data format")
    
    # fetch water consumption
    wRes = node.get_valueStore(key="WaterCons")
    if wRes.get("isSuccess") is True and wRes.get("value") is not None:
         values["water_consumption"] = float(wRes.get("value"))

    # Left water limit
    if(values["water_limit"] is not None and values["water_consumption"] is not None):
        values["left_water_limit"] = values["water_limit"] - values["water_consumption"]

    is_tds=st.session_state.nodesId[f"node_{NODE_NUMBER}"].get("tds")
    if is_tds:
        # Fetch tds 1 value
        tds1Res=node.get_latestData("tds1")
        if tds1Res.get("isSuccess") is True and tds1Res.get("data") is not None:
            values["tds_1"] = tds1Res.get("data")

        # Fetch tds 2 value
        tds2Res=node.get_latestData("tds2")
        if tds2Res.get("isSuccess") is True and tds2Res.get("data") is not None:
            values["tds_2"] = tds2Res.get("data")

    unit_header(
        f"{NODE_NAME}",
        node_client=node,
        device_status_res=device_status_res,
    )


    # Plot the dashboard
    unit_details(NODE_ID)
    # gauge_section(node)
    cards_section(node, values)
    settings_section(node, values)
    device_parameters(node)
    # controllers_section(node)
    graph_section(node)
    map_section(node)


draw_unit_1_dashboard()

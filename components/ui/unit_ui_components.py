import streamlit as st
import streamviz as sv
from datetime import datetime, timedelta
import pytz
import numpy as np
import pandas as pd
import time
from dateutil import relativedelta
from components.charts import draw_chart
from components.ui.time_range_controller import (
    get_default_time_range,
    auto_update_time_range,
    update_time_range,
    reset_time_range,
    is_within_tolerance,
)

from components.custome_component import draw_custom_tile

is_options_changed = False


def unit_header(title, des=None, node_client=None, device_status_res=None):
    if title is None:
        st.error("Please provide a valid title.")
    VARIABLES = st.session_state.variables
    headercols = st.columns([1, 0.12, 0.11, 0.11], gap="small")
    with headercols[0]:
        st.title(title, anchor=False)
    with headercols[1]:
        device_status = None
        if device_status_res is not None or device_status_res.get("status") is True:
            if device_status_res.get("device_status"):
                device_status = "Online"
            else:
                device_status = "Offline"
        else:
            device_status = "..."

        with st.container(border=False, height=40):
            if device_status == "Online":
                st.markdown(
                    f"""
                    <div style="
                        margin-top: 0px;
                        height: 38px;
                        margin-right: 0px;
                        padding-top: 0;
                        overflow: hidden;
                        white-space: nowrap;
                        text-overflow: ellipsis;
                        font-size: 16px;
                        line-height: 25px;
                        color: white;
                        font-weight: 600;
                        background-color: green;
                        border-radius: 6px;
                        align-items: center;
                        justify-content: center;
                        text-align: center;
                        display: flex;
                    ">
                        {device_status}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"""
                    <div style="
                        margin-top: 0px;
                        height: 38px;
                        margin-right: 0px;
                        padding-top: 0;
                        overflow: hidden;
                        white-space: nowrap;
                        text-overflow: ellipsis;
                        font-size: 16px;
                        line-height: 25px;
                        color: white;
                        font-weight: 600;
                        background-color: red;
                        border-radius: 6px;
                        align-items: center;
                        justify-content: center;
                        text-align: center;
                        display: flex;
                    ">
                        {device_status}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    with headercols[2]:
        on = st.button("Refresh")
        if on:
            st.rerun()
    with headercols[3]:
        logout = st.button("Logout")
        if logout:
            st.session_state.LoggedIn = False
            st.rerun()
    if des is not None:
        st.markdown(des)


def unit_details(data):
    # res=node_client.get_valueStore(key="DEVICEINFO")
    # st.write(res)
    # res_json=json.loads(res)
    # st.write(data)
    st.markdown(f"**Node ID:** {data}")
    # st.markdown(f"**Firmware:**  ")
    # st.text(f"IMEI No.: {data.get('imei_id')}")


def cards_section(node_client=None, values: dict = {}):
    container = st.container(border=True, height=150)
    with container:
        # st.subheader(body="Parameters", anchor=False)
        r1_cols = st.columns([1, 1, 1, 1], gap="large")
        with r1_cols[0]:
            left_water_limit = values["left_water_limit"]
            if left_water_limit is not None:
                if left_water_limit <= 0:
                    left_water_limit = int(left_water_limit)
                    draw_custom_tile("Remaining Water", f"{left_water_limit:.2f} L", "red")
                else:
                    draw_custom_tile(
                        "Remaining Water", f"{left_water_limit:.2f} L", "white"
                    )
            else:
                draw_custom_tile("Remaining Water", "N/A", "red")
        with r1_cols[1]:
            tds_1 = values["tds_1"]
            if tds_1 is not None:
                tds_1 = round(tds_1)
                draw_custom_tile("TDS 1", f"{tds_1} ppm", "white")
            # else:
            #     draw_custom_tile("TDS 1", "N/A", "red")
        # with r1_cols[2]:
        #     tds_2 = values["tds_2"]
        #     if tds_2 is not None:
        #         tds_2 = round(tds_2)
        #         draw_custom_tile("TDS 2", f"{tds_2} ppm", "white")
        #     # else:
        
        #     #     draw_custom_tile("TDS 2", "N/A", "red")
        with r1_cols[2]:
            todays_water_consumption = values["water_consumption_daily"]
            if todays_water_consumption is not None:
                draw_custom_tile(
                    "Water Consumption of the Day", f"{todays_water_consumption:.2f} L", "white"
                )
            else:
                draw_custom_tile(
                    "Water Consumption of the Day", f"N/A", "white"
                )


def settings_section(node_client=None, values: dict = {}):
    container = st.container(border=True, height=510)
    with container:
        st.header(body="Subscription Management", anchor=False)
        r1_cols = st.columns([1, 1, 1, 1], gap="large")
        value, water_limit, expiry = -1, 0, ""

        with r1_cols[0]:
            value = values["water_consumption"]
            if value is not None:
                draw_custom_tile("Total Water Consumption", f"{value:.2f} L", "white")
            else:
                draw_custom_tile("Total Water Consumption", f"N/A", "white")
        with r1_cols[1]:
            water_limit = values["water_limit"]
            if water_limit is not None:
                draw_custom_tile("Water Limit", f"{water_limit} L", "white")

            else:
                draw_custom_tile("Water Limit", f"N/A", "white")

        with r1_cols[2]:
            expiry = values["expiry"]
            if expiry is not None:
                draw_custom_tile(
                    "Plan Expiry Date",
                  f"{datetime.fromtimestamp(expiry).strftime('%Y-%m-%d | %H:%M:%S')}",
                    "white",
                )
            else:
                draw_custom_tile("Plan Expiry Date", f"N/A", "white")

        if water_limit is not None and value is not None:
            if value >= water_limit and water_limit != 0:
                st.warning("Water limit has been reached.", icon="🚨")

        con_1 = st.container(border=True)
        with con_1:
            st.subheader("Renew Plan", anchor=False)
            # cols= st.columns([1, 1,1], gap="small")
            # with cols[0]:
            r1_cols = st.columns(
                [0.5, 1, 0.26, 0.26, 0.14],
                # gap="none",
                vertical_alignment="center",
            )
            with r1_cols[0]:
                res=node_client.get_valueStore(key="DailyWaterLimit")
                value=res.get("value")
                # st.write(value)
                value= st.number_input("Daily Water Limit",step=1, value=value)
                r1_r1_cols=st.columns([0.7,1],gap="small")
                with r1_r1_cols[0]:
                    pass
                with r1_r1_cols[1]:
                    submit = st.button("Set", key="daily_water_limit_set",width="stretch")
                    if submit:
                        res=node_client.set_valueStore(key="DailyWaterLimit",value=value,type="float")
                        # st.write(res)
                        if(res.get("isSuccess") is True):
                            st.toast("Daily Water Limit value updated",icon="🎉")
                        else:
                            # st.write(res)
                            mess=f"Failed to set the Daily Water Limit value"
                            st.toast(mess,icon="❌")
            with r1_cols[1]:
                expiry_mode = st.radio(
                    "Expiry Mode",
                    ["Date", "Days"],
                    horizontal=True,
                    key="expiry_mode_radio",
                    label_visibility="collapsed",
                )
                if expiry_mode == "Date":
                    date_time=st.datetime_input(
                    "Expiry Time",
                    key="expiry_time",
                    value=datetime.now() + relativedelta.relativedelta(months=1),
                    step=300,
                    )
                    expiry = (
                        int(datetime.strptime(str(date_time), "%Y-%m-%d %H:%M:%S").timestamp())
                    )  # Adding 1 day to the epoch time
                    # st.write(f'Epoch Time: {expiry}')
                else:
                    days_to_add = st.number_input(
                        "Days to Add",
                        min_value=0,
                        value=30,
                        key="expiry_days_input",
                    )
                    # Fetch existing expiry from values (Anedya)
                    current_expiry = values.get("expiry", 0)
                    if current_expiry is None or current_expiry == 0:
                        base_time = time.time()
                    else:
                        base_time = current_expiry

                    expiry = int(base_time + (days_to_add * 86400))
                    # Show the resulting date for confirmation 
                    res_date = datetime.fromtimestamp(expiry).strftime("%Y-%m-%d")
                    # st.caption(f"Will expire on: {res_date}")
            with r1_cols[2]:
                data = node_client.get_valueStore(key="PlanStatus")
                value = 0
                if data.get("isSuccess") is True and data.get("value") is not None:
                    value_str = data.get("value")
                    v = float(value_str.split(",")[0])
                    value = float(v)
                submit = st.button("Renew")
                if submit:
                    try:
                                PlanStatusPayload = f"1000000,{expiry}"

                                res = node_client.set_valueStore(
                                    key="PlanStatus", value=PlanStatusPayload, type="string"
                                )
                                cmd_res=node_client.send_command("PlanStatus", PlanStatusPayload)

                                if res.get("isSuccess") is False or cmd_res.get("isSuccess")==False:
                                    st.toast("Fail to set Plan Status", icon="🚫")
                                    st.stop()
                                syncRes = node_client.set_valueStore(
                                    "IsPlanSync", value=False, type="boolean"
                                )
                                if syncRes.get("isSuccess") is False:
                                    st.toast("Fail to set IsPlanSync", icon="🚫")
                                    st.stop()

                                st.toast("Recharge successful", icon="🎉")
                                time.sleep(1)
                                st.rerun()

                    except ValueError:
                            st.toast("Recharge value must be a float or int", icon="🚫")
                            # st.stop()
                    

            with r1_cols[3]:
                reset = st.button("Reset")
                if reset:
                    current_time = int(time.time())
                    PlanStatusPayload = f"0,{current_time}"
                    res = node_client.set_valueStore(
                        key="PlanStatus", value=PlanStatusPayload, type="string"
                    )

                    wlRes = node_client.set_valueStore(
                        key="WaterCons", value=0, type="float"
                    )
                    syncRes = node_client.set_valueStore(
                                "IsPlanSync", value=False, type="boolean"
                            )
                    if syncRes.get("isSuccess") is False:
                                st.toast("Fail to set IsPlanSync", icon="🚫")
                                st.stop()
                    if res.get("isSuccess") is False or wlRes.get("isSuccess") is False or syncRes.get("isSuccess") is False:
                        st.error("Fail to set Plan Status")
                        st.stop()
                    st.toast("Reset the plan", icon="🎉")
                    time.sleep(1)
                    st.rerun()
            with r1_cols[4]:
                plan_sync_status = node_client.get_valueStore(key="IsPlanSync")
                if (
                    plan_sync_status.get("isSuccess") is True
                    and plan_sync_status.get("value") is not None
                ):
                    value = plan_sync_status.get("value")
                    if value == True:
                        # st.markdown("🔄")
                        st.markdown(
                            f"""
                        <div style="font-size: 30px; 
                                 margin-bottom: 12px;">✅</div>
                                """,
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            f"""
                        <div style="font-size: 30px; 
                                 margin-bottom: 12px;">⏳</div>
                                """,
                            unsafe_allow_html=True,
                        )


def device_parameters(node_client=None):
    container = st.container(border=True, height=220)
    with container:
        st.subheader(body="Device Parameters", anchor=False)
        # res = node_client.get_valueStore(key="PlanStatus")
        r1_cols = st.columns([1, 1, 1, 1], gap="small")
        with r1_cols[0]:
            draw_custom_tile("Device Health", "100%", "green")
        # with r1_cols[1]:
        #     draw_custom_tile("Pump", "OFF")

        # with r1_cols[2]:
        #      draw_custom_tile("Motor 2 Status", "ON", "green")


def gauge_section(node_client=None):
    container = st.container(border=True, height=330)
    VARIABLES = st.session_state.variables
    with container:

        indian_time_zone = pytz.timezone("Asia/Kolkata")  # set time zone
        r1_guage_cols = st.columns([1, 1, 1, 1], gap="small")
        with r1_guage_cols[0]:
            VARIABLE = VARIABLES["variable_1"]
            data = node_client.get_latestData(VARIABLE["identifier"])
            if data.get("data") != None:
                timestamp = data.get("timestamp")
                hr_timestamp = datetime.fromtimestamp(timestamp, indian_time_zone)
                fm_hr_timestamp = hr_timestamp.strftime("%Y-%m-%d %H:%M:%S %Z")
                st.markdown(f"**Last Updated:** {fm_hr_timestamp}")
                value = data.get("data")
                sv.gauge(
                    value,
                    VARIABLE["name"],
                    gMode="number",
                    cWidth=True,
                    gSize="MED",
                    sFix=VARIABLE["unit"],
                    arTop=int(VARIABLE["top_range"]),
                    arBot=int(VARIABLE["bottom_range"]),
                )
            else:
                st.error("No Data Available")
        with r1_guage_cols[1]:
            VARIABLE = VARIABLES["variable_2"]
            data = node_client.get_latestData(VARIABLE["identifier"])
            if data.get("data") != None:
                timestamp = data.get("timestamp")
                hr_timestamp = datetime.fromtimestamp(timestamp, indian_time_zone)
                fm_hr_timestamp = hr_timestamp.strftime("%Y-%m-%d %H:%M:%S %Z")
                st.markdown(f"**Last Updated:** {fm_hr_timestamp}")
                value = data.get("data")
                sv.gauge(
                    value,
                    VARIABLE["name"],
                    gMode="number",
                    cWidth=True,
                    gSize="MED",
                    sFix=VARIABLE["unit"],
                    arTop=int(VARIABLE["top_range"]),
                    arBot=int(VARIABLE["bottom_range"]),
                )
            else:
                st.error("No Data Available")

        with r1_guage_cols[2]:
            VARIABLE = VARIABLES["variable_3"]
            data = node_client.get_latestData(VARIABLE["identifier"])
            if data.get("data") != None:
                timestamp = data.get("timestamp")
                hr_timestamp = datetime.fromtimestamp(timestamp, indian_time_zone)
                fm_hr_timestamp = hr_timestamp.strftime("%Y-%m-%d %H:%M:%S %Z")
                st.markdown(f"**Last Updated:** {fm_hr_timestamp}")
                value = data.get("data")
                sv.gauge(
                    value,
                    VARIABLE["name"],
                    cWidth=True,
                    gSize="MED",
                    sFix=VARIABLE["unit"],
                    arTop=int(VARIABLE["top_range"]),
                    arBot=int(VARIABLE["bottom_range"]),
                )
            else:
                st.error("No Data Available")
        with r1_guage_cols[3]:
            VARIABLE = VARIABLES["variable_4"]
            data = node_client.get_latestData(VARIABLE["identifier"])
            if data.get("data") != None:
                timestamp = data.get("timestamp")
                hr_timestamp = datetime.fromtimestamp(timestamp, indian_time_zone)
                fm_hr_timestamp = hr_timestamp.strftime("%Y-%m-%d %H:%M:%S %Z")
                st.markdown(f"**Last Updated:**  {fm_hr_timestamp}")
                value = data.get("data")
                arTop = int(VARIABLE["top_range"])
                arBot = int(VARIABLE["bottom_range"])
                sv.gauge(
                    value,
                    VARIABLE["name"],
                    cWidth=True,
                    gSize="MED",
                    sFix="V",
                    arTop=arTop,
                    arBot=arBot,
                )
            else:
                st.error("No Data Available")


def sync_controllers_state(node_client=None):

    res = node_client.get_valueStore(key="door")
    if res.get("isSuccess") is True and res.get("value") is not None:
        value = res.get("value")
        if value == 0:
            st.session_state.door = "Open Door"
        elif value == 1:
            st.session_state.door = "Close Door"
        else:
            print("Invalid value")

    res = node_client.get_valueStore(key="light")
    if res.get("isSuccess") is True and res.get("value") is not None:
        value = res.get("value")
        if value == 0:
            st.session_state.light = "Turn Light On"
        elif value <= 5:
            st.session_state.light = "Turn Light Off"
        else:
            print("Invalid value")

    res = node_client.get_valueStore(key="fan")
    if res.get("isSuccess") is True and res.get("value") is not None:
        value = res.get("value")
        if value == 1:
            st.session_state.fan = "Turn Fan Off"
        elif value <= 3:
            st.session_state.fan = "Turn Fan On"

    res = node_client.get_valueStore(key="massage")
    if res.get("isSuccess") is True and res.get("value") is not None:
        value = res.get("value")
        if value == 1:
            st.session_state.massage = "Turn Massager Off"
        else:
            st.session_state.massage = "Turn Massager On"


def controllers_section(node_client=None):
    if node_client is None:
        st.stop()
    container = st.container(border=True)
    with container:
        st.subheader(body="Controllers", anchor=False)
        sync_controllers_state(node_client=node_client)
        r1_cols = st.columns([1, 1, 1, 1], gap="small")
        with r1_cols[0]:
            st.subheader("Door")
            state = st.button(st.session_state.door, key="door_key")
            if state:
                if st.session_state.door == "Open Door":
                    st.session_state.door = "Close Door"
                    node_client.set_valueStore(key="door", value=1, type="float")
                else:
                    st.session_state.door = "Open Door"
                    node_client.set_valueStore(key="door", value=0, type="float")
                st.rerun()
        with r1_cols[1]:
            st.subheader("Light")
            state = st.button(st.session_state.light, key="light_toggle")
            if state:
                if st.session_state.light == "Turn Light On":
                    st.session_state.light = "Turn Light Off"
                    node_client.set_valueStore(key="light", value=1, type="float")
                else:
                    st.session_state.light = "Turn Light On"
                    node_client.set_valueStore(key="light", value=0, type="float")
                st.rerun()
        with r1_cols[2]:
            st.subheader("Fan")
            state = st.button(st.session_state.fan, key="fan_toggle")
            if state:
                if st.session_state.fan == "Turn Fan On":
                    st.session_state.fan = "Turn Fan Off"
                    node_client.set_valueStore(key="fan", value=1, type="float")
                else:
                    st.session_state.fan = "Turn Fan On"
                    node_client.set_valueStore(key="fan", value=0, type="float")
                st.rerun()
        with r1_cols[3]:
            st.subheader("Massager")
            state = st.button(st.session_state.massage, key="massage_toggle")
            if state:
                if st.session_state.massage == "Turn Massager On":
                    st.session_state.massage = "Turn Massager Off"
                    node_client.set_valueStore(key="massage", value=1, type="float")
                else:
                    st.session_state.massage = "Turn Massager On"
                    node_client.set_valueStore(key="massage", value=0, type="float")
                st.rerun()


def handle_change(*args, **kwargs):
    st.write("Selection changed!")
    st.write("Args:", args)
    st.write("Kwargs:", kwargs)


def graph_section(node_client=None):
    global is_options_changed
    if node_client is None:
        st.error("Invalid Node Client")
        st.stop()
    container = st.container(border=True)
    with container:
        st.subheader(body="Visualizations", anchor=False)
        currentTime = int(time.time())  # to means recent time
        pastHour_Time = int(currentTime - 86400)

        # -----------------------------------------Time range filter-----------------------------------------
        datetime_cols = st.columns(
            [1, 1, 0.2], gap="small", vertical_alignment="bottom"
        )

        with datetime_cols[0]:
            from_cols = st.columns(2, gap="small")
            with from_cols[0]:
                # st.text("From:")
                from_start_datetime = st.date_input(
                    "From", key="from:date", value=st.session_state.from_date
                )
            with from_cols[1]:
                from_time_input = st.time_input(
                    "time",
                    key="from:time",
                    value=st.session_state.from_time,
                    label_visibility="hidden",
                )

            if from_start_datetime and from_time_input:
                st.session_state.from_time = from_time_input
                st.session_state.from_date = from_start_datetime

                combined_datetime = pd.to_datetime(
                    f"{from_start_datetime} {from_time_input}"
                )
                # st.write("Combined datetime:", combined_datetime)
                # Define the India time zone
                india_tz = pytz.timezone("Asia/Kolkata")

                # Localize the combined datetime to the India time zone
                localized_datetime = india_tz.localize(combined_datetime)

                # Convert the localized datetime to epoch time
                from_time = int(localized_datetime.timestamp())
                if from_time != st.session_state.from_input_time:
                    st.session_state.from_input_time = from_time
                    st.rerun()

        with datetime_cols[1]:
            to_cols = st.columns(2)
            with to_cols[0]:
                # st.text("To:")
                to_start_datetime = st.date_input(
                    "To", key="to:date", value=st.session_state.to_date
                )
            with to_cols[1]:
                to_time_input = st.time_input(
                    "time",
                    key="to:time",
                    value=st.session_state.to_time,
                    label_visibility="hidden",
                )
            if to_start_datetime and to_time_input:
                st.session_state.to_time = to_time_input
                st.session_state.to_date = to_start_datetime
                combined_datetime = pd.to_datetime(
                    f"{to_start_datetime} {to_time_input}"
                )
                # st.write("Combined datetime:", combined_datetime)

                # Define the India time zone
                india_tz = pytz.timezone("Asia/Kolkata")

                # Localize the combined datetime to the India time zone
                localized_datetime = india_tz.localize(combined_datetime)

                # Convert the localized datetime to epoch time
                to_time = int(localized_datetime.timestamp())
                if to_time != st.session_state.to_input_time:
                    st.session_state.to_input_time = to_time
                    st.rerun()
        default_time_range = get_default_time_range()
        # Check if the dates and times are within the tolerance range
        if (
            from_start_datetime == default_time_range[2]
            and is_within_tolerance(from_time_input, default_time_range[3])
        ) and (
            to_start_datetime == default_time_range[0]
            and is_within_tolerance(to_time_input, default_time_range[1])
        ):
            auto_update_time_range(True)
        else:
            auto_update_time_range(False)

        with datetime_cols[2]:
            reset_btn = st.button(
                label="Default", on_click=reset_time_range, use_container_width=True
            )
            if reset_btn:
                auto_update_time_range(True)
                # st.rerun()

        if st.session_state.var_auto_update_time_range:
            update_time_range()

        # ==================== Charts ======================
        interval = st.session_state.to_input_time - st.session_state.from_input_time
        agg_interval = 0
        if interval > 2592000:
            agg_interval = 60
        elif interval > 864000:
            agg_interval = 30
        elif interval > 100080:
            agg_interval = 10
        elif interval <= 100080:
            agg_interval = 0

        VARIABLES = st.session_state.variables
        options: list = []
        user_variables_access = st.session_state.user_variables_access
        if st.session_state.view_role == "user":
            for key, variable in VARIABLES.items():
                variable_name = variable.get("name")
                if variable_name in user_variables_access:
                    options.append(variable_name)
        else:
            for key, variable in VARIABLES.items():
                variable_name = variable.get("name")
                options.append(variable_name)

        # st.write(VARIABLES)
        if not options:
            st.error("No variables available")
            st.stop()
        multislect_cols = st.columns(
            [3.5, 1, 0.5], gap="medium", vertical_alignment="bottom"
        )
        with multislect_cols[0]:
            print(st.session_state.show_charts)
            show_charts = st.multiselect(
                "Show Charts",
                placeholder="Show Charts",
                options=options,
                default=st.session_state.show_charts,
                label_visibility="hidden",
                on_change=change_callback,
            )
            # if  is_options_changed:
            #     if show_charts != st.session_state.show_charts:
            #         st.session_state.show_charts = show_charts
            #     is_options_changed = False
            if st.session_state.show_charts != show_charts:
                st.session_state.show_charts = show_charts
                st.rerun()

        with multislect_cols[1]:
            pass
        with multislect_cols[2]:
            submit = st.button(label="Submit", use_container_width=True)
            if submit:
                st.rerun()

        number_of_graphs_per_row = [1]
        for i in range(
            0, len(st.session_state.show_charts), len(number_of_graphs_per_row)
        ):
            graph_cols = st.columns(number_of_graphs_per_row, gap="small")
            for j, chart in enumerate(
                st.session_state.show_charts[i : i + len(number_of_graphs_per_row)]
            ):
                with graph_cols[j]:
                    VARIABLE_KEY = get_variable_key_by_name(VARIABLES, chart)
                    if VARIABLE_KEY is not None:
                        VARIABLE = VARIABLES.get(VARIABLE_KEY)
                        # data=pd.DataFrame()
                        aggregate_or_value = "value"
                        if interval <= 100080:
                            data = node_client.get_data(
                                variable_identifier=VARIABLE.get("identifier"),
                                from_time=st.session_state.from_input_time,
                                to_time=st.session_state.to_input_time,
                            )
                            aggregate_or_value = "value"
                        else:
                            data = node_client.get_aggData(
                                variable_identifier=VARIABLE.get("identifier"),
                                from_time=st.session_state.from_input_time,
                                to_time=st.session_state.to_input_time,
                                agg_interval_mins=agg_interval,
                            )
                            aggregate_or_value = "aggregate"
                        minData = 0
                        maxData = 0
                        if not data.empty:
                            minData = data[aggregate_or_value].min()
                            maxData = data[aggregate_or_value].max()

                        sub_graph_sec = st.columns([1, 1], gap="small")
                        with sub_graph_sec[0]:
                            draw_chart(
                                chart_title=chart,
                                chart_data=data,
                                y_axis_title=VARIABLE.get("unit"),
                                bottomRange=(minData - (minData * 0.2)),
                                topRange=(maxData + (maxData * 0.2)),
                                agg=agg_interval,
                                aggregate_or_value=aggregate_or_value,
                            )
                        with sub_graph_sec[1]:

                            st.dataframe(data, use_container_width=True)
                    else:
                        st.subheader(chart)
                        st.error("Variable not found")


def change_callback():
    global is_options_changed
    is_options_changed = True


def map_section(node_client=None):
    container = st.container(border=True)
    currentTime = int(time.time())  # to means recent time
    pastHour_Time = int(currentTime - 86400)
    with container:
        st.subheader(body="Device Location", anchor=False)
        res = node_client.get_map_data("location", pastHour_Time, currentTime)
        if not res.empty:
            # st.write(res)
            last_updated_time = res.iloc[0]["Datetime"]
            st.markdown(f"**Last Updated:**  {last_updated_time}")
            st.map(
                res,
                zoom=13,
                # latitude="lat",
                # longitude="long",
                color="#0044ff",
                size=50,
                use_container_width=True,
            )
        else:
            res = node_client.get_latestData("location")
            if res.get("data") is not None:
                location = res.get("data")
                last_updated = res.get("timestamp")
                indian_time_zone = pytz.timezone("Asia/Kolkata")  # set time zone
                hr_timestamp = datetime.fromtimestamp(last_updated, indian_time_zone)
                fm_hr_timestamp = hr_timestamp.strftime("%Y-%m-%d %H:%M:%S %Z")
                st.markdown(f"**Last Updated:**  {fm_hr_timestamp}")

                latitude = location.get("lat")
                longitude = location.get("long")
                locationData = pd.DataFrame(
                    {"latitude": [latitude], "longitude": [longitude]}
                )
                st.map(
                    locationData,
                    zoom=13,
                    color="#0044ff",
                    size=50,
                    use_container_width=True,
                )
            else:
                st.error("No Data Available")


def get_variable_key_by_name(data, search_name):
    for key, variable in data.items():
        if variable["name"] == search_name:
            return key
    return None

import json
import streamlit as st
import pandas as pd
import pytz
import time
from datetime import datetime


class Anedya:
    def __init__(self) -> None:
        pass

    def new_client(self, API_KEY):
        return NewClient(API_KEY)

    def new_node(self, new_client, nodeId: str):
        return NewNode(new_client, nodeId)


class NewClient:
    def __init__(self, API_KEY) -> None:
        if API_KEY == "":
            st.error("Please config a valid NODE ID and API key.")

        elif API_KEY == "":
            st.error("Please config a valid API key.")
        else:
            self.API_KEY = API_KEY


class NewNode:
    def __init__(self, new_client: NewClient, nodeId: str) -> None:
        self.nodeId = nodeId
        self.API_KEY = new_client.API_KEY

    def get_deviceStatus(self) -> dict:
        return anedya_getDeviceStatus(self.API_KEY, self.nodeId)

    def get_latestData(self, variable_identifier: str) -> dict:
        return get_latestData(variable_identifier, self.nodeId, self.API_KEY)

    def get_data(
        self, variable_identifier: str, from_time: int, to_time: int
    ) -> pd.DataFrame:
        return get_data(
            variable_identifier, self.nodeId, from_time, to_time, self.API_KEY
        )

    def get_map_data(
        self, variable_identifier: str, from_time: int, to_time: int
    ) -> pd.DataFrame:
        return get_map_data(
            variable_identifier, self.nodeId, from_time, to_time, self.API_KEY
        )

    def get_aggData(
        self,
        variable_identifier: str,
        from_time: int,
        to_time: int,
        agg_interval_mins: int = 10,
    ) -> pd.DataFrame:
        return anedya_getAggData(
            variable_identifier,
            self.nodeId,
            from_time,
            to_time,
            self.API_KEY,
            agg_interval_mins,
        )

    def get_valueStore(self, key: str = "", scope: str = "node", id: str = "") -> dict:
        return anedya_getValueStore(self.API_KEY, self.nodeId, scope, id, key)

    def set_valueStore(
        self,
        key: str = "",
        value: str = "",
        type: str = "",
        scope: str = "node",
        id: str = "",
    ) -> dict:
        return anedya_setValueStore(
            self.API_KEY, self.nodeId, scope, id, key, value, type
        )
    def send_command(self, command: str, data: str = "") -> dict:
        return anedya_sendCommand(self.API_KEY, self.nodeId, command, data)


@st.cache_data(ttl=40, show_spinner=False)
def anedya_getDeviceStatus(apiKey, nodeId) -> dict:
    url = "https://api.anedya.io/v1/health/status"
    apiKey_in_formate = "Bearer " + apiKey

    payload = json.dumps({"nodes": [nodeId], "lastContactThreshold": 60})
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": apiKey_in_formate,
    }

    response = st.session_state.http_client.request(
        "POST", url, headers=headers, data=payload, timeout=10
    )
    responseMessage = response.text

    errorCode = json.loads(responseMessage).get("errcode")
    if errorCode == 0:
        device_status = json.loads(responseMessage).get("data")[nodeId].get("online")
        value = {
            "isSuccess": True,
            "device_status": device_status,
        }
    else:
        print(responseMessage)
        # st.write("No previous value!!")
        value = {"isSuccess": False, "device_status": None}

    return value


@st.cache_data(ttl=5, show_spinner=False)
def get_latestData(param_variable_identifier: str, nodeId: str, apiKey: str) -> dict:

    url = "https://api.anedya.io/v1/data/latest"
    apiKey_in_formate = "Bearer " + apiKey

    payload = json.dumps({"nodes": [nodeId], "variable": param_variable_identifier})
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": apiKey_in_formate,
    }

    response = st.session_state.http_client.request(
        "POST", url, headers=headers, data=payload, timeout=10
    )
    # response=request("POST", url, headers=headers, data=payload)
    response_message = response.text
    if response.status_code == 200:
        # print(response_message)
        data = json.loads(response_message).get("data")
        if data == {} or data == None:
            print("No Data found")
            # st.toast("No Data found")
            return {"isSuccess": True, "data": None, "timestamp": None}
        else:
            data = data[nodeId].get("value")
            timestamp = (
                json.loads(response_message).get("data")[nodeId].get("timestamp")
            )
            # print(data, timestamp)
            return {"isSuccess": True, "data": data, "timestamp": timestamp}
    else:
        st.error(f"Error: {response_message}")
        return {"isSuccess": False, "data": None, "timestamp": None}


@st.cache_data(ttl=30, show_spinner=False)
def get_data(
    variable_identifier: str,
    nodeId: str,
    from_time: int,
    to_time: int,
    apiKey: str,
) -> pd.DataFrame:

    url = "https://api.anedya.io/v1/data/getData"
    apiKey_in_formate = "Bearer " + apiKey

    payload = json.dumps(
        {
            "variable": variable_identifier,
            "nodes": [nodeId],
            "from": from_time,
            "to": to_time,
            "limit": 10000,
            "order": "desc",
        }
    )
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": apiKey_in_formate,
    }

    response = st.session_state.http_client.request(
        "POST", url, headers=headers, data=payload, timeout=10
    )
    response_message = response.text
    # st.write(response_message)

    if response.status_code == 200:
        data_list = []

        # Parse JSON string
        response_data = json.loads(response_message).get("data")
        for timeStamp, value in response_data.items():
            for entry in value:
                data_list.append(entry)

        if data_list:
            # st.session_state.CurrentTemperature = round(data_list[0]["aggregate"], 2)
            df = pd.DataFrame(data_list)

            if df.duplicated(subset=["timestamp"]).any():
                pass
                # st.warning("Found duplicate datapoints.")

            # Remove similar data points
            df.drop_duplicates(subset=["timestamp"], keep="first", inplace=True)
            df["Datetime"] = pd.to_datetime(df["timestamp"], unit="s")
            local_tz = pytz.timezone("Asia/Kolkata")  # Change to your local time zone
            df["Datetime"] = (
                df["Datetime"].dt.tz_localize("UTC").dt.tz_convert(local_tz)
            )
            df["Datetime"] = df["Datetime"].dt.strftime("%Y-%m-%d %H:%M:%S")
            df.set_index("Datetime", inplace=True)

            # Droped the original 'timestamp' column as it's no longer needed
            df.drop(columns=["timestamp"], inplace=True)
            # print(df.head())
            # Reset the index to prepare for Altair chart
            chart_data = df.reset_index()
        else:
            chart_data = pd.DataFrame()
        return chart_data
    else:
        # st.write(response_message)
        print(response_message[0])
        value = pd.DataFrame()
        return value


@st.cache_data(ttl=30, show_spinner=False)
def get_map_data(
    variable_identifier: str,
    nodeId: str,
    from_time: int,
    to_time: int,
    apiKey: str,
) -> pd.DataFrame:

    url = "https://api.anedya.io/v1/data/getData"
    apiKey_in_formate = "Bearer " + apiKey

    payload = json.dumps(
        {
            "variable": variable_identifier,
            "nodes": [nodeId],
            "from": from_time,
            "to": to_time,
            "limit": 100,
            "order": "desc",
        }
    )
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": apiKey_in_formate,
    }

    # print(payload)
    response = st.session_state.http_client.request(
        "POST", url, headers=headers, data=payload, timeout=10
    )
    response_message = response.text
    # st.write(response_message)

    if response.status_code == 200:
        data_list = []

        # Parse JSON string
        response_data = json.loads(response_message).get("data")
        for timeStamp, value in response_data.items():
            for entry in value:
                data_list.append(
                    {
                        "timestamp": entry["timestamp"],
                        "latitude": entry["value"]["lat"],
                        "longitude": entry["value"]["long"],
                    }
                )

        if data_list:
            # st.session_state.CurrentTemperature = round(data_list[0]["aggregate"], 2)
            df = pd.DataFrame(data_list)

            if df.duplicated(subset=["timestamp"]).any():
                pass
                # st.warning("Found duplicate datapoints.")
            # print(df)

            # Remove similar data points
            df.drop_duplicates(subset=["timestamp"], keep="first", inplace=True)
            df["Datetime"] = pd.to_datetime(df["timestamp"], unit="s")
            local_tz = pytz.timezone("Asia/Kolkata")  # Change to your local time zone
            df["Datetime"] = (
                df["Datetime"].dt.tz_localize("UTC").dt.tz_convert(local_tz)
            )
            df["Datetime"] = df["Datetime"].dt.strftime("%Y-%m-%d %H:%M:%S")
            df.set_index("Datetime", inplace=True)

            # Droped the original 'timestamp' column as it's no longer needed
            df.drop(columns=["timestamp"], inplace=True)
            # print(df.head())
            # Reset the index to prepare for Altair chart
            chart_data = df.reset_index()
        else:
            chart_data = pd.DataFrame()
        return chart_data
    else:
        # st.write(response_message)
        print(response_message[0])
        value = pd.DataFrame()
        return value


@st.cache_data(ttl=30, show_spinner=False)
def anedya_getAggData(
    variable_identifier: str,
    nodeId: str,
    from_time: int,
    to_time: int,
    apiKey: str,
    agg_interval_mins: int,
) -> pd.DataFrame:
    url = "https://api.anedya.io/v1/aggregates/variable/byTime"
    apiKey_in_formate = "Bearer " + apiKey

    payload = json.dumps(
        {
            "variable": variable_identifier,
            "from": from_time,
            "to": to_time,
            "config": {
                "aggregation": {"compute": "avg", "forEachNode": True},
                "interval": {
                    "measure": "minute",
                    "interval": agg_interval_mins,
                },
                "responseOptions": {"timezone": "UTC"},
                "filter": {"nodes": [nodeId], "type": "include"},
            },
        }
    )
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": apiKey_in_formate,
    }

    response = st.session_state.http_client.request(
        "POST", url, headers=headers, data=payload
    )
    response_message = response.text

    if response.status_code == 200:
        data_list = []

        # Parse JSON string
        response_data = json.loads(response_message).get("data")
        for timeStamp, aggregate in response_data.items():
            for entry in aggregate:
                data_list.append(entry)

        if data_list:
            # st.session_state.CurrentTemperature = round(data_list[0]["aggregate"], 2)
            df = pd.DataFrame(data_list)

            if df.duplicated(subset=["timestamp"]).any():
                pass
                # st.warning("Found duplicate datapoints.")
                # Remove similar data points
                df.drop_duplicates(subset=["timestamp"], keep="first", inplace=True)

            df["Datetime"] = pd.to_datetime(df["timestamp"], unit="s")
            local_tz = pytz.timezone("Asia/Kolkata")  # Change to your local time zone
            df["Datetime"] = (
                df["Datetime"].dt.tz_localize("UTC").dt.tz_convert(local_tz)
            )
            # Strip timezone info
            df["Datetime"] = df["Datetime"].dt.strftime("%Y-%m-%d %H:%M:%S")
            df.set_index("Datetime", inplace=True)

            # Droped the original 'timestamp' column as it's no longer needed
            df.drop(columns=["timestamp"], inplace=True)
            # print(df.head())
            # Reset the index to prepare for Altair chart
            chart_data = df.reset_index()
        else:
            chart_data = pd.DataFrame()
        return chart_data
    else:
        # st.write(response_message)
        print(response_message[0])
        value = pd.DataFrame()
        return value


@st.cache_data(ttl=1, show_spinner=False)
def anedya_getValueStore(
    apiKey,
    nodeId,
    scope: str,
    id: str,
    key: str,
) -> dict:
    url = "https://api.anedya.io/v1/valuestore/getValue"

    if scope != "global":
        id = nodeId

    payload = json.dumps({"namespace": {"scope": scope, "id": id}, "key": key})
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {apiKey}",
    }

    response = st.session_state.http_client.request(
        "POST", url, headers=headers, data=payload
    )
    responseMessage = response.text

    isSucess = json.loads(responseMessage).get("success")
    if isSucess:
        value = json.loads(responseMessage).get("value")
        value = {
            "isSuccess": True,
            "key": key,
            "value": value,
        }
    else:
        print(responseMessage)
        # st.write("No previous value!!")
        value = {
            "isSuccess": False,
            "key": key,
            "value": None,
            "error": responseMessage,
        }

    return value


def anedya_setValueStore(
    apiKey, nodeId, scope: str, id: str, key: str, value, type: str
) -> dict:
    url = "https://api.anedya.io/v1/valuestore/setValue"

    if scope != "global":
        id = nodeId
    if type == "":
        if isinstance(value, str):
            type = "string"
        elif isinstance(value, (bytes, bytearray)):
            type = "binary"
        elif isinstance(value, float):
            type = "float"
        elif isinstance(value, bool):
            type = "boolean"
        else:
            type = "string"
            value = str(value)
    payload = json.dumps(
        {
            "namespace": {"scope": scope, "id": id},
            "key": key,
            "value": value,
            "type": type,
        }
    )
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {apiKey}",
    }

    response = st.session_state.http_client.request(
        "POST", url, headers=headers, data=payload
    )
    responseMessage = response.text
    # print(responseMessage)

    isSucess = json.loads(responseMessage).get("success")
    if isSucess:
        value = json.loads(responseMessage).get("value")
        value = {
            "isSuccess": True,
        }
        print("Value Updated")
    else:
        print(responseMessage)
        # st.write("No previous value!!")
        value = {"isSuccess": False, "res": responseMessage}

    return value


def anedya_sendCommand(
    apiKey, nodeId, command: str, data: str = ""
) -> dict:
    url = "https://api.anedya.io/v1/commands/send"
    expiry = int(time.time()) + (60 * 60 * 24 * 5)  # 5 days expiry
    expiry = int(expiry * 1000)  # Convert to milliseconds

    payload = json.dumps(
        {
            "nodeid": nodeId,
            "command": command,
            "data": data,
            "type": "string",
            "expiry": expiry,
        }
    )
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {apiKey}",
    }

    response = st.session_state.http_client.request(
        "POST", url, headers=headers, data=payload
    )
    responseMessage = response.text
    print(responseMessage)

    isSucess = json.loads(responseMessage).get("success")
    commandId= json.loads(responseMessage).get("commandId")
    if isSucess:
        value = json.loads(responseMessage).get("value")
        value = {
            "isSuccess": True,
            "commandId": commandId,
        }
        print("Command Sent")
    else:
        print(responseMessage)
        # st.write("No previous value!!")
        value = {"isSuccess": False, "res": responseMessage}

    return value

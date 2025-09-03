import streamlit as st


def draw_custom_tile(Name, value, bg_color="White", color="Black"):

    st.markdown(
        f"""
                <div style="
                    width: 100%;
                    height: 105px;
                    border: 1px solid #d3d3d3;
                    border-radius: 12px;
                    padding: 12px 16px;
                    box-shadow: 1px 1px 5px rgba(0,0,0,0.05);
                    background-color: {bg_color};
                    color: Black;
                    margin-bottom: 20px;
                ">
                    <p style="margin: 0px; font-size: 14px; color: Black;">{Name}</p>
                    <p style="margin: 4px 0 0 0; padding-top: 10px; text-align: right; font-size: 28px; font-weight: 500;">{value}</p>
                </div>
                """,
        unsafe_allow_html=True,
    )

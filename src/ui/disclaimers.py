import streamlit as st


def top_disclaimer():
    st.markdown(
        """
        <div class="gaia-warning">
        <b>General-interest demonstrator only.</b> This dashboard is a public-data visualisation prepared by GAIA Marine. 
        It is not an official forecast, warning, emergency advice product, marine safety tool, or operational decision-support system.
        For official warnings, forecasts and emergency information, refer directly to the Bureau of Meteorology, Emergency WA, local authorities and relevant marine safety agencies.
        </div>
        """,
        unsafe_allow_html=True,
    )


def footer_disclaimer():
    st.markdown("---")
    st.markdown(
        """
        **Data sources and limitations**  
        This demonstrator uses selected publicly available weather, coastal and metocean information where available, plus synthetic demonstration data when no uploaded source data is provided. Source data remains subject to the relevant agency terms, copyright, disclaimers and conditions of use.  

        GAIA Marine has processed and visualised the information independently for general interest and capability demonstration. GAIA Marine does not warrant the completeness, accuracy, timeliness or fitness for purpose of this dashboard and accepts no liability for decisions made using it.
        """
    )

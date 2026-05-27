import streamlit as st


def top_disclaimer():
    st.markdown(
        """
        <div class="gaia-warning">
        <b>General-interest demonstrator only.</b> GAIA Marine Storm Watch is an educational storm-event visualisation prepared by GAIA Marine for public interest and brand awareness. It shows how public weather, coastal and metocean information can be brought together into a clear event story before, during and after a storm. It is not an official forecast, warning, emergency advice product, marine safety tool, operational decision-support system, or commercial decision-making product.
        <br><br>
        For official warnings, forecasts and emergency information, refer directly to the Bureau of Meteorology, Emergency WA, local authorities and relevant marine safety agencies.
        </div>
        """,
        unsafe_allow_html=True,
    )


def footer_disclaimer():
    st.markdown("---")
    st.markdown(
        """
        <div class="gaia-legal">
        <b>Data sources, copyright and limitations.</b><br>
        This demonstrator uses selected publicly available weather, coastal and metocean information where available, plus synthetic or curated demonstration data where checked source feeds are not connected. Source information remains subject to the relevant agency terms, copyright, disclaimers, licensing and conditions of use. Bureau of Meteorology, Emergency WA and WA Department of Transport and Major Infrastructure information should be read at the official source for authoritative context.<br><br>
        GAIA Marine does not copy, download, archive or rehost third-party camera image files, radar images, satellite images or weather-map graphics in this public prototype. Official camera, radar, satellite and weather-map references are linked or previewed from source where technically possible. Source pages may show their own issue, validity or observation timestamps, which should be used when comparing visual references against the dashboard timeline.<br><br>
        GAIA Marine has processed and visualised the displayed information independently for general interest and capability demonstration. The dashboard is not for emergency response, marine navigation, water-user safety, operational planning, infrastructure protection, commercial reliance or any other decision-making purpose. GAIA Marine does not warrant the completeness, accuracy, timeliness, availability or fitness for purpose of this dashboard and accepts no liability for decisions made using it.<br><br>
        <b>Contact:</b> solutions@gaia-marine.ai · <b>Website:</b> https://gaia-marine.com.au
        </div>
        """,
        unsafe_allow_html=True,
    )

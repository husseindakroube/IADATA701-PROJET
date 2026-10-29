import streamlit as st

st.html("""
<section class="conteneur-video-principal">

    <video
        class="video-arriere-plan"
        autoplay
        muted
        loop
        playsinline
        preload="metadata"
        aria-hidden="true"
    >
        <source
            src="/app/static/sncf.mp4"
            type="video/mp4"
        >
    </video>

</section>
""")


import streamlit as st

st.html("""
<section class="hero-video">

    <!-- Background video -->
    <video
        class="hero-video-media"
        autoplay
        muted
        loop
        playsinline
        preload="metadata"
        aria-hidden="true"
    >
        <source
            src="/app/static/Le groupe SNCF en bref.mp4"
            type="video/mp4"
        >
    </video>

    <!-- Background overlay -->
    <div class="hero-video-overlay"></div>

    <!-- Text content -->
    <div class="hero-video-content">

        <p class="hero-video-label">
            LE RAIL À TRAVERS LES DONNÉES
        </p>

        <h1 class="hero-video-title">
            TGVision
        </h1>

        <h2 class="hero-video-slogan">
            Au-delà des horaires,<br>
            la réalité des voyages.
        </h2>

        <p class="hero-video-description">
            La ponctualité ferroviaire
            sous un nouvel angle.
        </p>

    </div>

</section>
""")

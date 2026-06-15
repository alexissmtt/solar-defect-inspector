"""Streamlit frontend.

This is now a thin client: it does no inference and talks to no model. It calls
the inspection API over HTTP, which keeps the UI and the model lifecycle fully
decoupled. Point it at a running API with INSPECTOR_API_URL.
"""

from __future__ import annotations

import os

import httpx
import streamlit as st

API_URL = os.environ.get("INSPECTOR_API_URL", "http://localhost:8000")

st.set_page_config(page_title="Solar Inspector", page_icon=None)
st.title("Solar Inspector")
st.caption(f"Connected to API at {API_URL}")

tab_inspect, tab_history = st.tabs(["Inspect", "History"])

with tab_inspect:
    uploaded = st.file_uploader("Upload a panel image", type=["jpg", "jpeg", "png"])
    if uploaded is not None:
        st.image(uploaded, caption="Uploaded image", use_container_width=True)
        if st.button("Run inspection"):
            with st.spinner("Inspecting..."):
                files = {"file": (uploaded.name, uploaded.getvalue(), uploaded.type)}
                try:
                    resp = httpx.post(f"{API_URL}/inspect", files=files, timeout=60)
                    resp.raise_for_status()
                except httpx.HTTPError as exc:
                    st.error(f"API error: {exc}")
                else:
                    result = resp.json()
                    if result["is_defect"]:
                        st.error(
                            f"Defect: **{result['label']}** "
                            f"({result['confidence']:.1f}% confidence)"
                        )
                        st.subheader("Maintenance report")
                        st.write(result["report"])
                    else:
                        st.success(
                            f"No defect detected ({result['confidence']:.1f}% confidence)"
                        )

with tab_history:
    if st.button("Refresh history"):
        st.rerun()
    try:
        resp = httpx.get(f"{API_URL}/inspections", params={"limit": 25}, timeout=30)
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        st.error(f"API error: {exc}")
    else:
        rows = resp.json()
        if not rows:
            st.info("No inspections yet.")
        else:
            st.dataframe(
                [
                    {
                        "id": r["id"],
                        "time": r["created_at"],
                        "label": r["label"],
                        "confidence": round(r["confidence"], 1),
                        "defect": r["is_defect"],
                        "source": r["source"],
                    }
                    for r in rows
                ],
                use_container_width=True,
            )

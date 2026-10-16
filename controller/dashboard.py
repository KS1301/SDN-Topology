from pathlib import Path
import time
import pandas as pd
import streamlit as st
import plotly.express as px

BASE = Path(__file__).resolve().parent
RESULTS = BASE / "results"

st.set_page_config(page_title="SDN Live Monitor", layout="wide")
st.title("SDN Network — Live Monitoring Dashboard")
st.caption("Refreshes the CSV-backed charts automatically. Keep the Ryu controller and resource monitor running to collect new samples.")

def read_csv_safe(path):
    try:
        if path.exists() and path.stat().st_size > 0:
            return pd.read_csv(path)
    except Exception:
        pass
    return pd.DataFrame()

def newest_resource_file():
    files = sorted(RESULTS.glob("resource_usage_*.csv"), key=lambda x: x.stat().st_mtime, reverse=True)
    return files[0] if files else None

@st.fragment(run_every=2)
def live_view():
    resource_file = newest_resource_file()
    resources = read_csv_safe(resource_file) if resource_file else pd.DataFrame()
    switches = read_csv_safe(RESULTS / "switch_stats.csv")

    if not resources.empty and "timestamp" in resources.columns:
        resources["time"] = pd.to_datetime(resources["timestamp"], unit="s", errors="coerce")
        for col in ["cpu_percent", "memory_percent", "memory_used_mb"]:
            if col in resources:
                resources[col] = pd.to_numeric(resources[col], errors="coerce")
    if not switches.empty and "timestamp" in switches.columns:
        switches["time"] = pd.to_datetime(switches["timestamp"], unit="s", errors="coerce")
        for col in ["switch_dpid", "flow_count", "total_packets", "total_bytes"]:
            if col in switches:
                switches[col] = pd.to_numeric(switches[col], errors="coerce")

    a, b, c = st.columns(3)
    a.metric("Resource log", resource_file.name if resource_file else "Not found")
    b.metric("Switch-stat rows", str(len(switches)))
    c.metric("Last refresh", time.strftime("%H:%M:%S"))

    if not resources.empty:
        if "cpu_percent" in resources:
            st.subheader("CPU usage (%)")
            st.plotly_chart(px.line(resources, x="time", y="cpu_percent", title="CPU usage over time"), use_container_width=True, key="cpu_chart")
        if "memory_percent" in resources:
            st.subheader("RAM usage (%)")
            st.plotly_chart(px.line(resources, x="time", y="memory_percent", title="RAM usage over time"), use_container_width=True, key="ram_chart")
        if "memory_used_mb" in resources:
            st.plotly_chart(px.line(resources, x="time", y="memory_used_mb", title="Memory used (MB)"), use_container_width=True, key="mem_mb_chart")
    else:
        st.warning("No resource CSV found yet. Start `python monitor_resources.py` in another terminal.")

    if not switches.empty and {"time", "switch_dpid"}.issubset(switches.columns):
        st.subheader("Ryu/OpenFlow switch statistics")
        if "total_packets" in switches:
            st.plotly_chart(px.line(switches, x="time", y="total_packets", color="switch_dpid",
                                    markers=True, title="Observed flow packets by switch (cumulative flow-stat snapshot)"),
                            use_container_width=True, key="packets_chart")
        if "total_bytes" in switches:
            st.plotly_chart(px.line(switches, x="time", y="total_bytes", color="switch_dpid",
                                    markers=True, title="Observed flow bytes by switch (cumulative flow-stat snapshot)"),
                            use_container_width=True, key="bytes_chart")
        if "flow_count" in switches:
            st.plotly_chart(px.line(switches, x="time", y="flow_count", color="switch_dpid",
                                    markers=True, title="Active flow count reported by Ryu"),
                            use_container_width=True, key="flows_chart")
        st.caption("These graphs use the controller's flow-stat CSV. Byte/packet values can fall when flows expire or counters reset; they are not guaranteed to be physical-port throughput.")
        st.dataframe(switches.tail(10), use_container_width=True)
    else:
        st.warning("No usable results/switch_stats.csv rows found yet. Check that Ryu is running and writing switch statistics.")

    st.markdown("### Packet loss and latency")
    st.info("The current CSV files do not record ping loss/latency. To graph those, run a separate ping-probe logger; the current switch counters alone cannot calculate end-to-end packet loss.")

live_view()

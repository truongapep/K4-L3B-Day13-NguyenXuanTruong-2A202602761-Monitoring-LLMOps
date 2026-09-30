from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st
import yaml

ROOT = Path(__file__).resolve().parent.parent
LOG_PATH = ROOT / "data" / "logs.jsonl"
CONFIG_PATH = ROOT / "config" / "dashboard.yaml"
COLUMNS = [
    "ts", "event", "latency_ms", "ttft_ms", "cost_usd", "tokens_in",
    "tokens_out", "quality_score", "tool_success", "error_type",
]

st.set_page_config(page_title="Day 13 Monitoring", layout="wide")


def load_contract() -> dict:
    cfg = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))["dashboard"]
    thresholds = {p["id"]: p["threshold"]["value"] for p in cfg["panels"]}
    return {
        "range": cfg["time_range_minutes"],
        "refresh": cfg["refresh_seconds"],
        "thresholds": thresholds,
    }


def load_logs(window_minutes: int) -> pd.DataFrame:
    rows = []
    if LOG_PATH.exists():
        for line in LOG_PATH.read_text(encoding="utf-8").splitlines():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    df = pd.DataFrame(rows).reindex(columns=COLUMNS)
    if df.empty:
        return df
    df["ts"] = pd.to_datetime(df["ts"], utc=True, errors="coerce")
    df = df.dropna(subset=["ts"])
    cutoff = pd.Timestamp.now(tz="UTC") - pd.Timedelta(minutes=window_minutes)
    return df[df["ts"] >= cutoff]


def per_minute(df: pd.DataFrame, col: str, how: str) -> pd.Series:
    series = df.set_index("ts")[col].astype(float)
    return getattr(series.resample("1min"), how)()


contract = load_contract()
TH = contract["thresholds"]
window = st.sidebar.number_input("Time range (phút)", 5, 1440, contract["range"])
st.sidebar.caption(f"Refresh mỗi {contract['refresh']}s. Nguồn: data/logs.jsonl")


@st.fragment(run_every=contract["refresh"])
def render() -> None:
    df = load_logs(window)
    st.title("K4-L3B Day 13 Monitoring & LLMOps")
    st.caption(f"Time range: {window} phút gần nhất (UTC)")
    if df.empty:
        st.warning("Chưa có log trong time range. Chạy load_test.py rồi tải lại.")
        return

    sent = df[df["event"] == "response_sent"]
    received = df[df["event"] == "request_received"]
    failed = df[df["event"] == "request_failed"]

    # 1. Latency
    st.subheader("1. Latency percentiles và TTFT (ms)")
    if not sent.empty:
        p50, p95, p99 = (sent["latency_ms"].quantile(q) for q in (0.5, 0.95, 0.99))
        ttft95 = sent["ttft_ms"].quantile(0.95)
        c = st.columns(4)
        c[0].metric("P50", f"{p50:.0f} ms")
        c[1].metric("P95", f"{p95:.0f} ms", f"SLO ≤ {TH['latency']} ms", delta_color="off")
        c[2].metric("P99", f"{p99:.0f} ms")
        c[3].metric("TTFT P95", f"{ttft95:.0f} ms")
        chart = pd.DataFrame({
            "P50": per_minute(sent, "latency_ms", "median"),
            "P95": sent.set_index("ts")["latency_ms"].resample("1min").quantile(0.95),
            "P99": sent.set_index("ts")["latency_ms"].resample("1min").quantile(0.99),
            "TTFT P95": sent.set_index("ts")["ttft_ms"].resample("1min").quantile(0.95),
        })
        chart["Threshold P95"] = TH["latency"]
        st.line_chart(chart)

    # 2. Traffic
    st.subheader("2. Request traffic (requests/phút)")
    if not received.empty:
        traffic = received.set_index("ts")["event"].resample("1min").count()
        st.metric("Tổng request", len(received), f"Ngưỡng ≥ {TH['traffic']}/phút", delta_color="off")
        st.line_chart(pd.DataFrame({"requests/min": traffic, "Threshold": TH["traffic"]}))

    # 3. Errors + retrieval success
    st.subheader("3. Error rate và retrieval success (%)")
    total_req = len(received)
    err_rate = len(failed) / total_req * 100 if total_req else 0.0
    tool_rows = df["tool_success"].dropna()
    retrieval = (tool_rows.astype(bool).sum() / len(tool_rows) * 100) if len(tool_rows) else 100.0
    c = st.columns(3)
    c[0].metric("Error rate", f"{err_rate:.2f} %", f"SLO ≤ {TH['errors']} %", delta_color="off")
    c[1].metric("Retrieval success", f"{retrieval:.1f} %", "Guardrail ≥ 90 %", delta_color="off")
    c[2].metric("request_failed", len(failed))
    if not failed.empty:
        st.bar_chart(failed["error_type"].fillna("unknown").value_counts())

    # 4. Cost
    st.subheader("4. Cost over time (USD)")
    if not sent.empty:
        st.metric("Tổng cost", f"${sent['cost_usd'].sum():.4f}", f"Ngưỡng ≤ ${TH['cost']}", delta_color="off")
        cost = pd.DataFrame({"cost/min": per_minute(sent, "cost_usd", "sum")})
        st.line_chart(cost)

    # 5. Tokens
    st.subheader("5. Input và output tokens")
    if not sent.empty:
        c = st.columns(2)
        c[0].metric("Tokens in", int(sent["tokens_in"].sum()))
        c[1].metric("Tokens out", int(sent["tokens_out"].sum()), f"Ngưỡng ≤ {TH['tokens']}", delta_color="off")
        st.line_chart(pd.DataFrame({
            "tokens_in": per_minute(sent, "tokens_in", "sum"),
            "tokens_out": per_minute(sent, "tokens_out", "sum"),
        }))

    # 6. Quality
    st.subheader("6. Quality proxy (0-1)")
    if not sent.empty:
        q = sent["quality_score"].astype(float)
        st.metric("Mean quality", f"{q.mean():.2f}", f"SLO ≥ {TH['quality']}", delta_color="off")
        qc = pd.DataFrame({"quality": per_minute(sent, "quality_score", "mean")})
        qc["Threshold"] = TH["quality"]
        st.line_chart(qc)


render()

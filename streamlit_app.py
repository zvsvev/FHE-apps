from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Any

import numpy as np
import pandas as pd
import streamlit as st


OP_ADD = "x + y"
OP_MUL = "x * y"
OP_LINEAR = "(x * weight) + y"
TOLERANCE = 1e-9


@dataclass(frozen=True)
class PlaintextPayload:
    x: float
    y: float
    weight: float


@dataclass(frozen=True)
class MockCiphertext:
    values: dict[str, float]
    scheme_label: str
    slot_count: int
    estimated_size_bytes: int
    operation_history: list[str]


@dataclass(frozen=True)
class PipelineResult:
    plaintext_result: float
    fhe_result: float
    is_valid: bool
    difference: float
    metrics: dict[str, float]
    input_ciphertext: MockCiphertext
    output_ciphertext: MockCiphertext


def format_number(value: float) -> str:
    if abs(value - round(value)) < TOLERANCE:
        return f"{value:,.0f}"
    return f"{value:,.6f}".rstrip("0").rstrip(".")


def elapsed_ms(start_time: float) -> float:
    return (perf_counter() - start_time) * 1000


def estimate_ciphertext_size(slot_count: int, history_length: int) -> int:
    base_size = 4096
    slot_overhead = slot_count * 1024
    history_overhead = history_length * 768
    return base_size + slot_overhead + history_overhead


def represent_data(payload: PlaintextPayload) -> dict[str, float]:
    values = {
        "x": float(np.asarray(payload.x)),
        "y": float(np.asarray(payload.y)),
        "weight": float(np.asarray(payload.weight)),
    }
    return values


def encrypt(represented_data: dict[str, float]) -> MockCiphertext:
    history = ["represent_data", "encrypt"]
    return MockCiphertext(
        values=represented_data,
        scheme_label="Mock-FHE / CKKS-style numeric slots",
        slot_count=len(represented_data),
        estimated_size_bytes=estimate_ciphertext_size(len(represented_data), len(history)),
        operation_history=history,
    )


def evaluate_plaintext(payload: PlaintextPayload, operation: str) -> float:
    if operation == OP_ADD:
        return payload.x + payload.y
    if operation == OP_MUL:
        return payload.x * payload.y
    if operation == OP_LINEAR:
        return (payload.x * payload.weight) + payload.y
    raise ValueError(f"Unsupported operation: {operation}")


def evaluate_fhe(ciphertext: MockCiphertext, operation: str, weight: float) -> MockCiphertext:
    x_value = ciphertext.values["x"]
    y_value = ciphertext.values["y"]

    if operation == OP_ADD:
        result = x_value + y_value
        history_label = "homomorphic_add(x, y)"
    elif operation == OP_MUL:
        result = x_value * y_value
        history_label = "homomorphic_multiply(x, y)"
    elif operation == OP_LINEAR:
        result = (x_value * weight) + y_value
        history_label = "homomorphic_linear((x * weight) + y)"
    else:
        raise ValueError(f"Unsupported operation: {operation}")

    history = [*ciphertext.operation_history, history_label]
    return MockCiphertext(
        values={"result": result},
        scheme_label=ciphertext.scheme_label,
        slot_count=1,
        estimated_size_bytes=estimate_ciphertext_size(1, len(history)),
        operation_history=history,
    )


def decrypt(ciphertext_result: MockCiphertext) -> float:
    return ciphertext_result.values["result"]


def validate_result(plaintext_result: float, fhe_result: float) -> tuple[bool, float]:
    difference = abs(plaintext_result - fhe_result)
    return difference <= TOLERANCE, difference


def run_pipeline(payload: PlaintextPayload, operation: str) -> PipelineResult:
    total_start = perf_counter()

    step_start = perf_counter()
    represented_data = represent_data(payload)
    representation_ms = elapsed_ms(step_start)

    step_start = perf_counter()
    input_ciphertext = encrypt(represented_data)
    encryption_ms = elapsed_ms(step_start)

    plaintext_result = evaluate_plaintext(payload, operation)

    step_start = perf_counter()
    output_ciphertext = evaluate_fhe(input_ciphertext, operation, payload.weight)
    evaluation_ms = elapsed_ms(step_start)

    step_start = perf_counter()
    fhe_result = decrypt(output_ciphertext)
    decryption_ms = elapsed_ms(step_start)

    is_valid, difference = validate_result(plaintext_result, fhe_result)
    total_ms = elapsed_ms(total_start)

    metrics = {
        "Representation time (ms)": representation_ms,
        "Encryption time (ms)": encryption_ms,
        "Evaluation time (ms)": evaluation_ms,
        "Decryption time (ms)": decryption_ms,
        "Total pipeline time (ms)": total_ms,
        "Input ciphertext size (bytes)": float(input_ciphertext.estimated_size_bytes),
        "Output ciphertext size (bytes)": float(output_ciphertext.estimated_size_bytes),
    }

    return PipelineResult(
        plaintext_result=plaintext_result,
        fhe_result=fhe_result,
        is_valid=is_valid,
        difference=difference,
        metrics=metrics,
        input_ciphertext=input_ciphertext,
        output_ciphertext=output_ciphertext,
    )


def render_pipeline() -> None:
    steps = [
        "Input",
        "Representasi Data",
        "Enkripsi",
        "Evaluasi FHE",
        "Dekripsi",
        "Validasi",
    ]
    st.markdown("**Alur framework**")
    st.markdown(" &rarr; ".join(f"`{step}`" for step in steps))


def render_metrics(metrics: dict[str, float]) -> None:
    rows: list[dict[str, Any]] = []
    for name, value in metrics.items():
        if "bytes" in name:
            display_value = f"{int(value):,} bytes"
        else:
            display_value = f"{value:.4f} ms"
        rows.append({"Metrik": name, "Nilai": display_value})

    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)


def render_ciphertext_metadata(label: str, ciphertext: MockCiphertext) -> None:
    st.markdown(f"**{label}**")
    st.json(
        {
            "scheme_label": ciphertext.scheme_label,
            "slot_count": ciphertext.slot_count,
            "estimated_size_bytes": ciphertext.estimated_size_bytes,
            "operation_history": ciphertext.operation_history,
        }
    )


def main() -> None:
    st.set_page_config(
        page_title="Framework Lapisan Aplikasi FHE",
        page_icon="FHE",
        layout="wide",
    )

    st.title("Framework Lapisan Aplikasi FHE")
    st.caption(
        "Demo frontend untuk prototipe proposal. Backend FHE pada versi ini masih berupa "
        "mock/simulasi agar alur framework bisa ditunjukkan sebelum SDK FHE asli dipilih."
    )

    with st.sidebar:
        st.header("Input Aplikasi")
        x_value = st.number_input("Nilai x", value=10.0, step=1.0)
        y_value = st.number_input("Nilai y", value=5.0, step=1.0)
        weight_value = st.number_input("Weight", value=2.0, step=0.5)
        operation = st.selectbox("Fungsi komputasi", [OP_ADD, OP_MUL, OP_LINEAR])
        run_clicked = st.button("Jalankan Prototipe", type="primary", use_container_width=True)

    st.subheader("Tujuan Prototipe")
    st.write(
        "Interface ini menunjukkan bagaimana developer mendefinisikan input dan fungsi "
        "aplikasi, lalu framework menjalankan alur representasi data, enkripsi, evaluasi "
        "homomorfik, dekripsi, validasi, dan pencatatan metrik."
    )

    render_pipeline()

    if not run_clicked:
        st.info("Isi input di sidebar, pilih fungsi komputasi, lalu jalankan prototipe.")
        return

    payload = PlaintextPayload(x=x_value, y=y_value, weight=weight_value)
    result = run_pipeline(payload, operation)

    st.subheader("Hasil Eksekusi")
    col_plain, col_fhe, col_status = st.columns(3)
    col_plain.metric("Baseline plaintext", format_number(result.plaintext_result))
    col_fhe.metric("Hasil FHE setelah dekripsi", format_number(result.fhe_result))
    col_status.metric("Status validasi", "Valid" if result.is_valid else "Tidak valid")

    if result.is_valid:
        st.success(
            f"Hasil FHE sesuai dengan baseline plaintext. Selisih: {result.difference:.12f}."
        )
    else:
        st.error(
            f"Hasil FHE belum sesuai dengan baseline plaintext. Selisih: {result.difference:.12f}."
        )

    st.subheader("Metrik Dasar")
    render_metrics(result.metrics)

    with st.expander("Lihat metadata ciphertext simulasi"):
        left_col, right_col = st.columns(2)
        with left_col:
            render_ciphertext_metadata("Input ciphertext", result.input_ciphertext)
        with right_col:
            render_ciphertext_metadata("Output ciphertext", result.output_ciphertext)

    st.warning(
        "Catatan: angka waktu dan ukuran ciphertext pada demo ini digunakan untuk menunjukkan "
        "format evaluasi framework. Nilai tersebut belum mewakili performa library FHE asli."
    )


if __name__ == "__main__":
    main()

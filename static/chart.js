const statusEl = document.getElementById("statusMessage");
const fileInput = document.getElementById("audioFile");
const chunkInput = document.getElementById("chunkSize");
const modelSelect = document.getElementById("modelSelect");
const mapSelect = document.getElementById("mapSelect");
const uploadBtn = document.getElementById("uploadBtn");
const analyzeBtn = document.getElementById("analyzeBtn");
const clearBtn = document.getElementById("clearBtn");
const downloadLink = document.getElementById("downloadLink");
const rawJsonEl = document.getElementById("rawJson");
const tableBody = document.querySelector("#emotionTable tbody");

let uploadedFilename = null;
let chartInstance = null;
let lastBlobUrl = null;

function setStatus(message, type = "info") {
    statusEl.textContent = message || "";
    statusEl.className = `status ${type}`;
}

function clearTable() {
    tableBody.innerHTML = "";
}

function renderChart(times, emotions) {
    const ctx = document.getElementById("emotionChart").getContext("2d");

    if (chartInstance) {
        chartInstance.destroy();
    }

    chartInstance = new Chart(ctx, {
        type: "line",
        data: {
            labels: times,
            datasets: [{
                label: "Emotion",
                data: emotions,
                borderColor: "#2563eb",
                backgroundColor: "rgba(37,99,235,0.15)",
                tension: 0.3,
                pointRadius: 6,
            }],
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    type: "category",
                    labels: [...new Set(emotions)],
                },
            },
        },
    });
}

function renderResults(payload) {
    const data = payload.timeline || [];
    clearTable();

    if (data.length === 0) {
        setStatus("No emotion data to display.", "warn");
        rawJsonEl.textContent = JSON.stringify(payload, null, 2);
        return;
    }

    setStatus("Analysis complete.", "success");

    data.forEach((row) => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${row.time}</td>
            <td>${row.emotion}</td>
            <td>${row.confidence}</td>
        `;
        tableBody.appendChild(tr);
    });

    const times = data.map((d) => d.time);
    const emotions = data.map((d) => d.emotion);
    renderChart(times, emotions);

    rawJsonEl.textContent = JSON.stringify(payload, null, 2);

    if (lastBlobUrl) {
        URL.revokeObjectURL(lastBlobUrl);
    }
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    lastBlobUrl = URL.createObjectURL(blob);
    downloadLink.href = lastBlobUrl;
}

uploadBtn.addEventListener("click", async () => {
    const file = fileInput.files[0];
    if (!file) {
        setStatus("Select an audio file first.", "warn");
        return;
    }

    setStatus("Uploading...", "info");

    const formData = new FormData();
    formData.append("audio", file);

    try {
        const res = await fetch("/upload", { method: "POST", body: formData });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
            throw new Error(data.error || "Upload failed");
        }
        uploadedFilename = data.filename || null;
        setStatus(`Uploaded: ${uploadedFilename || "file"}`, "success");
    } catch (err) {
        setStatus(err.message || "Upload failed", "error");
    }
});

analyzeBtn.addEventListener("click", async () => {
    setStatus("Analyzing...", "info");

    const payload = {
        filename: uploadedFilename,
        chunk_ms: parseInt(chunkInput.value, 10),
        emotion_map: mapSelect.value,
        model: modelSelect.value,
    };

    try {
        const res = await fetch("/analyze", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });

        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
            throw new Error(data.error || "Analysis failed");
        }

        renderResults(data);
    } catch (err) {
        setStatus(err.message || "Analysis failed", "error");
    }
});

clearBtn.addEventListener("click", async () => {
    setStatus("Clearing uploads...", "info");
    try {
        const res = await fetch("/clear", { method: "POST" });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
            throw new Error(data.error || "Clear failed");
        }
        uploadedFilename = null;
        clearTable();
        rawJsonEl.textContent = "";
        if (chartInstance) {
            chartInstance.destroy();
            chartInstance = null;
        }
        setStatus(`Cleared ${data.deleted || 0} file(s).`, "success");
    } catch (err) {
        setStatus(err.message || "Clear failed", "error");
    }
});

const BRIDGE_URL = "http://127.0.0.1:8765/download-event";

async function reportDownload(downloadId) {
  const items = await chrome.downloads.search({ id: downloadId });
  if (!items || items.length === 0) return;

  const item = items[0];
  const filename = (item.filename || "").toLowerCase();
  const mime = (item.mime || "").toLowerCase();
  if (!filename.endsWith(".pdf") && mime !== "application/pdf") return;

  const payload = {
    id: item.id,
    filename: item.filename,
    finalUrl: item.finalUrl || item.url || "",
    referrer: item.referrer || "",
    mime: item.mime || "",
    fileSize: item.fileSize || 0,
    startTime: item.startTime || "",
    endTime: new Date().toISOString()
  };

  try {
    await fetch(BRIDGE_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
  } catch (error) {
    console.warn("Scout Download Bridge could not reach local bridge", error);
  }
}

chrome.downloads.onChanged.addListener((delta) => {
  if (!delta.state || delta.state.current !== "complete") return;
  reportDownload(delta.id);
});

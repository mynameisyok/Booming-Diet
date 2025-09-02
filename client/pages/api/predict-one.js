// booming-diet\pages\api\predict-one.js

export default async function handler(req, res) {
  if (req.method !== "POST") {
    return res.status(405).json({ error: "Method not allowed" });
  }
  try {
    const PY_API = process.env.PY_API_URL || "http://127.0.0.1:8000";
    const r = await fetch(`${PY_API}/predict-one`, {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify(req.body),
    });
    const data = await r.json();
    return res.status(r.ok ? 200 : r.status).json(data);
  } catch (e) {
    return res.status(500).json({ error: String(e) });
  }
}

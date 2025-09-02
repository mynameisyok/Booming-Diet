"use client";

import { useState } from "react";
import Head from "next/head";
import styles from "@/styles/BloomDiet.module.css";

export default function BloomDietPage() {
  const [gender, setGender] = useState("");
  const [age, setAge] = useState("");
  const [height, setHeight] = useState("");
  const [weight, setWeight] = useState("");
  const [disease, setDisease] = useState("None");
  const [allergies, setAllergies] = useState("None");
  const [exerciseHours, setExerciseHours] = useState("");
  const [loading, setLoading] = useState(false);
  const [prediction, setPrediction] = useState(null);      // string หรือ object ก็ได้
  const [probabilities, setProbabilities] = useState(null); // object
  const [error, setError] = useState("");

  const yearNow = new Date().getFullYear();

  const calcBMI = (h, w) => {
    const heightNum = Number(h);
    const weightNum = Number(w);
    if (!heightNum || !weightNum) return null;
    const bmi = weightNum / ((heightNum / 100) ** 2);
    return Number(bmi.toFixed(2));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    setPrediction(null);
    setProbabilities(null);

    const bmi = calcBMI(height, weight);

    try {
      const res = await fetch("/api/predict-one", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          data: {
            gender,
            age: Number(age) || null,
            height_cm: Number(height) || null,
            weight_kg: Number(weight) || null,
            bmi,
            disease,
            allergies,
            exercise_hours: Number(exerciseHours) || 0,
          },
        }),
      });

      if (!res.ok) throw new Error("HTTP " + res.status);
      const json = await res.json();

      setPrediction(json.prediction ?? "—");
      setProbabilities(json.probabilities ?? null);
    } catch (err) {
      setError(`Failed to fetch: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Head>
        <title>BloomDiet – แบบฟอร์มสุขภาพ & AI เมนูอาหาร</title>
        {/* โหลดฟอนต์ Prompt (ถ้าไม่ต้องการ ลบบรรทัดนี้ได้) */}
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
        <link
          href="https://fonts.googleapis.com/css2?family=Prompt:wght@300;400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </Head>

      <div className={styles.page}>
        <div className={styles.container}>
          <h1 className={styles.title}>🌸 BloomDiet</h1>
          <p className={styles.subtitle}>กรอกข้อมูลสุขภาพของคุณเพื่อรับคำแนะนำเมนูอาหารจาก AI</p>

          <form onSubmit={handleSubmit}>
            {/* เพศ */}
            <label className={styles.label}>เพศ</label>
            <select
              className={styles.select}
              value={gender}
              onChange={(e) => setGender(e.target.value)}
            >
              <option value="">-- เลือก --</option>
              <option value="Male">ชาย</option>
              <option value="Female">หญิง</option>
            </select>

            {/* อายุ */}
            <label className={styles.label}>อายุ (ปี)</label>
            <input
              type="number"
              min="1"
              max="120"
              className={styles.input}
              value={age}
              onChange={(e) => setAge(e.target.value)}
            />

            {/* ส่วนสูง */}
            <label className={styles.label}>ส่วนสูง (ซม.)</label>
            <input
              type="number"
              min="100"
              max="250"
              className={styles.input}
              value={height}
              onChange={(e) => setHeight(e.target.value)}
            />

            {/* น้ำหนัก */}
            <label className={styles.label}>น้ำหนัก (กก.)</label>
            <input
              type="number"
              min="20"
              max="300"
              className={styles.input}
              value={weight}
              onChange={(e) => setWeight(e.target.value)}
            />

            {/* โรคประจำตัว */}
            <label className={styles.label}>โรคประจำตัว</label>
            <select
              className={styles.select}
              value={disease}
              onChange={(e) => setDisease(e.target.value)}
            >
              <option value="None">ไม่มี</option>
              <option value="Diabetes">เบาหวาน</option>
              <option value="Hypertension">ความดันโลหิตสูง</option>
              <option value="Heart">โรคหัวใจ</option>
              <option value="Obesity">โรคอ้วน</option>
            </select>

            {/* การแพ้อาหาร */}
            <label className={styles.label}>การแพ้อาหาร</label>
            <select
              className={styles.select}
              value={allergies}
              onChange={(e) => setAllergies(e.target.value)}
            >
              <option value="None">ไม่มี</option>
              <option value="Gluten">Gluten</option>
              <option value="Dairy">นม</option>
              <option value="Nuts">ถั่ว</option>
              <option value="Seafood">อาหารทะเล</option>
              <option value="Eggs">ไข่</option>
            </select>

            {/* ชั่วโมงออกกำลังกาย */}
            <label className={styles.label}>ชั่วโมงออกกำลังกายต่อสัปดาห์</label>
            <input
              type="number"
              step="0.5"
              min="0"
              max="50"
              className={styles.input}
              value={exerciseHours}
              onChange={(e) => setExerciseHours(e.target.value)}
            />

            <button type="submit" className={styles.button} disabled={loading}>
              {loading ? "⏳ กำลังทำนาย..." : "ขอคำแนะนำเมนูด้วย AI 🍽️"}
            </button>
          </form>

          {/* แสดงผล */}
          <div className={styles.result}>
            {error && <div className={styles.error}>❌ {error}</div>}

            {!error && prediction && (
              <>
                <div className={styles.pred}>
                  ✅ <b>คำแนะนำ:</b> {String(prediction)}
                </div>
                {probabilities && (
                  <pre className={styles.pre}>
{JSON.stringify(probabilities, null, 2)}
                  </pre>
                )}
              </>
            )}
          </div>

          <div className={styles.footer}>© {yearNow} BloomDiet</div>
        </div>
      </div>
    </>
  );
}

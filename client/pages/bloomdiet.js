"use client";

import { useState, useRef } from "react";
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
  const [prediction, setPrediction] = useState(null);
  const [error, setError] = useState("");

  // refs สำหรับเด้งไปช่องที่ผิด/ว่าง
  const genderRef = useRef(null);
  const ageRef = useRef(null);
  const heightRef = useRef(null);
  const weightRef = useRef(null);
  const exerciseRef = useRef(null); // ⬅️ เพิ่ม ref

  const yearNow = new Date().getFullYear();

  const calcBMI = (h, w) => {
    const heightNum = Number(h);
    const weightNum = Number(w);
    if (!heightNum || !weightNum) return null;
    const bmi = weightNum / ((heightNum / 100) ** 2);
    return Number(bmi.toFixed(2));
  };

  // helper: focus + scroll + ใช้ native validity tooltip
  const jumpTo = (ref, msg) => {
    const el = ref?.current;
    if (!el) return;
    el.scrollIntoView({ behavior: "smooth", block: "center" });
    el.focus({ preventScroll: true });
    if (el.setCustomValidity) {
      el.setCustomValidity(msg);
      el.reportValidity();
      setTimeout(() => el.setCustomValidity(""), 2000);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setPrediction(null);

    // ✅ ตรวจทีละช่อง แล้วเด้งไปช่องแรกที่ไม่ผ่าน
    if (!gender) return jumpTo(genderRef, "โปรดเลือกเพศ");

    const ageNum = Number(age);
    if (!age) return jumpTo(ageRef, "กรอกอายุ");
    if (Number.isNaN(ageNum) || ageNum < 1 || ageNum > 120)
      return jumpTo(ageRef, "อายุต้องอยู่ระหว่าง 1–120 ปี");

    const heightNum = Number(height);
    if (!height) return jumpTo(heightRef, "กรอกส่วนสูง");
    // if (Number.isNaN(heightNum) || heightNum < 100 || heightNum > 250)
    //   return jumpTo(heightRef, "ส่วนสูงต้องอยู่ระหว่าง 100–250 ซม.");

    const weightNum = Number(weight);
    if (!weight) return jumpTo(weightRef, "กรอกน้ำหนัก");
    // if (Number.isNaN(weightNum) || weightNum < 20 || weightNum > 300)
    //   return jumpTo(weightRef, "น้ำหนักต้องอยู่ระหว่าง 20–300 กก.");

    // ⬇️ บังคับช่องชั่วโมงออกกำลังกาย
    const exNum = Number(exerciseHours);
    if (exerciseHours === "") return jumpTo(exerciseRef, "กรอกชั่วโมงออกกำลังกายต่อสัปดาห์");
    // if (Number.isNaN(exNum) || exNum < 0 || exNum > 50)
    //   return jumpTo(exerciseRef, "ชั่วโมงออกกำลังกายต้องอยู่ระหว่าง 0–50 ชั่วโมง");

    setLoading(true);
    const bmi = calcBMI(heightNum, weightNum);

    try {
      const res = await fetch("/api/predict-one", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          data: {
            gender,
            age: ageNum,
            height_cm: heightNum,
            weight_kg: weightNum,
            bmi,
            disease,
            allergies,
            exercise_hours: exNum, // ⬅️ ใช้ค่าที่ตรวจแล้ว
          },
        }),
      });

      if (!res.ok) {
        const msg = await res.text();
        throw new Error(`HTTP ${res.status} ${msg}`);
      }
      const json = await res.json();
      setPrediction(json?.prediction ?? "—");
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

          <form onSubmit={handleSubmit} noValidate>
            {/* เพศ */}
            <label className={styles.label}>เพศ</label>
            <select
              ref={genderRef}
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
              ref={ageRef}
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
              ref={heightRef}
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
              ref={weightRef}
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
              ref={exerciseRef}
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

          <div className={styles.result}>
            {error && <div className={styles.error}>❌ {error}</div>}
            {!error && prediction && (
              <div className={styles.pred}>
                ✅ <b>คำแนะนำ:</b> {String(prediction)}
              </div>
            )}
          </div>

          <div className={styles.footer}>© {yearNow} BloomDiet</div>
        </div>
      </div>
    </>
  );
}

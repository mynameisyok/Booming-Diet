// pages/register.js

"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import Head from "next/head";
import styles from "@/styles/Register.module.css";

export default function RegisterPage() {
  const [showOk, setShowOk] = useState(false);
  const [days, setDays] = useState([]);
  const [months, setMonths] = useState([]);
  const [years, setYears] = useState([]);

  useEffect(() => {
    setDays(Array.from({ length: 31 }, (_, i) => i + 1));
    setMonths([
      "ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.",
      "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค.",
    ]);
    const now = new Date();
    const startY = now.getFullYear() - 100;
    setYears(Array.from({ length: 101 }, (_, i) => startY + i));
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    setShowOk(true);
    setTimeout(() => {
      setShowOk(false);
      window.location.href = "/login";
    }, 1200);
  };

  const yearNow = new Date().getFullYear();

  return (
    <>
      <Head>
        <title>Booming Diet — สมัครสมาชิก</title>
      </Head>

      {/* แถบบน */}
      <div className={styles.topbar}>
        <div className={styles.containerTop}>
          <button className={styles.back} onClick={() => history.back()}>
            กลับ
          </button>
          <div className={styles.brand}>
            <svg width="22" height="22" viewBox="0 0 24 24" aria-hidden="true">
              <path
                d="M12 21s-6.5-3.9-9.1-7.1C1.6 12.1 2 8.8 4.5 7.3 6.4 6.2 8.7 6.8 10 8.4c1.3-1.6 3.6-2.2 5.5-1.1 2.5 1.5 2.9 4.8 1.6 6.6C18.5 17.1 12 21 12 21z"
                fill="#F59BB2"
              />
              <path
                d="M18.8 4.5c-2.3-.4-4.3.6-5.6 2.1 1.7.1 3.6-.4 5-.9 1-.4 1.5-1.2.6-1.2z"
                fill="#8FD6C9"
              />
            </svg>
            <span>Booming Diet</span>
          </div>
        </div>
      </div>

      {/* เนื้อหา */}
      <div className={styles.container}>
        <h1 className={styles.h1}>สร้างบัญชี</h1>

        <div className={styles.card}>
          <ul className={styles.bullets}>
            <li>รับสิทธิประโยชน์และโปรโมชันเฉพาะสมาชิก Booming Diet</li>
            <li>ปรับแต่งแผนโภชนาการให้เหมาะกับคุณ</li>
          </ul>

          <form onSubmit={handleSubmit}>
            {/* ชื่อ-นามสกุล */}
            <div className={`${styles.row} ${styles.two}`}>
              <div>
                <label className={styles.formLabel}>ชื่อ*</label>
                <input
                  type="text"
                  placeholder="ชื่อจริง"
                  required
                  className={styles.formInput}
                />
              </div>
              <div>
                <label className={styles.formLabel}>นามสกุล*</label>
                <input
                  type="text"
                  placeholder="นามสกุล"
                  required
                  className={styles.formInput}
                />
              </div>
            </div>

            {/* Email / เบอร์มือถือ */}
            <div className={`${styles.row} ${styles.two}`}>
              <div>
                <label className={styles.formLabel}>อีเมล</label>
                <input
                  type="email"
                  placeholder="you@example.com"
                  className={styles.formInput}
                />
              </div>
              <div>
                <label className={styles.formLabel}>เบอร์มือถือ*</label>
                <input
                  type="tel"
                  placeholder="08x-xxx-xxxx"
                  required
                  className={styles.formInput}
                />
              </div>
            </div>

            {/* ที่อยู่ */}
            <div className={styles.row}>
              <div>
                <label className={styles.formLabel}>ที่อยู่</label>
                <textarea
                  placeholder="บ้านเลขที่ / ถนน / แขวง / เขต / จังหวัด / รหัสไปรษณีย์"
                  className={styles.formTextarea}
                />
              </div>
            </div>

            {/* วันเกิด */}
            <div className={`${styles.row} ${styles.three}`}>
              <div>
                <label className={styles.formLabel}>วัน</label>
                <select required className={styles.formSelect}>
                  <option value="">วัน</option>
                  {days.map((d) => (
                    <option key={d}>{d}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className={styles.formLabel}>เดือน</label>
                <select required className={styles.formSelect}>
                  <option value="">เดือน</option>
                  {months.map((m, i) => (
                    <option key={i} value={i + 1}>
                      {m}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className={styles.formLabel}>ปี (ค.ศ.)</label>
                <select required className={styles.formSelect}>
                  <option value="">ปี</option>
                  {years.map((y) => (
                    <option key={y}>{y}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className={styles.center} style={{ marginTop: 16 }}>
              <button
                type="submit"
                className={`${styles.btn} ${styles.btnPrimary}`}
              >
                สมัครสมาชิก Booming Diet
              </button>

              {showOk && (
                <div className={`${styles.alert} ${styles.ok}`}>
                  สมัครสมาชิกสำเร็จ (โหมดสแตติก)
                </div>
              )}

              <div className={styles.muted} style={{ marginTop: 10 }}>
                มีบัญชีอยู่แล้ว? <Link href="/login">ลงชื่อเข้าใช้</Link>
              </div>
            </div>
          </form>
        </div>

        <div className={styles.footer}>© {yearNow} Booming Diet</div>
      </div>
    </>
  );
}

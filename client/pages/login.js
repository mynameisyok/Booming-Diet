"use client";

import { useState } from "react";
import styles from "@/styles/Login.module.css";
import Link from "next/link";

export const metadata = {
  title: "Booming Diet — Login",
};

export default function LoginPage() {
  const [showOk, setShowOk] = useState(false);
  const year = new Date().getFullYear();

  const onSubmit = (e) => {
    e.preventDefault();
    setShowOk(true);
    const t = setTimeout(() => setShowOk(false), 3000);
    // ถ้าต้องการพาไปหน้าทดสอบโมเดล ให้ยกคอมเมนต์บรรทัดล่าง:
    // router.push("/predict-ui");
    return () => clearTimeout(t);
  };

  return (
    <div className={styles.wrap}>
      <div className={styles.card}>
        {/* โลโก้ */}
        <div className={styles.brand}>
          <svg width="28" height="28" viewBox="0 0 24 24" aria-hidden="true">
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

        <h1 className={styles.h1}>เข้าสู่ระบบ</h1>

        {/* ฟอร์มสแตติก: ไม่เรียก API */}
        <form onSubmit={onSubmit}>
          <div className={styles.field}>
            <input id="phone" type="tel" placeholder="หมายเลขโทรศัพท์ " />
          </div>

          <div className={styles.row}>
            <label>
              <input type="checkbox" id="remember" /> จำฉันไว้
            </label>
            {/* เดิมเป็น onclick alert; ใน React ใช้ onClick */}
            <a
              className={styles.link}
              href="#"
              onClick={(e) => {
                e.preventDefault();
                alert("ลืมรหัสผ่าน (ตัวอย่างสแตติก)");
              }}
            >
              ลืมรหัสผ่าน?
            </a>
          </div>

          <button className={`${styles.btn} ${styles.btnPrimary}`} type="submit">
            เข้าสู่ระบบ
          </button>
        </form>

        {showOk && <div className={`${styles.alert} ${styles.ok}`}>เข้าสู่ระบบสำเร็จ </div>}

        {/* ปุ่มสมัครสมาชิก: เดิมชี้ไป Legister.html — แนะนำให้ใช้เส้นทาง /register */}
        <Link href="/register" className={`${styles.btn} ${styles.btnOutline}`}>
          สมัครสมาชิก Booming Diet
        </Link>

        <div className={styles.footer}>
          © <span>{year}</span> Booming Diet
        </div>
      </div>
    </div>
  );
}

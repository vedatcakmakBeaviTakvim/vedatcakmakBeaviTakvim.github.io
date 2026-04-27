#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VedatBot — Beyanname Son Gün Alarm Sistemi
- Son gün: sesli alarm + yanıp sönen lacivert-sarı pencere
- Ertesi gün: "Teslim edildi mi?" kontrolü
- Uzatma varsa: yeni tarihi cache'e işler, takvim güncellenir
"""
import tkinter as tk
from tkinter import messagebox
from datetime import date, timedelta
import winsound, threading, time, sys, os, json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from beyanname_takvim import beyanname_tarihleri_hesapla

DIZIN = os.path.dirname(os.path.abspath(__file__))
CACHE_DOSYA = os.path.join(DIZIN, "takvim_cache.json")
TESLIM_LOG = os.path.join(DIZIN, "teslim_log.json")

alarm_aktif = False


# ── Cache İşlemleri ────────────────────────────────────────────────────────
def cache_yukle():
    if os.path.exists(CACHE_DOSYA):
        try:
            with open(CACHE_DOSYA, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def cache_kaydet(data):
    with open(CACHE_DOSYA, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def teslim_log_yukle():
    if os.path.exists(TESLIM_LOG):
        try:
            with open(TESLIM_LOG, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []


def teslim_log_kaydet(kayit):
    log = teslim_log_yukle()
    log.append(kayit)
    with open(TESLIM_LOG, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)


# ── Bugün/Dün Son Gün Hesaplama ────────────────────────────────────────────
def bugun_son_gunler():
    """Bugün son günü olan beyannameler (cache + dinamik)."""
    bugun = date.today()
    sonuc = []

    # Önce cache'den bak
    cache = cache_yukle()
    for g in cache.get("girdiler", []):
        try:
            if date.fromisoformat(g["tarih"]) == bugun:
                sonuc.append(g)
        except Exception:
            pass

    # Cache boşsa dinamik hesapla
    if not sonuc:
        for ad, tarih in beyanname_tarihleri_hesapla():
            if tarih == bugun:
                sonuc.append({"tarih": bugun.isoformat(), "tur": ad})

    return sonuc


def dun_son_gunler():
    """Dün son günü olan ama teslim kaydı olmayan beyannameler."""
    dun = date.today() - timedelta(days=1)
    sonuc = []

    # Cache'den dünün beyannamelerini bul
    cache = cache_yukle()
    for g in cache.get("girdiler", []):
        try:
            if date.fromisoformat(g["tarih"]) == dun:
                sonuc.append(g)
        except Exception:
            pass

    # Dinamik hesaptan da bak
    if not sonuc:
        for ad, tarih in beyanname_tarihleri_hesapla():
            if tarih == dun:
                sonuc.append({"tarih": dun.isoformat(), "tur": ad})

    if not sonuc:
        return []

    # Teslim logundan zaten kaydedilmişleri çıkar
    log = teslim_log_yukle()
    teslim_edilmis = {(k["tarih"], k["tur"]) for k in log}

    bekleyenler = [
        g for g in sonuc
        if (g["tarih"], g["tur"]) not in teslim_edilmis
    ]
    return bekleyenler


# ── Tarihi Cache'de Güncelle ───────────────────────────────────────────────
def tarihi_guncelle(eski_tarih_str, tur, yeni_tarih_str):
    """Cache'deki bir beyanname tarihini günceller."""
    cache = cache_yukle()
    girdiler = cache.get("girdiler", [])
    guncellendi = False

    for g in girdiler:
        if g.get("tarih") == eski_tarih_str and g.get("tur") == tur:
            g["tarih"] = yeni_tarih_str
            g["uzatma_notu"] = f"{eski_tarih_str} → {yeni_tarih_str} (uzatma)"
            guncellendi = True
            break

    if guncellendi:
        cache["girdiler"] = sorted(girdiler, key=lambda x: x["tarih"])
        cache["son_guncelleme"] = date.today().isoformat()
        cache_kaydet(cache)
        print(f"[Alarm] Cache güncellendi: {tur} → {yeni_tarih_str}", flush=True)
    else:
        # Cache'de yoksa yeni kayıt ekle
        girdiler.append({
            "tarih": yeni_tarih_str,
            "tur": tur,
            "kaynak": "manuel_uzatma",
            "uzatma_notu": f"{eski_tarih_str} → {yeni_tarih_str} (uzatma)"
        })
        cache["girdiler"] = sorted(girdiler, key=lambda x: x["tarih"])
        cache_kaydet(cache)
        print(f"[Alarm] Yeni tarih eklendi: {tur} → {yeni_tarih_str}", flush=True)

    return guncellendi


# ── Tarih Giriş Penceresi ─────────────────────────────────────────────────
def tarih_sor(parent, tur_adi):
    """Yeni tarih girmek için ayrı tkinter penceresi açar."""
    sonuc = {"deger": None}

    pencere = tk.Toplevel(parent)
    pencere.title("Uzatma Tarihi")
    pencere.attributes("-topmost", True)
    pencere.geometry("420x220+300+250")
    pencere.config(bg="#1a1a2e")
    pencere.resizable(False, False)
    pencere.grab_set()  # Modal yap

    tk.Label(pencere,
        text="📅 Uzatma Tarihi",
        font=("Arial", 13, "bold"), fg="#FFD700", bg="#1a1a2e"
    ).pack(pady=(20, 5))

    tk.Label(pencere,
        text=f"{tur_adi}\niçin yeni son tarih:",
        font=("Arial", 10), fg="#aaaacc", bg="#1a1a2e", justify="center"
    ).pack(pady=(0, 10))

    giris = tk.Entry(pencere, font=("Arial", 14, "bold"),
                     justify="center", width=14,
                     bg="#16213e", fg="white",
                     insertbackground="white")
    giris.pack(pady=5)
    giris.insert(0, "GG.AA.YYYY")
    giris.select_range(0, "end")
    giris.focus()

    def onayla(event=None):
        sonuc["deger"] = giris.get()
        pencere.destroy()

    def iptal():
        pencere.destroy()

    btn_f = tk.Frame(pencere, bg="#1a1a2e")
    btn_f.pack(pady=12)
    tk.Button(btn_f, text="Onayla", font=("Arial", 11, "bold"),
              bg="#22aa44", fg="white", command=onayla, width=10).pack(side="left", padx=8)
    tk.Button(btn_f, text="İptal", font=("Arial", 11),
              bg="#aa2222", fg="white", command=iptal, width=10).pack(side="left", padx=8)

    giris.bind("<Return>", onayla)
    parent.wait_window(pencere)
    return sonuc["deger"]


# ── Teslim Kontrol Penceresi ───────────────────────────────────────────────
def teslim_kontrol_goster(bekleyenler):
    """Dünkü beyannameler için 'teslim edildi mi?' sorar."""
    root = tk.Tk()
    root.title("VedatBot — Beyanname Kontrol")
    root.attributes("-topmost", True)
    root.geometry("680x520+200+100")
    root.config(bg="#1a1a2e")
    root.resizable(False, False)

    tk.Label(root,
        text="📋 DÜNKÜ BEYANNAME KONTROLÜ",
        font=("Arial", 15, "bold"), fg="#FFD700", bg="#1a1a2e"
    ).pack(pady=(20, 5))

    tk.Label(root,
        text=f"{(date.today()-timedelta(days=1)).strftime('%d.%m.%Y')} tarihli beyannameler:",
        font=("Arial", 11), fg="#aaaacc", bg="#1a1a2e"
    ).pack(pady=(0, 10))

    # Her beyanname için frame
    frames = []
    for b in bekleyenler:
        f = tk.Frame(root, bg="#16213e", bd=1, relief="solid")
        f.pack(fill="x", padx=20, pady=4)

        tk.Label(f, text=f"  • {b['tur']}", font=("Arial", 11),
                 fg="white", bg="#16213e", anchor="w").pack(side="left", padx=10, pady=8)

        durum_var = tk.StringVar(value="")
        frames.append({"beyanname": b, "durum": durum_var})

        btn_frame = tk.Frame(f, bg="#16213e")
        btn_frame.pack(side="right", padx=10)

        tk.Radiobutton(btn_frame, text="✅ Teslim", variable=durum_var,
                       value="teslim", bg="#16213e", fg="#44ff88",
                       selectcolor="#16213e", font=("Arial", 10, "bold"),
                       activebackground="#16213e").pack(side="left", padx=5)

        tk.Radiobutton(btn_frame, text="📅 Uzatıldı", variable=durum_var,
                       value="uzatildi", bg="#16213e", fg="#FFD700",
                       selectcolor="#16213e", font=("Arial", 10, "bold"),
                       activebackground="#16213e").pack(side="left", padx=5)

        tk.Radiobutton(btn_frame, text="⏭️ Sonra", variable=durum_var,
                       value="sonra", bg="#16213e", fg="#aaaacc",
                       selectcolor="#16213e", font=("Arial", 10, "bold"),
                       activebackground="#16213e").pack(side="left", padx=5)

    def kaydet():
        for item in frames:
            durum = item["durum"].get()
            b = item["beyanname"]

            if durum == "teslim":
                teslim_log_kaydet({
                    "tarih": b["tarih"],
                    "tur": b["tur"],
                    "teslim_tarihi": date.today().isoformat(),
                    "durum": "teslim"
                })
                print(f"[Alarm] Teslim kaydedildi: {b['tur']}", flush=True)

            elif durum == "uzatildi":
                yeni = tarih_sor(root, b["tur"])
                if yeni:
                    try:
                        gun, ay, yil = yeni.strip().split(".")
                        yeni_tarih = date(int(yil), int(ay), int(gun))
                        tarihi_guncelle(b["tarih"], b["tur"], yeni_tarih.isoformat())
                        teslim_log_kaydet({
                            "tarih": b["tarih"],
                            "tur": b["tur"],
                            "yeni_tarih": yeni_tarih.isoformat(),
                            "durum": "uzatildi"
                        })
                        messagebox.showinfo("Güncellendi",
                            f"{b['tur']}\nYeni tarih: {yeni_tarih.strftime('%d.%m.%Y')}\nTakvim güncellendi ✅",
                            parent=root)
                    except Exception as e:
                        messagebox.showerror("Hata", f"Tarih formatı yanlis: {e}", parent=root)

            elif durum == "sonra":
                # Bir sonraki kontrolde tekrar sorulacak
                print(f"[Alarm] Ertelendi: {b['tur']}", flush=True)

            # Seçim yapılmamışsa atla
        root.destroy()

    tk.Button(root,
        text="KAYDET",
        font=("Arial", 13, "bold"),
        bg="#22aa44", fg="white",
        command=kaydet, width=20
    ).pack(pady=20)

    tk.Label(root,
        text="'Sonra' seçerseniz yarın tekrar sorulur.",
        font=("Arial", 9), fg="#666688", bg="#1a1a2e"
    ).pack()

    root.mainloop()


# ── Alarm Penceresi ────────────────────────────────────────────────────────
def ses_cal():
    while alarm_aktif:
        winsound.Beep(1000, 400)
        time.sleep(0.2)
        winsound.Beep(1500, 400)
        time.sleep(0.2)
        winsound.Beep(2000, 400)
        time.sleep(4)


def alarm_goster(beyannameler):
    global alarm_aktif
    alarm_aktif = True
    tur_metni = "\n".join(f"• {b['tur']}" for b in beyannameler)
    root = tk.Tk()
    root.title("BEYANNAME SON GUN ALARMI")
    root.attributes("-topmost", True)
    root.geometry("760x460+200+150")
    root.config(bg="#002366")
    root.resizable(False, False)

    lbl = tk.Label(root,
        text=f"SON GUN!\n\n{date.today().strftime('%d.%m.%Y')}\n\n{tur_metni}\n\nBUGUN BEYANNAMEYI VER!",
        font=("Arial", 16, "bold"), fg="white", bg="#002366", justify="center")
    lbl.pack(expand=True, fill="both", padx=20, pady=20)

    def yanip_son():
        if not alarm_aktif:
            return
        current = root.cget("bg")
        nxt = "#002366" if current != "#002366" else "#FFD700"
        fg = "white" if nxt == "#002366" else "#002366"
        root.config(bg=nxt)
        lbl.config(bg=nxt, fg=fg)
        root.after(600, yanip_son)

    def kapat():
        global alarm_aktif
        alarm_aktif = False
        root.destroy()

    def ertele():
        global alarm_aktif
        alarm_aktif = False
        root.destroy()
        threading.Thread(target=lambda: (time.sleep(1800), main()), daemon=True).start()

    btn = tk.Frame(root, bg="#002366")
    btn.pack(pady=10)
    tk.Button(btn, text="TAMAM KAPAT", font=("Arial", 13, "bold"),
              bg="#22aa44", fg="white", command=kapat, width=16).pack(side="left", padx=10)
    tk.Button(btn, text="30 DK ERTELE", font=("Arial", 13, "bold"),
              bg="#ee7700", fg="white", command=ertele, width=16).pack(side="left", padx=10)

    threading.Thread(target=ses_cal, daemon=True).start()
    yanip_son()
    root.protocol("WM_DELETE_WINDOW", kapat)
    root.mainloop()


# ── Ana Döngü ──────────────────────────────────────────────────────────────
def main():
    import datetime as _dt

    print(f"[VedatBot Alarm] Baslatildi — {date.today().strftime('%d.%m.%Y')}", flush=True)

    while True:
        # 1) Dünün beyannameleri teslim edildi mi?
        bekleyenler = dun_son_gunler()
        if bekleyenler:
            print(f"[VedatBot Alarm] Dünkü {len(bekleyenler)} beyanname kontrol bekleniyor...", flush=True)
            teslim_kontrol_goster(bekleyenler)

        # 2) Bugün son gün var mı?
        bugun = bugun_son_gunler()
        if bugun:
            print(f"[VedatBot Alarm] SON GUN: {len(bugun)} beyanname!", flush=True)
            for b in bugun:
                print(f"  — {b['tur']}", flush=True)
            alarm_goster(bugun)
        else:
            # Yaklaşan var mı?
            cache = cache_yukle()
            bugun_dt = date.today()
            yaklasan = []
            for g in cache.get("girdiler", []):
                try:
                    tarih = date.fromisoformat(g["tarih"])
                    fark = (tarih - bugun_dt).days
                    if 0 < fark <= 3:
                        yaklasan.append((fark, g["tur"]))
                except Exception:
                    pass

            if yaklasan:
                fark, tur = sorted(yaklasan)[0]
                print(f"[VedatBot Alarm] {fark} gun kaldi: {tur}", flush=True)
            else:
                print(f"[VedatBot Alarm] Bugun son gun degil.", flush=True)

        # 3) Ertesi gün 08:00'e kadar bekle
        simdi = _dt.datetime.now()
        yarin_sabah = simdi.replace(hour=8, minute=0, second=0, microsecond=0)
        if simdi.hour >= 8:
            yarin_sabah += timedelta(days=1)

        bekleme = (yarin_sabah - simdi).total_seconds()
        print(f"[VedatBot Alarm] Sonraki kontrol: {yarin_sabah.strftime('%d.%m.%Y 08:00')}", flush=True)
        time.sleep(max(bekleme, 3600))


if __name__ == "__main__":
    main()

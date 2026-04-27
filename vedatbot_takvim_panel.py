#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VedatBot Takvim — Bağımsız Beyanname & Prim Takip Sistemi
API gerektirmez. Açık/koyu tema. Hiyerarşik şeffaflık.
"""
import tkinter as tk
from tkinter import ttk
import threading, time, winsound, os, sys, json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from beyanname_takvim import (
    KATEGORILER, ayarlari_yukle, ayarlari_kaydet,
    ilk_kurulum_yapildi_mi, cache_veya_hesapla, bugun_son_gunler
)
from datetime import date, datetime

DIZIN = os.path.dirname(os.path.abspath(__file__))
TEMA_DOSYA = os.path.join(DIZIN, "takvim_tema.json")
alarm_aktif = False

# ── Tema Tanımları ─────────────────────────────────────────────────────────
TEMALAR = {
    "koyu": {
        "BG": "#0f0f1a", "PANEL": "#1a1a2e", "KART": "#16213e",
        "TEXT": "#e2e8f0", "TEXT2": "#6677aa",
        "MAVI": "#3b82f6", "YESIL": "#22c55e", "KIRMIZI": "#ff3333", "SARI": "#f59e0b",
        # Acil — renkli
        "L1_BG": "#cc0000", "L2_BG": "#200505", "L3_BG": "#181400",
        # Normal arka planlar — ince fark
        "L4_BG": "#141c2e", "L5_BG": "#0f1220", "L6_BG": "#0a0b14",
        # Acil yazılar
        "L1_TEXT": "#ffffff", "L2_TEXT": "#ff6666", "L3_TEXT": "#ffd700",
        # Normal yazılar — beyazdan kirli beyaza
        "L4_TEXT": "#e8eaf0",  # neredeyse beyaz — en yakın
        "L5_TEXT": "#b8bccb",  # açık gri
        "L6_TEXT": "#888da0",  # orta gri
        # Alt yazılar
        "L1_SUB": "#ffbbbb", "L2_SUB": "#774444", "L3_SUB": "#665522",
        "L4_SUB": "#7a80a0", "L5_SUB": "#555a70", "L6_SUB": "#383c50",
        # Sol çizgiler
        "L2_BAR": "#cc0000", "L3_BAR": "#f59e0b",
        "L4_BAR": "#3b5a8f", "L5_BAR": "#253550", "L6_BAR": "#161e30",
        # Sayaçlar
        "L1_SAY": "#ffffff", "L2_SAY": "#ff3333", "L3_SAY": "#f59e0b",
        "L4_SAY": "#c8ccdc",  # açık
        "L5_SAY": "#888da0",  # orta
        "L6_SAY": "#555a70",  # kirli
        # Çok uzak tonlar
        "L7_BG": "#080910", "L7_TEXT": "#606478",
        "L8_BG": "#060708", "L8_TEXT": "#404455",
        "L9_BG": "#040506", "L9_TEXT": "#2a2d3a",
    },
    "acik": {
        "BG": "#f0f2f8", "PANEL": "#ffffff", "KART": "#f8f9fc",
        "TEXT": "#1a1a2e", "TEXT2": "#6677aa",
        "MAVI": "#2563eb", "YESIL": "#16a34a", "KIRMIZI": "#dc2626", "SARI": "#d97706",
        "L1_BG": "#dc2626", "L2_BG": "#fff0f0", "L3_BG": "#fffbea",
        "L4_BG": "#3a3a3a",  # en koyu gri
        "L5_BG": "#5a5a5a",  # orta koyu gri
        "L6_BG": "#7a7a7a",  # orta gri
        "L7_BG": "#9a9a9a",  # açık gri
        "L8_BG": "#bbbbbb",  # daha açık
        "L9_BG": "#dddddd",  # en açık gri
        "L1_TEXT": "#ffffff", "L2_TEXT": "#b91c1c", "L3_TEXT": "#92400e",
        "L4_TEXT": "#ffffff", "L5_TEXT": "#ffffff", "L6_TEXT": "#ffffff",
        "L1_SUB": "#fecaca", "L2_SUB": "#f87171", "L3_SUB": "#d97706",
        "L4_SUB": "#cccccc", "L5_SUB": "#dddddd", "L6_SUB": "#eeeeee",
        "L2_BAR": "#dc2626", "L3_BAR": "#d97706",
        "L4_BAR": "#222222", "L5_BAR": "#444444",
        "L6_BAR": "#666666", "L5_BAR2": "#888888", "L6_BAR2": "#aaaaaa",
        "L1_SAY": "#ffffff", "L2_SAY": "#dc2626", "L3_SAY": "#d97706",
        "L4_SAY": "#ffffff", "L5_SAY": "#eeeeee", "L6_SAY": "#dddddd",
        "L7_TEXT": "#eeeeee", "L8_TEXT": "#f5f5f5", "L9_TEXT": "#fafafa",
    }
}

def tema_yukle():
    if os.path.exists(TEMA_DOSYA):
        try:
            with open(TEMA_DOSYA, encoding="utf-8") as f:
                return json.load(f).get("tema", "koyu")
        except Exception:
            pass
    return "koyu"

def tema_kaydet(t):
    with open(TEMA_DOSYA, "w", encoding="utf-8") as f:
        json.dump({"tema": t}, f)


# ── İlk Kurulum ────────────────────────────────────────────────────────────
def kategori_secim_goster():
    T = TEMALAR["koyu"]
    secimler = {}
    p = tk.Tk()
    p.title("VedatBot Takvim — Kurulum")
    p.config(bg=T["BG"])
    p.resizable(False, False)

    alt = tk.Frame(p, bg=T["BG"])
    alt.pack(side="bottom", fill="x", pady=14)
    tk.Label(alt, text="Bu seçimi daha sonra Ayarlar'dan değiştirebilirsiniz.",
        font=("Segoe UI", 9), fg=T["TEXT2"], bg=T["BG"]).pack(pady=(0, 8))

    def kaydet():
        kayit = {k: v.get() for k, v in secimler.items()}
        kayit["edefter_tip"] = "her_ikisi"
        kayit["edefter_muk"] = "her_ikisi"
        ayarlari_kaydet(kayit)
        p.destroy()

    tk.Button(alt, text="✓   Kaydet ve Başlat",
        font=("Segoe UI", 12, "bold"), bg=T["MAVI"], fg="white",
        command=kaydet, relief="flat", padx=36, pady=10, cursor="hand2"
    ).pack()

    tk.Label(p, text="VedatBot Takvim",
        font=("Segoe UI", 18, "bold"), fg=T["MAVI"], bg=T["BG"]).pack(pady=(22, 4))
    tk.Label(p, text="Hangi beyanname türlerini takip etmek istiyorsunuz?",
        font=("Segoe UI", 10), fg=T["TEXT2"], bg=T["BG"]).pack(pady=(0, 12))

    cv = tk.Canvas(p, bg=T["BG"], highlightthickness=0)
    sb = ttk.Scrollbar(p, orient="vertical", command=cv.yview)
    kf = tk.Frame(cv, bg=T["BG"])
    cv.configure(yscrollcommand=sb.set)
    sb.pack(side="right", fill="y")
    cv.pack(side="top", fill="both", expand=True)
    cv.create_window((0, 0), window=kf, anchor="nw")
    kf.bind("<Configure>", lambda e: cv.configure(scrollregion=cv.bbox("all")))

    for key, bilgi in KATEGORILER.items():
        f = tk.Frame(kf, bg=T["KART"], pady=10)
        f.pack(fill="x", padx=22, pady=3)
        tk.Frame(f, bg=bilgi["renk"], width=4).pack(side="left", fill="y", padx=(8, 10))
        bf = tk.Frame(f, bg=T["KART"])
        bf.pack(side="left", fill="x", expand=True)
        tk.Label(bf, text=bilgi["ad"], font=("Segoe UI", 10, "bold"),
            fg=T["TEXT"], bg=T["KART"], anchor="w").pack(anchor="w")
        tk.Label(bf, text=bilgi["aciklama"], font=("Segoe UI", 9),
            fg=T["TEXT2"], bg=T["KART"], anchor="w").pack(anchor="w")
        var = tk.BooleanVar(value=bilgi["varsayilan"])
        secimler[key] = var
        tk.Checkbutton(f, variable=var, bg=T["KART"],
            activebackground=T["KART"], selectcolor=T["MAVI"], cursor="hand2"
        ).pack(side="right", padx=10)

    p.update_idletasks()
    yh = min(680, p.winfo_screenheight() - 80)
    p.geometry(f"560x{yh}+300+40")
    p.mainloop()


# ── Ana Panel ──────────────────────────────────────────────────────────────
class TakvimPanel:
    def __init__(self):
        self.tema_adi = tema_yukle()
        self.T = TEMALAR[self.tema_adi]
        self.root = tk.Tk()
        self.root.title("Beavi Takvim")
        self.root.geometry("520x700")
        self.root.config(bg=self.T["BG"])
        self.root.resizable(True, True)
        try:
            self.root.iconbitmap(os.path.join(DIZIN, "beavi.ico"))
        except Exception:
            try:
                self.root.iconbitmap(os.path.join(DIZIN, "vedatbot_icon.ico"))
            except Exception:
                pass
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"520x700+{(sw-520)//2}+{(sh-700)//2}")
        self._bugun = __import__('datetime').date.today()
        self._arayuz_olustur()
        self._takvim_yenile()
        self._saat_guncelle()
        threading.Thread(target=self._alarm_dongusu, daemon=True).start()
        self._periyodik_kontrol()

    def _arayuz_olustur(self):
        T = self.T
        baslik = tk.Frame(self.root, bg=T["PANEL"], pady=10)
        baslik.pack(fill="x")

        # Logo — beavi.ico PNG olarak yukle
        try:
            from PIL import Image, ImageTk
            _logo_img = Image.open(os.path.join(DIZIN, "beavi.ico")).resize((48, 48), Image.LANCZOS)
            self._logo_photo = ImageTk.PhotoImage(_logo_img)
            logo_canvas = tk.Canvas(baslik, width=48, height=48, bg=T["PANEL"],
                                    highlightthickness=0)
            logo_canvas.pack(side="left", padx=(14, 0))
            logo_canvas.create_image(24, 24, image=self._logo_photo)
        except Exception:
            logo_canvas = tk.Canvas(baslik, width=48, height=48, bg=T["PANEL"],
                                    highlightthickness=0)
            logo_canvas.pack(side="left", padx=(14, 0))
            logo_canvas.create_oval(2, 2, 46, 46, fill="#1E2761", outline="#F59E0B", width=2)
            logo_canvas.create_rectangle(13, 10, 18, 38, fill="white", outline="white")
            logo_canvas.create_arc(17, 10, 37, 26, start=270, extent=180,
                                   outline="white", style="arc", width=4)
            logo_canvas.create_arc(17, 22, 39, 38, start=270, extent=180,
                                   outline="#F59E0B", style="arc", width=4)

        # Beavi yazısı
        isim = tk.Frame(baslik, bg=T["PANEL"])
        isim.pack(side="left", padx=(8, 0))
        tk.Label(isim, text="Beavi", font=("Segoe UI", 18, "bold"),
            fg="#1E2761" if self.tema_adi == "acik" else "#FFFFFF",
            bg=T["PANEL"]).pack(anchor="w")
        # Altın çizgi
        tk.Frame(isim, bg="#F59E0B", height=3).pack(fill="x", pady=(0, 2))
        tk.Label(isim, text="by VedatBot", font=("Segoe UI", 8),
            fg=T["TEXT2"], bg=T["PANEL"]).pack(anchor="w")
        self.saat_label = tk.Label(baslik, text="", font=("Segoe UI", 9),
            fg=T["TEXT2"], bg=T["PANEL"])
        self.saat_label.pack(side="right", padx=(0, 14))
        tk.Button(baslik, text="☀ / ☾", font=("Segoe UI", 9),
            bg=T["KART"], fg=T["TEXT2"], command=self._tema_degistir,
            relief="flat", padx=8, pady=3, cursor="hand2"
        ).pack(side="right", padx=2)
        tk.Button(baslik, text="Ayarlar", font=("Segoe UI", 9),
            bg=T["KART"], fg=T["TEXT2"], command=self._ayarlar_ac,
            relief="flat", padx=8, pady=3, cursor="hand2"
        ).pack(side="right", padx=2)

        ozet = tk.Frame(self.root, bg=T["BG"])
        ozet.pack(fill="x", padx=14, pady=10)
        self.acil_var = tk.StringVar(value="0")
        self.ay_var = tk.StringVar(value="0")
        self.sonraki_var = tk.StringVar(value="-")
        for lbl, var, renk in [
            ("Acil (3 gün)", self.acil_var, T["KIRMIZI"]),
            ("Bu ay", self.ay_var, T["MAVI"]),
            ("Sonraki", self.sonraki_var, T["YESIL"]),
        ]:
            k = tk.Frame(ozet, bg=T["KART"], pady=10)
            k.pack(side="left", fill="both", expand=True, padx=3)
            tk.Label(k, text=lbl, font=("Segoe UI", 9), fg=T["TEXT2"], bg=T["KART"]).pack()
            tk.Label(k, textvariable=var, font=("Segoe UI", 16, "bold"),
                fg=renk, bg=T["KART"]).pack()

        b2 = tk.Frame(self.root, bg=T["BG"])
        b2.pack(fill="x", padx=14, pady=(0, 4))
        tk.Label(b2, text="YAKLAŞAN BEYANNAMELER", font=("Segoe UI", 9),
            fg=T["TEXT2"], bg=T["BG"]).pack(side="left")
        tk.Button(b2, text="↻ Yenile", font=("Segoe UI", 8),
            bg=T["KART"], fg=T["TEXT2"], command=self._takvim_yenile,
            relief="flat", padx=8, pady=2, cursor="hand2"
        ).pack(side="right")

        cf = tk.Frame(self.root, bg=T["BG"])
        cf.pack(fill="both", expand=True, padx=14, pady=(0, 6))
        self.canvas = tk.Canvas(cf, bg=T["BG"], highlightthickness=0)
        sb = ttk.Scrollbar(cf, orient="vertical", command=self.canvas.yview)
        self.liste_frame = tk.Frame(self.canvas, bg=T["BG"])
        self.canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self._liste_win = self.canvas.create_window((0, 0), window=self.liste_frame, anchor="nw")
        self.liste_frame.bind("<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        # Canvas genişliği değişince liste_frame de uzasın
        self.canvas.bind("<Configure>",
            lambda e: self.canvas.itemconfig(self._liste_win, width=e.width))

        tk.Label(self.root, text="Powered by VedatBot — Mali Müşavirlik Asistanı",
            font=("Segoe UI", 8),
            fg=T["TEXT2"] if self.tema_adi == "acik" else "#222233",
            bg=T["BG"]).pack(pady=(0, 6))

    def _saat_guncelle(self):
        self.saat_label.config(text=datetime.now().strftime("%d.%m.%Y  %H:%M"))
        self.root.after(60000, self._saat_guncelle)

    def _periyodik_kontrol(self):
        import datetime
        bugun=datetime.date.today()
        if bugun!=self._bugun:
            self._bugun=bugun
            self._takvim_yenile()
        self.root.after(60000,self._periyodik_kontrol)

    def _takvim_yenile(self):
        T = self.T
        for w in self.liste_frame.winfo_children():
            w.destroy()
        beyannameler = cache_veya_hesapla()
        if not beyannameler:
            tk.Label(self.liste_frame, text="Yaklaşan beyanname yok.",
                font=("Segoe UI", 10), fg=T["TEXT2"], bg=T["BG"]).pack(pady=20)
            return
        acil = sum(1 for b in beyannameler if b["kalan_gun"] <= 3)
        ay30 = sum(1 for b in beyannameler if b["kalan_gun"] <= 30)
        ilk = beyannameler[0]
        self.acil_var.set(str(acil))
        self.ay_var.set(str(ay30))
        self.sonraki_var.set(ilk["tarih"].strftime("%d %b"))
        for b in beyannameler:
            self._kart_ciz(b, T)

    def _kart_ciz(self, b, T):
        kalan = b["kalan_gun"]
        ts = b["tarih"].strftime("%d.%m.%Y")
        ga = b["tarih"].strftime("%A")
        ad_buyuk = b["tur"].upper()
        ad_normal = b["tur"]

        if kalan == 0:
            k = tk.Frame(self.liste_frame, bg=T["L1_BG"], pady=16)
            k.pack(fill="x", pady=5)
            ust = tk.Frame(k, bg=T["L1_BG"])
            ust.pack(fill="x", padx=16)
            tk.Label(ust, text="🔴", font=("Segoe UI", 26), bg=T["L1_BG"]
            ).pack(side="left", padx=(0, 10))
            ic = tk.Frame(ust, bg=T["L1_BG"])
            ic.pack(side="left")
            tk.Label(ic, text="⚠  BUGÜN SON GÜN!",
                font=("Segoe UI", 9, "bold"), fg=T["L1_SUB"], bg=T["L1_BG"]
            ).pack(anchor="w")
            tk.Label(ic, text=ad_buyuk,
                font=("Segoe UI", 13, "bold"), fg=T["L1_TEXT"], bg=T["L1_BG"]
            ).pack(anchor="w")
            tk.Label(ic, text=f"{ts}  —  HEMEN BEYANNAMEYI VER!",
                font=("Segoe UI", 9, "bold"), fg=T["L1_SUB"], bg=T["L1_BG"]
            ).pack(anchor="w")

        elif kalan <= 3:
            k = tk.Frame(self.liste_frame, bg=T["L2_BG"], pady=14)
            k.pack(fill="x", pady=4)
            tk.Frame(k, bg=T["L2_BAR"], width=6).pack(side="left", fill="y")
            ic = tk.Frame(k, bg=T["L2_BG"])
            ic.pack(side="left", fill="x", expand=True, padx=12)
            tk.Label(ic, text="🚨  ACİL",
                font=("Segoe UI", 9, "bold"), fg=T["L2_SAY"], bg=T["L2_BG"]
            ).pack(anchor="w")
            tk.Label(ic, text=ad_buyuk,
                font=("Segoe UI", 12, "bold"), fg=T["L2_TEXT"], bg=T["L2_BG"]
            ).pack(anchor="w")
            tk.Label(ic, text=f"Son gün: {ts} ({ga})",
                font=("Segoe UI", 9), fg=T["L2_SUB"], bg=T["L2_BG"]
            ).pack(anchor="w")
            sag = tk.Frame(k, bg=T["L2_BG"])
            sag.pack(side="right", padx=14)
            tk.Label(sag, text=str(kalan),
                font=("Segoe UI", 30, "bold"), fg=T["L2_SAY"], bg=T["L2_BG"]
            ).pack()
            tk.Label(sag, text="GÜN",
                font=("Segoe UI", 8, "bold"), fg=T["L2_SAY"], bg=T["L2_BG"]
            ).pack()

        elif kalan <= 7:
            k = tk.Frame(self.liste_frame, bg=T["L3_BG"], pady=12)
            k.pack(fill="x", pady=3)
            tk.Frame(k, bg=T["L3_BAR"], width=5).pack(side="left", fill="y")
            ic = tk.Frame(k, bg=T["L3_BG"])
            ic.pack(side="left", fill="x", expand=True, padx=12)
            tk.Label(ic, text="⚡  YAKLAŞIYOR",
                font=("Segoe UI", 8, "bold"), fg=T["L3_SAY"], bg=T["L3_BG"]
            ).pack(anchor="w")
            tk.Label(ic, text=ad_normal,
                font=("Segoe UI", 11, "bold"), fg=T["L3_TEXT"], bg=T["L3_BG"]
            ).pack(anchor="w")
            tk.Label(ic, text=f"Son gün: {ts} ({ga})",
                font=("Segoe UI", 9), fg=T["L3_SUB"], bg=T["L3_BG"]
            ).pack(anchor="w")
            sag = tk.Frame(k, bg=T["L3_BG"])
            sag.pack(side="right", padx=12)
            tk.Label(sag, text=str(kalan),
                font=("Segoe UI", 22, "bold"), fg=T["L3_SAY"], bg=T["L3_BG"]
            ).pack()
            tk.Label(sag, text="gün",
                font=("Segoe UI", 8), fg=T["L3_SAY"], bg=T["L3_BG"]
            ).pack()

        elif kalan <= 14:
            # Ton 1 — en koyu gri
            bg = T["L4_BG"]
            k = tk.Frame(self.liste_frame, bg=bg, pady=10)
            k.pack(fill="x", pady=1, padx=0)
            ic = tk.Frame(k, bg=bg)
            ic.pack(side="left", fill="x", expand=True, padx=14)
            tk.Label(ic, text=ad_normal,
                font=("Segoe UI", 10, "bold"), fg=T["L4_TEXT"], bg=bg
            ).pack(anchor="w")
            tk.Label(ic, text=f"{ts} ({ga})",
                font=("Segoe UI", 9), fg=T["L4_SUB"], bg=bg
            ).pack(anchor="w")
            tk.Label(k, text=f"{kalan} gün",
                font=("Segoe UI", 10, "bold"), fg=T["L4_SAY"], bg=bg
            ).pack(side="right", padx=14)

        elif kalan <= 21:
            # Ton 2 — orta koyu gri
            bg = T["L5_BG"]
            k = tk.Frame(self.liste_frame, bg=bg, pady=9)
            k.pack(fill="x", pady=1, padx=0)
            ic = tk.Frame(k, bg=bg)
            ic.pack(side="left", fill="x", expand=True, padx=14)
            tk.Label(ic, text=ad_normal,
                font=("Segoe UI", 10, "bold"), fg=T["L5_TEXT"], bg=bg
            ).pack(anchor="w")
            tk.Label(ic, text=f"{ts}",
                font=("Segoe UI", 9), fg=T["L5_SUB"], bg=bg
            ).pack(anchor="w")
            tk.Label(k, text=f"{kalan} gün",
                font=("Segoe UI", 9), fg=T["L5_SAY"], bg=bg
            ).pack(side="right", padx=14)

        elif kalan <= 30:
            # Ton 3 — orta gri
            bg = T["L6_BG"]
            k = tk.Frame(self.liste_frame, bg=bg, pady=8)
            k.pack(fill="x", pady=1, padx=0)
            ic = tk.Frame(k, bg=bg)
            ic.pack(side="left", fill="x", expand=True, padx=14)
            tk.Label(ic, text=ad_normal,
                font=("Segoe UI", 9), fg=T["L6_TEXT"], bg=bg
            ).pack(anchor="w")
            tk.Label(k, text=f"{kalan}g",
                font=("Segoe UI", 9), fg=T["L6_SAY"], bg=bg
            ).pack(side="right", padx=14)

        elif kalan <= 45:
            # Ton 4 — açık gri
            bg = T.get("L7_BG", T["L6_BG"])
            txt = T.get("L7_TEXT", T["L6_TEXT"]) if "L7_TEXT" in T else T["L6_TEXT"]
            k = tk.Frame(self.liste_frame, bg=bg, pady=8)
            k.pack(fill="x", pady=1, padx=0)
            ic = tk.Frame(k, bg=bg)
            ic.pack(side="left", fill="x", expand=True, padx=14)
            tk.Label(ic, text=ad_normal,
                font=("Segoe UI", 9), fg=txt, bg=bg
            ).pack(anchor="w")
            tk.Label(k, text=f"{kalan}g",
                font=("Segoe UI", 8), fg=txt, bg=bg
            ).pack(side="right", padx=14)

        elif kalan <= 60:
            # Ton 5 — daha açık gri
            bg = T.get("L8_BG", T["L6_BG"])
            txt = T.get("L8_TEXT", T["L6_TEXT"]) if "L8_TEXT" in T else T["L6_TEXT"]
            k = tk.Frame(self.liste_frame, bg=bg, pady=7)
            k.pack(fill="x", pady=1, padx=0)
            ic = tk.Frame(k, bg=bg)
            ic.pack(side="left", fill="x", expand=True, padx=14)
            tk.Label(ic, text=ad_normal,
                font=("Segoe UI", 9), fg=txt, bg=bg
            ).pack(anchor="w")
            tk.Label(k, text=f"{kalan}g",
                font=("Segoe UI", 8), fg=txt, bg=bg
            ).pack(side="right", padx=14)

        else:
            # Ton 6 — en açık gri, neredeyse arka plan
            bg = T.get("L9_BG", T["L6_BG"])
            txt = T.get("L9_TEXT", T["L6_TEXT"]) if "L9_TEXT" in T else T["L6_TEXT"]
            k = tk.Frame(self.liste_frame, bg=bg, pady=7)
            k.pack(fill="x", pady=1, padx=0)
            ic = tk.Frame(k, bg=bg)
            ic.pack(side="left", fill="x", expand=True, padx=14)
            tk.Label(ic, text=ad_normal,
                font=("Segoe UI", 9), fg=txt, bg=bg
            ).pack(anchor="w")
            tk.Label(k, text=f"{kalan}g",
                font=("Segoe UI", 8), fg=txt, bg=bg
            ).pack(side="right", padx=14)

    def _tema_degistir(self):
        self.tema_adi = "acik" if self.tema_adi == "koyu" else "koyu"
        tema_kaydet(self.tema_adi)
        self.root.destroy()
        app = TakvimPanel()
        app.calistir()

    def _alarm_dongusu(self):
        while True:
            bugun_son = bugun_son_gunler()
            if bugun_son:
                self.root.after(0, lambda b=bugun_son: self._alarm_goster(b))
            import datetime as _dt
            simdi = _dt.datetime.now()
            yarin = simdi.replace(hour=8, minute=0, second=0, microsecond=0)
            if simdi.hour >= 8:
                from datetime import timedelta
                yarin += timedelta(days=1)
            time.sleep(max((yarin - simdi).total_seconds(), 3600))

    def _alarm_goster(self, beyannameler):
        global alarm_aktif
        alarm_aktif = True
        alarm = tk.Toplevel(self.root)
        alarm.title("BEYANNAME SON GÜN!")
        alarm.attributes("-topmost", True)
        alarm.geometry("680x400+200+150")
        alarm.config(bg="#002366")
        alarm.resizable(False, False)
        tur_metni = "\n".join(f"• {b['tur']}" for b in beyannameler)
        lbl = tk.Label(alarm,
            text=f"🔴  SON GÜN!\n\n{date.today().strftime('%d.%m.%Y')}\n\n{tur_metni}\n\nBUGÜN BEYANNAMEYI VER!",
            font=("Segoe UI", 14, "bold"), fg="white", bg="#002366", justify="center")
        lbl.pack(expand=True, fill="both", padx=20, pady=20)

        def yanip_son():
            if not alarm_aktif: return
            c = alarm.cget("bg")
            yeni = "#002366" if c != "#002366" else "#FFD700"
            fg = "white" if yeni == "#002366" else "#002366"
            alarm.config(bg=yeni); lbl.config(bg=yeni, fg=fg)
            alarm.after(600, yanip_son)

        def kapat():
            global alarm_aktif
            alarm_aktif = False
            alarm.destroy()

        tk.Button(alarm, text="TAMAM KAPAT", font=("Segoe UI", 12, "bold"),
            bg="#22aa44", fg="white", command=kapat,
            relief="flat", padx=20, pady=8).pack(pady=10)
        threading.Thread(target=self._ses_cal, daemon=True).start()
        yanip_son()
        alarm.protocol("WM_DELETE_WINDOW", kapat)

    def _ses_cal(self):
        while alarm_aktif:
            winsound.Beep(1000, 400); time.sleep(0.2)
            winsound.Beep(1500, 400); time.sleep(0.2)
            winsound.Beep(2000, 400); time.sleep(4)

    def _ayarlar_ac(self):
        T = self.T
        p = tk.Toplevel(self.root)
        p.title("Kategori Ayarları")
        p.attributes("-topmost", True)
        p.geometry("520x700+250+60")
        p.config(bg=T["BG"])
        p.resizable(True, True)
        tk.Label(p, text="Takip Edilecek Kategoriler",
            font=("Segoe UI", 13, "bold"), fg=T["TEXT"], bg=T["BG"]
        ).pack(pady=(20, 4))
        tk.Label(p, text="Hepsi varsayılan olarak seçili — dilediğinizi kaldırabilirsiniz.",
            font=("Segoe UI", 9), fg=T["TEXT2"], bg=T["BG"]
        ).pack(pady=(0, 10))
        mevcut = ayarlari_yukle()
        secimler = {}

        # Kaydirilebilir liste
        container = tk.Frame(p, bg=T["BG"])
        container.pack(fill="both", expand=True, padx=0, pady=0)
        canvas2 = tk.Canvas(container, bg=T["BG"], highlightthickness=0)
        sb2 = tk.Scrollbar(container, orient="vertical", command=canvas2.yview)
        liste2 = tk.Frame(canvas2, bg=T["BG"])
        canvas2.configure(yscrollcommand=sb2.set)
        sb2.pack(side="right", fill="y")
        canvas2.pack(side="left", fill="both", expand=True)
        win2 = canvas2.create_window((0, 0), window=liste2, anchor="nw")
        liste2.bind("<Configure>", lambda e: canvas2.configure(scrollregion=canvas2.bbox("all")))
        canvas2.bind("<Configure>", lambda e: canvas2.itemconfig(win2, width=e.width))
        canvas2.bind_all("<MouseWheel>", lambda e: canvas2.yview_scroll(int(-1*(e.delta/120)), "units"))

        for key, bilgi in KATEGORILER.items():
            f = tk.Frame(liste2, bg=T["KART"], pady=8)
            f.pack(fill="x", padx=20, pady=3)
            tk.Frame(f, bg=bilgi["renk"], width=4).pack(side="left", fill="y", padx=(8, 10))
            bf = tk.Frame(f, bg=T["KART"])
            bf.pack(side="left", fill="x", expand=True)
            tk.Label(bf, text=bilgi["ad"], font=("Segoe UI", 10),
                fg=T["TEXT"], bg=T["KART"], anchor="w"
            ).pack(anchor="w")
            tk.Label(bf, text=bilgi["aciklama"], font=("Segoe UI", 8),
                fg=T["TEXT2"], bg=T["KART"], anchor="w"
            ).pack(anchor="w")
            var = tk.BooleanVar(value=mevcut.get(key, bilgi["varsayilan"]))
            secimler[key] = var
            tk.Checkbutton(f, variable=var, bg=T["KART"],
                selectcolor=T["MAVI"], cursor="hand2",
                activebackground=T["KART"]
            ).pack(side="right", padx=10)

        # ── e-Defter Ek Ayarlar ──────────────────────────────────────────
        edf_frame = tk.Frame(liste2, bg=T["PANEL"], pady=10)
        edf_frame.pack(fill="x", padx=20, pady=(6, 3))
        tk.Label(edf_frame, text="e-Defter Berat — Detay Ayarları",
            font=("Segoe UI", 10, "bold"), fg=T["SARI"], bg=T["PANEL"]
        ).pack(anchor="w", padx=10, pady=(4, 6))

        # Sıklık
        tk.Label(edf_frame, text="Yükleme Sıklığı:",
            font=("Segoe UI", 9), fg=T["TEXT2"], bg=T["PANEL"]
        ).pack(anchor="w", padx=10)
        edefter_tip_var = tk.StringVar(value=mevcut.get("edefter_tip", "her_ikisi"))
        tip_f = tk.Frame(edf_frame, bg=T["PANEL"])
        tip_f.pack(fill="x", padx=10, pady=2)
        for val, lbl in [("aylik", "Aylık"), ("yillik", "Yıllık"), ("her_ikisi", "Her İkisi")]:
            tk.Radiobutton(tip_f, text=lbl, variable=edefter_tip_var, value=val,
                bg=T["PANEL"], fg=T["TEXT"], selectcolor=T["SARI"],
                activebackground=T["PANEL"], font=("Segoe UI", 9), cursor="hand2"
            ).pack(side="left", padx=6)

        # Mükellef Türü
        tk.Label(edf_frame, text="Mükellef Türü:",
            font=("Segoe UI", 9), fg=T["TEXT2"], bg=T["PANEL"]
        ).pack(anchor="w", padx=10, pady=(6, 0))
        edefter_muk_var = tk.StringVar(value=mevcut.get("edefter_muk", "her_ikisi"))
        muk_f = tk.Frame(edf_frame, bg=T["PANEL"])
        muk_f.pack(fill="x", padx=10, pady=2)
        for val, lbl in [("gv", "GV Mükellefi (10. gün)"), ("kv", "KV Mükellefi (14. gün)"), ("her_ikisi", "Her İkisi")]:
            tk.Radiobutton(muk_f, text=lbl, variable=edefter_muk_var, value=val,
                bg=T["PANEL"], fg=T["TEXT"], selectcolor=T["SARI"],
                activebackground=T["PANEL"], font=("Segoe UI", 9), cursor="hand2"
            ).pack(side="left", padx=6)

        def kaydet():
            kayit = {k: v.get() for k, v in secimler.items()}
            kayit["edefter_tip"] = edefter_tip_var.get()
            kayit["edefter_muk"] = edefter_muk_var.get()
            ayarlari_kaydet(kayit)
            p.destroy()
            self._takvim_yenile()

        tk.Button(p, text="Kaydet", font=("Segoe UI", 11, "bold"),
            bg=T["MAVI"], fg="white", command=kaydet,
            relief="flat", padx=20, pady=8, cursor="hand2"
        ).pack(pady=16)

    def calistir(self):
        self.root.mainloop()


# ── Başlat ─────────────────────────────────────────────────────────────────

def lisans_ekrani_goster():
    """Lisans aktivasyon ekranı. Geçerliyse True döner."""
    try:
        from beavi_lisans import lisans_kontrol, anahtar_dogrula, lisans_kaydet
    except ImportError:
        return True  # lisans modülü yoksa geç

    durum, gun_kalan = lisans_kontrol()
    if durum == "gecerli":
        if gun_kalan <= 30:
            # Yenileme uyarısı — ayrı pencere açmadan
            import tkinter.messagebox as _mb
            _mb.showwarning("Lisans Yakında Bitiyor",
                f"Beavi lisansiniz {gun_kalan} gun icinde sona erecek.\n"
                "Yenilemek icin VedatBot ile iletisime gecin.")
        return True

    # Lisans yok veya süresi doldu
    sonuc = [False]

    _root_gizli = tk.Tk()
    _root_gizli.withdraw()
    _root_gizli.geometry("0x0+0+0")
    _root_gizli.attributes("-alpha", 0)
    _root_gizli.overrideredirect(True)
    pencere = tk.Toplevel(_root_gizli)
    pencere.title("Beavi — Lisans Aktivasyonu")
    pencere.geometry("460x380")
    pencere.resizable(False, False)
    pencere.configure(bg="#1E2761")
    pencere.eval("tk::PlaceWindow . center")

    tk.Label(pencere, text="Beavi", font=("Segoe UI", 28, "bold"),
             fg="#F59E0B", bg="#1E2761").pack(pady=(24, 0))
    tk.Label(pencere, text="Takvim & Beyanname Takip",
             font=("Segoe UI", 11), fg="white", bg="#1E2761").pack()

    if durum == "suresi_doldu":
        mesaj = "Lisansınızın süresi doldu.\nYenilemek için VedatBot ile iletişime geçin."
        renk = "#FF6B6B"
    else:
        mesaj = "Bu ürünü kullanmak için lisans anahtarı gereklidir."
        renk = "#93C5FD"

    tk.Label(pencere, text=mesaj, font=("Segoe UI", 10),
             fg=renk, bg="#1E2761", wraplength=400, justify="center").pack(pady=12)

    frame = tk.Frame(pencere, bg="#0F1C4A", padx=20, pady=16)
    frame.pack(fill="x", padx=20)

    tk.Label(frame, text="Lisans Anahtarı:", font=("Segoe UI", 10),
             fg="white", bg="#0F1C4A", anchor="w").pack(fill="x")
    anahtar_var = tk.StringVar()
    anahtar_entry = tk.Entry(frame, textvariable=anahtar_var,
                             font=("Consolas", 13, "bold"),
                             bg="#1E2761", fg="#F59E0B", insertbackground="white",
                             relief="flat", bd=8, justify="center")
    anahtar_entry.pack(fill="x", pady=(4, 0))
    anahtar_entry.insert(0, "BEAVI-XXXX-XXXX-XXXX")
    anahtar_entry.bind("<FocusIn>", lambda e: anahtar_entry.delete(0, "end") if anahtar_var.get() == "BEAVI-XXXX-XXXX-XXXX" else None)

    hata_var = tk.StringVar()
    tk.Label(frame, textvariable=hata_var, font=("Segoe UI", 9),
             fg="#FF6B6B", bg="#0F1C4A").pack(pady=(4, 0))

    def aktive_et():
        anahtar = anahtar_var.get().strip()
        try:
            from beavi_lisans import anahtar_dogrula, lisans_kaydet
            gecerli, gun_kalan = anahtar_dogrula(anahtar)
            if gecerli:
                lisans_kaydet(anahtar, gun_kalan)
                sonuc[0] = True
                _root_gizli.destroy()
            else:
                hata_var.set("Geçersiz anahtar. Lütfen kontrol edin.")
        except Exception as e:
            hata_var.set(f"Hata: {e}")

    tk.Button(frame, text="Aktivasyon Yap", font=("Segoe UI", 11, "bold"),
              bg="#F59E0B", fg="#1E2761", relief="flat", pady=8,
              cursor="hand2", command=aktive_et).pack(fill="x", pady=(12, 0))

    tk.Label(pencere, text="Lisans almak için: WhatsApp +90 5XX XXX XX XX",
             font=("Segoe UI", 9), fg="#6B7280", bg="#1E2761").pack(pady=(12, 0))
    tk.Label(pencere, text="Powered by VedatBot — Mali Müşavirlik Asistanı",
             font=("Segoe UI", 8), fg="#374151", bg="#1E2761").pack(pady=(4, 0))

    def kapat():
        sonuc[0] = False
        try: _root_gizli.destroy()
        except: pass

    pencere.protocol("WM_DELETE_WINDOW", kapat)
    pencere.lift()
    pencere.focus_force()
    _root_gizli.mainloop()
    try: _root_gizli.destroy()
    except: pass
    return sonuc[0]

if __name__ == "__main__":
    if not lisans_ekrani_goster():
        sys.exit(0)
    if not ilk_kurulum_yapildi_mi():
        kategori_secim_goster()
    app = TakvimPanel()
    app.calistir()

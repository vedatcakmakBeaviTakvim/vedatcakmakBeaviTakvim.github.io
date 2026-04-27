#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VedatBot — Vergi + SGK Takvim Güncelleme Modülü

- GİB (muhasebetr.com) ve SGK'dan tarihleri çeker
- İnternetsiz çalışır — son başarılı çekimi takvim_cache.json'a kaydeder
- İnternet gelince karşılaştırır, değişiklik varsa uyarı verir
- beyanname_takvim.py ile birlikte çalışır (tek kaynak prensibi)
"""

import json
import os
import re
import urllib.request
import urllib.error
from datetime import datetime, date, timedelta
from html.parser import HTMLParser

DIZIN = os.path.dirname(os.path.abspath(__file__))
CACHE_DOSYA = os.path.join(DIZIN, "takvim_cache.json")
DEGISIKLIK_DOSYA = os.path.join(DIZIN, "takvim_degisiklik.json")

# ── Kaynak URL'ler ──────────────────────────────────────────────────────────
GIB_URL = "https://www.muhasebetr.com/vergi-takvimi"
SGK_URL = "https://www.sgk.gov.tr/wps/portal/sgk/tr/calisan/sgk_prim_odeme_takvimi"

# ── Kritik beyanname anahtar kelimeleri ────────────────────────────────────
KRITIK = [
    "KDV", "Katma Değer", "Muhtasar", "Prim Hizmet",
    "Geçici Vergi", "Gelir Vergisi", "Kurumlar Vergisi",
    "SGK", "Bağ-Kur", "e-Defter",
]

# ── 2026 Dahili Yedek Takvim (GİB + SGK) ──────────────────────────────────
YEDEK_TAKVIM_2026 = [
    # MART
    ("2026-03-26", "Muhtasar ve Prim Hizmet Beyannamesi (Şubat 2026)", "GIB"),
    ("2026-03-30", "KDV-1 Beyannamesi (Şubat 2026)", "GIB"),
    ("2026-03-31", "Yıllık Gelir Vergisi Beyannamesi (2025 yılı)", "GIB"),
    ("2026-03-31", "SGK Primi 4/a (Şubat 2026)", "SGK"),
    ("2026-03-31", "Bağ-Kur Primi 4/b (Şubat 2026)", "SGK"),
    # NİSAN
    ("2026-04-27", "Muhtasar ve Prim Hizmet Beyannamesi (Mart 2026)", "GIB"),
    ("2026-04-28", "KDV-1 Beyannamesi (Mart 2026)", "GIB"),
    ("2026-04-30", "Kurumlar Vergisi Beyannamesi (2025 yılı)", "GIB"),
    ("2026-04-30", "SGK Primi 4/a (Mart 2026)", "SGK"),
    ("2026-04-30", "Bağ-Kur Primi 4/b (Mart 2026)", "SGK"),
    # MAYIS
    ("2026-05-18", "Geçici Vergi Beyannamesi (2026 I. Dönem)", "GIB"),
    ("2026-05-26", "Muhtasar ve Prim Hizmet Beyannamesi (Nisan 2026)", "GIB"),
    ("2026-05-29", "KDV-1 Beyannamesi (Nisan 2026)", "GIB"),
    ("2026-05-29", "SGK Primi 4/a (Nisan 2026)", "SGK"),
    ("2026-05-29", "Bağ-Kur Primi 4/b (Nisan 2026)", "SGK"),
    # HAZİRAN
    ("2026-06-26", "Muhtasar ve Prim Hizmet Beyannamesi (Mayıs 2026)", "GIB"),
    ("2026-06-29", "KDV-1 Beyannamesi (Mayıs 2026)", "GIB"),
    ("2026-06-30", "SGK Primi 4/a (Mayıs 2026)", "SGK"),
    ("2026-06-30", "Bağ-Kur Primi 4/b (Mayıs 2026)", "SGK"),
    # TEMMUZ
    ("2026-07-27", "Muhtasar ve Prim Hizmet Beyannamesi (Haziran 2026)", "GIB"),
    ("2026-07-28", "KDV-1 Beyannamesi (Haziran 2026)", "GIB"),
    ("2026-07-31", "SGK Primi 4/a (Haziran 2026)", "SGK"),
    ("2026-07-31", "Bağ-Kur Primi 4/b (Haziran 2026)", "SGK"),
    ("2026-07-31", "Yıllık Gelir Vergisi 2. Taksit Ödemesi", "GIB"),
    # AĞUSTOS
    ("2026-08-17", "Geçici Vergi Beyannamesi (2026 II. Dönem)", "GIB"),
    ("2026-08-26", "Muhtasar ve Prim Hizmet Beyannamesi (Temmuz 2026)", "GIB"),
    ("2026-08-28", "KDV-1 Beyannamesi (Temmuz 2026)", "GIB"),
    ("2026-08-31", "SGK Primi 4/a (Temmuz 2026)", "SGK"),
    ("2026-08-31", "Bağ-Kur Primi 4/b (Temmuz 2026)", "SGK"),
    # EYLÜL
    ("2026-09-28", "Muhtasar ve Prim Hizmet Beyannamesi (Ağustos 2026)", "GIB"),
    ("2026-09-28", "KDV-1 Beyannamesi (Ağustos 2026)", "GIB"),
    ("2026-09-30", "SGK Primi 4/a (Ağustos 2026)", "SGK"),
    ("2026-09-30", "Bağ-Kur Primi 4/b (Ağustos 2026)", "SGK"),
    # EKİM
    ("2026-10-26", "Muhtasar ve Prim Hizmet Beyannamesi (Eylül 2026)", "GIB"),
    ("2026-10-28", "KDV-1 Beyannamesi (Eylül 2026)", "GIB"),
    ("2026-10-30", "SGK Primi 4/a (Eylül 2026)", "SGK"),
    ("2026-10-30", "Bağ-Kur Primi 4/b (Eylül 2026)", "SGK"),
    # KASIM
    ("2026-11-17", "Geçici Vergi Beyannamesi (2026 III. Dönem)", "GIB"),
    ("2026-11-26", "Muhtasar ve Prim Hizmet Beyannamesi (Ekim 2026)", "GIB"),
    ("2026-11-30", "KDV-1 Beyannamesi (Ekim 2026)", "GIB"),
    ("2026-11-30", "SGK Primi 4/a (Ekim 2026)", "SGK"),
    ("2026-11-30", "Bağ-Kur Primi 4/b (Ekim 2026)", "SGK"),
    # ARALIK
    ("2026-12-28", "Muhtasar ve Prim Hizmet Beyannamesi (Kasım 2026)", "GIB"),
    ("2026-12-28", "KDV-1 Beyannamesi (Kasım 2026)", "GIB"),
    ("2026-12-31", "SGK Primi 4/a (Kasım 2026)", "SGK"),
    ("2026-12-31", "Bağ-Kur Primi 4/b (Kasım 2026)", "SGK"),
]


# ── HTML Parser: muhasebetr.com ────────────────────────────────────────────
class MuhasebetrParser(HTMLParser):
    """muhasebetr.com/vergi-takvimi sayfasından tarih+beyanname çeker."""

    def __init__(self):
        super().__init__()
        self.girdiler = []
        self._in_table = False
        self._in_tr = False
        self._cells = []
        self._current_cell = ""
        self._in_td = False

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self._in_table = True
        if self._in_table and tag == "tr":
            self._in_tr = True
            self._cells = []
        if self._in_tr and tag in ("td", "th"):
            self._in_td = True
            self._current_cell = ""

    def handle_endtag(self, tag):
        if tag == "table":
            self._in_table = False
        if self._in_table and tag == "tr":
            self._in_tr = False
            self._isle_satir(self._cells)
        if self._in_tr and tag in ("td", "th"):
            self._in_td = False
            self._cells.append(self._current_cell.strip())

    def handle_data(self, data):
        if self._in_td:
            self._current_cell += data

    def _isle_satir(self, cells):
        if len(cells) < 2:
            return
        # Hücrelerde tarih ara (GG.AA.YYYY veya YYYY-AA-GG)
        tarih = None
        aciklama = ""
        for cell in cells:
            cell = cell.strip()
            m = re.search(r'(\d{2})\.(\d{2})\.(\d{4})', cell)
            if m:
                try:
                    tarih = date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
                except ValueError:
                    pass
            elif cell and not tarih:
                aciklama = cell
            elif cell and tarih:
                aciklama = cell

        if tarih and aciklama:
            # Sadece kritik beyannameleri al
            if any(k.lower() in aciklama.lower() for k in KRITIK):
                self.girdiler.append({
                    "tarih": tarih.isoformat(),
                    "tur": aciklama,
                    "kaynak": "GIB"
                })


# ── İnternet Çekme ─────────────────────────────────────────────────────────
def _url_cek(url, timeout=10):
    req = urllib.request.Request(url, headers={"User-Agent": "VedatBot/2.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="ignore")


def gib_cek():
    """GİB takvimini web'den çek. Başarısız olursa None döner."""
    try:
        html = _url_cek(GIB_URL)
        parser = MuhasebetrParser()
        parser.feed(html)
        if len(parser.girdiler) >= 5:  # Makul sayıda kayıt geldiyse güven
            print(f"[GİB] {len(parser.girdiler)} kayıt çekildi.")
            return parser.girdiler
        else:
            print(f"[GİB] Sayfa parse edilemedi, yedek kullanılıyor.")
            return None
    except Exception as e:
        print(f"[GİB] Bağlantı hatası: {e}")
        return None


def sgk_cek():
    """SGK'dan prim tarihlerini çek. Başarısız olursa None döner."""
    # SGK sayfası JavaScript ağırlıklı, doğrudan parse zor.
    # Şimdilik yedek veriden SGK satirlarini döndür.
    try:
        html = _url_cek(SGK_URL, timeout=8)
        # Basit tarih + "prim" kelimesi arama
        girdiler = []
        tarihler = re.findall(r'(\d{2})\.(\d{2})\.(\d{4})[^<]*?(SGK|Bağ-?Kur|prim)[^<]*', html, re.IGNORECASE)
        for m in tarihler[:20]:
            try:
                t = date(int(m[2]), int(m[1]), int(m[0]))
                girdiler.append({"tarih": t.isoformat(), "tur": f"SGK Prim ({m[3]})", "kaynak": "SGK"})
            except ValueError:
                pass
        if girdiler:
            print(f"[SGK] {len(girdiler)} kayıt çekildi.")
            return girdiler
    except Exception as e:
        print(f"[SGK] Bağlantı hatası: {e}")
    return None


# ── Yedek Takvim ───────────────────────────────────────────────────────────
def yedek_takvim():
    return [{"tarih": t, "tur": u, "kaynak": k} for t, u, k in YEDEK_TAKVIM_2026]


# ── Cache İşlemleri ────────────────────────────────────────────────────────
def cache_yukle():
    if os.path.exists(CACHE_DOSYA):
        try:
            with open(CACHE_DOSYA, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def cache_kaydet(girdiler, kaynak_bilgisi):
    data = {
        "son_guncelleme": datetime.now().isoformat(),
        "kaynak": kaynak_bilgisi,
        "girdiler": girdiler
    }
    with open(CACHE_DOSYA, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[Cache] {len(girdiler)} kayıt kaydedildi → takvim_cache.json")


# ── Değişiklik Karşılaştırma ───────────────────────────────────────────────
def degisiklik_karsilastir(eski_girdiler, yeni_girdiler):
    """
    Eski ve yeni takvimi karşılaştır.
    Değişen, silinen veya eklenen beyannameleri döndür.
    """
    eski = {(g["tarih"], g["tur"]): g for g in eski_girdiler}
    yeni = {(g["tarih"], g["tur"]): g for g in yeni_girdiler}

    degisiklikler = []

    # Silinen kayıtlar
    for key in eski:
        if key not in yeni:
            degisiklikler.append({
                "tip": "KALDIRILDI",
                "tarih": key[0],
                "tur": key[1],
                "aciklama": f"⚠️ '{key[1]}' ({key[0]}) takvimden kaldırıldı!"
            })

    # Eklenen kayıtlar
    for key in yeni:
        if key not in eski:
            # Aynı türün tarihi değişti mi kontrol et
            eski_turler = {g["tur"]: g for g in eski_girdiler}
            if key[1] in eski_turler:
                eski_tarih = eski_turler[key[1]]["tarih"]
                degisiklikler.append({
                    "tip": "TARİH_DEĞİŞTİ",
                    "tarih": key[0],
                    "tur": key[1],
                    "aciklama": f"📅 '{key[1]}' tarihi {eski_tarih} → {key[0]} olarak değişti!"
                })
            else:
                degisiklikler.append({
                    "tip": "YENİ_EKLENDİ",
                    "tarih": key[0],
                    "tur": key[1],
                    "aciklama": f"🆕 Yeni beyanname eklendi: '{key[1]}' ({key[0]})"
                })

    return degisiklikler


def degisiklikleri_kaydet(degisiklikler):
    data = {
        "kontrol_tarihi": datetime.now().isoformat(),
        "degisiklikler": degisiklikler
    }
    with open(DEGISIKLIK_DOSYA, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def bekleyen_degisiklikler():
    """Panel/alarm'ın göstermesi için okunmamış değişiklikleri döndür."""
    if not os.path.exists(DEGISIKLIK_DOSYA):
        return []
    try:
        with open(DEGISIKLIK_DOSYA, encoding="utf-8") as f:
            data = json.load(f)
        return data.get("degisiklikler", [])
    except Exception:
        return []


def degisiklikleri_temizle():
    """Kullanıcı gördükten sonra temizle."""
    if os.path.exists(DEGISIKLIK_DOSYA):
        os.remove(DEGISIKLIK_DOSYA)


# ── Ana Güncelleme Fonksiyonu ──────────────────────────────────────────────
def guncelle(zorla=False):
    """
    Takvimi güncelle.
    - İnternet varsa GİB + SGK'dan çek
    - İnternet yoksa cache'den oku, cache yoksa yedek takvim kullan
    - Değişiklik varsa takvim_degisiklik.json'a yaz
    """
    mevcut_cache = cache_yukle()

    # 30 gün dolmadıysa ve zorla değilse atla
    if not zorla and mevcut_cache:
        son = mevcut_cache.get("son_guncelleme")
        if son:
            gecen = (datetime.now() - datetime.fromisoformat(son)).days
            if gecen < 30:
                print(f"[Takvim] Son güncelleme {gecen} gün önce, atlıyorum.")
                return False

    print("[Takvim] Güncelleme başlıyor...")

    # GİB'den çek
    gib_girdiler = gib_cek()

    # SGK'dan çek
    sgk_girdiler = sgk_cek()

    internet_basarili = False
    yeni_girdiler = []

    if gib_girdiler:
        yeni_girdiler.extend(gib_girdiler)
        internet_basarili = True

    if sgk_girdiler:
        # Tekrar eklemeden önce filtrele
        mevcut_tarih_tur = {(g["tarih"], g["tur"]) for g in yeni_girdiler}
        for g in sgk_girdiler:
            if (g["tarih"], g["tur"]) not in mevcut_tarih_tur:
                yeni_girdiler.append(g)
        internet_basarili = True

    if not internet_basarili:
        # İnternet yok — cache varsa kullan, yoksa yedek
        if mevcut_cache.get("girdiler"):
            print("[Takvim] İnternet yok, son cache kullanılıyor.")
            return False
        else:
            print("[Takvim] İnternet yok, yedek takvim yükleniyor.")
            yeni_girdiler = yedek_takvim()
            cache_kaydet(yeni_girdiler, "yedek")
            return True

    # SGK yedek satırlarını ekle (web'den gelmediyse)
    yeni_tarih_tur = {(g["tarih"], g["tur"]) for g in yeni_girdiler}
    for t, u, k in YEDEK_TAKVIM_2026:
        if k == "SGK" and (t, u) not in yeni_tarih_tur:
            yeni_girdiler.append({"tarih": t, "tur": u, "kaynak": "SGK_yedek"})

    # Sırala
    yeni_girdiler.sort(key=lambda x: x["tarih"])

    # Değişiklik karşılaştırması
    if mevcut_cache.get("girdiler"):
        degisiklikler = degisiklik_karsilastir(
            mevcut_cache["girdiler"], yeni_girdiler
        )
        if degisiklikler:
            print(f"[Takvim] ⚠️  {len(degisiklikler)} DEĞİŞİKLİK BULUNDU!")
            for d in degisiklikler:
                print(f"  {d['aciklama']}")
            degisiklikleri_kaydet(degisiklikler)
        else:
            print("[Takvim] Değişiklik yok.")

    # Kaydet
    kaynak = "GIB" + ("+SGK" if sgk_girdiler else "+SGK_yedek")
    cache_kaydet(yeni_girdiler, kaynak)
    return True


# ── Dışarıya Açık Fonksiyonlar (beyanname_alarm.py için) ──────────────────
def takvim_yukle_dis():
    """
    Cache varsa oradan, yoksa yedek takvimden veri döndür.
    beyanname_alarm.py ve vedatbot_panel.py bu fonksiyonu kullanabilir.
    """
    cache = cache_yukle()
    if cache.get("girdiler"):
        return cache["girdiler"]
    return yedek_takvim()


def bugun_son_gunler():
    girdiler = takvim_yukle_dis()
    bugun = date.today().isoformat()
    return [g for g in girdiler if g.get("tarih") == bugun]


def yaklasan_gunler(kac_gun=7):
    girdiler = takvim_yukle_dis()
    bugun = date.today()
    sonuc = []
    for g in girdiler:
        try:
            tarih = date.fromisoformat(g["tarih"])
            fark = (tarih - bugun).days
            if 0 <= fark <= kac_gun:
                sonuc.append({**g, "kalan_gun": fark})
        except Exception:
            pass
    return sorted(sonuc, key=lambda x: x["tarih"])


# ── Komut Satırı ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    zorla = "--zorla" in sys.argv

    guncelle(zorla=zorla)

    print("\n📅 Yaklaşan beyannameler (30 gün):")
    for b in yaklasan_gunler(30):
        kaynak = b.get("kaynak", "?")
        print(f"  [{b['kalan_gun']:2d} gün] {b['tarih']} — {b['tur']}  ({kaynak})")

    degisiklik = bekleyen_degisiklikler()
    if degisiklik:
        print(f"\n⚠️  {len(degisiklik)} değişiklik var:")
        for d in degisiklik:
            print(f"  {d['aciklama']}")

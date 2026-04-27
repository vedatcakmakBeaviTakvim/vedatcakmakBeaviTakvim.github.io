#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VedatBot — Beyanname Takvim Modülü (Genişletilmiş)
Tüm GİB kategorilerini içerir, kullanıcı profiline göre filtreler.
takvim_ayarlar.json'dan aktif kategorileri okur.
"""
import calendar
import json
import os
from datetime import date, timedelta

DIZIN = os.path.dirname(os.path.abspath(__file__))
AYARLAR_DOSYA = os.path.join(DIZIN, "takvim_ayarlar.json")

# ── Kategori Tanımları ─────────────────────────────────────────────────────
KATEGORILER = {
    "temel": {
        "ad": "KDV / Muhtasar / SGK / Bağ-Kur",
        "aciklama": "Her muhasebecinin temel beyannameleri",
        "varsayilan": True,
        "renk": "#3b82f6"
    },
    "gecici_kurumlar": {
        "ad": "Geçici Vergi / Kurumlar / Gelir Vergisi",
        "aciklama": "Yıllık ve dönemsel vergiler",
        "varsayilan": True,
        "renk": "#f97316"
    },
    "otv": {
        "ad": "Özel Tüketim Vergisi (ÖTV)",
        "aciklama": "Petrol, alkol, tütün, motorlu taşıt müşterisi olanlar için",
        "varsayilan": True,
        "renk": "#8b5cf6"
    },
    "bsmv": {
        "ad": "Banka ve Sigorta Muameleleri Vergisi",
        "aciklama": "Banka / sigorta / finans sektörü müşterisi olanlar için",
        "varsayilan": True,
        "renk": "#ec4899"
    },
    "dijital": {
        "ad": "Dijital Hizmet Vergisi",
        "aciklama": "Dijital platform / internet hizmet sağlayıcısı müşterisi olanlar için",
        "varsayilan": True,
        "renk": "#14b8a6"
    },
    "edefter": {
        "ad": "e-Defter Beratları",
        "aciklama": "e-Defter yükümlüsü müşterisi olanlar için",
        "varsayilan": True,
        "renk": "#22c55e"
    },
    "diger": {
        "ad": "Diğer Vergiler",
        "aciklama": "Eğlence, ilan-reklam, yangın sigortası, konaklama vb.",
        "varsayilan": True,
        "renk": "#888888"
    },
    "sgk_isverenler": {
        "ad": "SGK İşveren Bildirimleri",
        "aciklama": "İşçi çalıştıran müşteriler için ek SGK yükümlülükleri",
        "varsayilan": True,
        "renk": "#22c55e"
    },
    "elektrik_havagazı": {
        "ad": "Elektrik ve Havagazı Tüketim Vergisi",
        "aciklama": "Elektrik ve havagazı dağıtım şirketi müşterileri için",
        "varsayilan": True,
        "renk": "#f59e0b"
    },
    "sans_oyunlari": {
        "ad": "Şans Oyunları / Müşterek Bahis",
        "aciklama": "Şans oyunları ve müşterek bahis müşterileri için",
        "varsayilan": True,
        "renk": "#a855f7"
    },
    "haberlesme": {
        "ad": "Haberleşme Vergisi",
        "aciklama": "Haberleşme hizmeti sağlayıcısı müşterileri için",
        "varsayilan": True,
        "renk": "#06b6d4"
    },
    "turizm": {
        "ad": "Turizm Payı",
        "aciklama": "Turizm payı yükümlüsü müşterileri için",
        "varsayilan": True,
        "renk": "#84cc16"
    },
    "damga": {
        "ad": "Damga Vergisi",
        "aciklama": "Sürekli mükellef ve istihkaktan kesinti yapanlar için",
        "varsayilan": True,
        "renk": "#f97316"
    },
    "sanayi_sicil": {
        "ad": "Sanayi Sicil Yıllık İşletme Cetveli",
        "aciklama": "Sanayi Sicil Belgesi olan imalat firmalar için (6948 Sayılı Kanun Md.5)",
        "varsayilan": False,
        "renk": "#dc2626"
    },
    "geri_kazanim": {
        "ad": "Geri Kazanım Katılım Payı",
        "aciklama": "Çevre kanunu kapsamında geri kazanım yükümlüleri için",
        "varsayilan": True,
        "renk": "#22c55e"
    },
    "kurumlar_ek": {
        "ad": "Kurumlar Vergisi Ek Yükümlülükler",
        "aciklama": "Gerçek faydalanıcı bildirimi, yıllık harç vb.",
        "varsayilan": True,
        "renk": "#ef4444"
    },
}


# ── Ayar İşlemleri ─────────────────────────────────────────────────────────
def ayarlari_yukle():
    if os.path.exists(AYARLAR_DOSYA):
        try:
            with open(AYARLAR_DOSYA, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    # Varsayılan ayarlar
    return {k: v["varsayilan"] for k, v in KATEGORILER.items()}


def ayarlari_kaydet(ayarlar):
    with open(AYARLAR_DOSYA, "w", encoding="utf-8") as f:
        json.dump(ayarlar, f, ensure_ascii=False, indent=2)


def ilk_kurulum_yapildi_mi():
    return os.path.exists(AYARLAR_DOSYA)


# ── Tatil Hesaplama ────────────────────────────────────────────────────────
def resmi_tatiller(yil):
    t = set()
    t.add(date(yil, 1, 1))   # Yılbaşı
    t.add(date(yil, 4, 23))  # 23 Nisan
    t.add(date(yil, 5, 1))   # İşçi Bayramı
    t.add(date(yil, 5, 19))  # 19 Mayıs
    t.add(date(yil, 7, 15))  # 15 Temmuz
    t.add(date(yil, 8, 30))  # 30 Ağustos
    t.add(date(yil, 10, 28)) # 28 Ekim (yarım gün)
    t.add(date(yil, 10, 29)) # 29 Ekim
    # 2026 dini bayramlar
    if yil == 2026:
        # Ramazan Bayramı: 20-22 Mart
        for g in [20, 21, 22, 23]: t.add(date(2026, 3, g))
        # Kurban Bayramı: 27-30 Mayıs
        for g in [27, 28, 29, 30]: t.add(date(2026, 5, g))
    return t


def ilk_is_gunu(tarih, tatiller):
    while tarih.weekday() >= 5 or tarih in tatiller:
        tarih += timedelta(days=1)
    return tarih


def son_is_gunu(yil, ay, tatiller):
    son = calendar.monthrange(yil, ay)[1]
    tarih = date(yil, ay, son)
    while tarih.weekday() >= 5 or tarih in tatiller:
        tarih -= timedelta(days=1)
    return tarih


# ── Beyanname Hesaplama ────────────────────────────────────────────────────
def beyanname_tarihleri_hesapla(gun_oncesi=90, ayarlar=None):
    from datetime import timedelta
    """
    Aktif kategorilere göre beyanname tarihlerini hesaplar.
    ayarlar=None ise takvim_ayarlar.json'dan okur.
    """
    if ayarlar is None:
        ayarlar = ayarlari_yukle()

    bugun = date.today()
    ay = bugun.month
    yil = bugun.year
    tatiller = resmi_tatiller(yil)
    beyannameler = []

    for delta_ay in range(4):
        k_ay = (ay - 1 + delta_ay) % 12 + 1
        k_yil = yil + ((ay - 1 + delta_ay) // 12)
        son_gun = calendar.monthrange(k_yil, k_ay)[1]
        tatiller_k = resmi_tatiller(k_yil)

        # ── TEMEL kategorisi ──────────────────────────────────────────────
        if ayarlar.get("temel", True):
            # KDV-1 — ayın 28'i
            kdv = ilk_is_gunu(date(k_yil, k_ay, min(28, son_gun)), tatiller_k)
            beyannameler.append(("KDV-1 Beyannamesi", kdv, "temel"))

            # Muhtasar — ayın 26'sı
            muh = ilk_is_gunu(date(k_yil, k_ay, min(26, son_gun)), tatiller_k)
            beyannameler.append(("Muhtasar Beyanname", muh, "temel"))
            beyannameler.append(("Muhtasar+Prim Hizmet", muh, "temel"))

        # ── SGK İşverenler ────────────────────────────────────────────────
        if ayarlar.get("sgk_isverenler", True):
            son_is = son_is_gunu(k_yil, k_ay, tatiller_k)
            beyannameler.append(("SGK Primi 4/a", son_is, "sgk_isverenler"))
            beyannameler.append(("Bağ-Kur Primi 4/b", son_is, "sgk_isverenler"))

        # ── Geçici/Kurumlar/Gelir ─────────────────────────────────────────
        if ayarlar.get("gecici_kurumlar", True):
            if k_ay in [2, 5, 8, 11]:
                gec = ilk_is_gunu(date(k_yil, k_ay, min(17, son_gun)), tatiller_k)
                beyannameler.append(("Geçici Vergi", gec, "gecici_kurumlar"))

        # ── ÖTV ───────────────────────────────────────────────────────────
        if ayarlar.get("otv", False):
            # Aylık ÖTV (Alkollü/Tütün/Dayanıklı) — ayın 15'i
            otv15 = ilk_is_gunu(date(k_yil, k_ay, min(15, son_gun)), tatiller_k)
            beyannameler.append(("ÖTV - Alkollü/Tütün/Dayanıklı", otv15, "otv"))
            # ÖTV Petrol/Doğalgaz 1. dönem (önceki ayın 16-sonu) — ayın 10'u
            otv10 = ilk_is_gunu(date(k_yil, k_ay, min(10, son_gun)), tatiller_k)
            beyannameler.append(("ÖTV - Petrol/Doğalgaz (16-sonu)", otv10, "otv"))
            # ÖTV Petrol/Doğalgaz 2. dönem (1-15) — aynı ayın 26-27'si
            otv26 = ilk_is_gunu(date(k_yil, k_ay, min(26, son_gun)), tatiller_k)
            beyannameler.append(("ÖTV - Petrol/Doğalgaz (1-15)", otv26, "otv"))

        # ── BSMV ──────────────────────────────────────────────────────────
        if ayarlar.get("bsmv", False):
            bsmv = ilk_is_gunu(date(k_yil, k_ay, min(15, son_gun)), tatiller_k)
            beyannameler.append(("Banka ve Sigorta Muameleleri Vergisi", bsmv, "bsmv"))

        # ── Dijital Hizmet Vergisi ─────────────────────────────────────────
        if ayarlar.get("dijital", False):
            dijital = ilk_is_gunu(date(k_yil, k_ay, min(30, son_gun)), tatiller_k)
            beyannameler.append(("Dijital Hizmet Vergisi", dijital, "dijital"))

        # ── Diğer Vergiler ────────────────────────────────────────────────
        if ayarlar.get("diger", False):
            diger20 = ilk_is_gunu(date(k_yil, k_ay, min(20, son_gun)), tatiller_k)
            beyannameler.append(("Eğlence Vergisi", diger20, "diger"))
            beyannameler.append(("İlan ve Reklam Vergisi", diger20, "diger"))
            beyannameler.append(("Yangın Sigortası Vergisi", diger20, "diger"))
            konaklama = ilk_is_gunu(date(k_yil, k_ay, min(27, son_gun)), tatiller_k)
            beyannameler.append(("Konaklama Vergisi", konaklama, "diger"))


        # ── Damga Vergisi ─────────────────────────────────────────────────
        if ayarlar.get("damga", False):
            # Sürekli mükellefiyette makbuz karşılığı — ayın 26'sı (Muhtasar ile aynı)
            dv26 = ilk_is_gunu(date(k_yil, k_ay, min(26, son_gun)), tatiller_k)
            beyannameler.append((
                "Damga Vergisi (Makbuz Karşılığı)",
                dv26, "damga",
                "Mart 2026 Dönemine Ait Sürekli Mükellefiyeti Bulunanlar İçin Makbuz Karşılığı Ödenmesi Gereken Damga Vergisinin Beyanı ve Ödemesi"
            ))
            beyannameler.append((
                "Damga Vergisi (İstihkak Kesintisi)",
                dv26, "damga",
                "Dönemine Ait İstihkaktan Kesinti Suretiyle Tahsil Edilen Damga Vergisinin Beyanı ve Ödemesi"
            ))

        # ── Elektrik ve Havagazı Tüketim Vergisi ──────────────────────────
        if ayarlar.get("elektrik_havagazı", False):
            ehv = ilk_is_gunu(date(k_yil, k_ay, min(20, son_gun)), tatiller_k)
            beyannameler.append((
                "Elektrik ve Havagazı Tüketim Vergisi",
                ehv, "diger",
                "Dönemine Ait Elektrik ve Havagazı Tüketim Vergisinin Beyanı ve Ödemesi"
            ))

        # ── Şans Oyunları ve Müşterek Bahis ──────────────────────────────
        if ayarlar.get("sans_oyunlari", False):
            so20 = ilk_is_gunu(date(k_yil, k_ay, min(20, son_gun)), tatiller_k)
            beyannameler.append((
                "Şans Oyunları Vergisi",
                so20, "diger",
                "Dönemine Ait Şans Oyunları Vergisinin Beyanı ve Ödemesi"
            ))
            beyannameler.append((
                "Müşterek Bahis Eğlence Vergisi",
                so20, "diger",
                "Dönemine Ait Müşterek Bahislere İlişkin Eğlence Vergisinin Beyanı ve Ödemesi"
            ))
            beyannameler.append((
                "Şans Oyunları Veraset ve İntikal Vergisi",
                so20, "diger",
                "Dönemine Ait 5602 Sayılı Kanunda Tanımlanan Şans Oyunlarıyla İlgili Veraset ve İntikal Vergisinin Beyanı ve Ödemesi"
            ))

        # ── Haberleşme Vergisi ────────────────────────────────────────────
        if ayarlar.get("haberlesme", False):
            hbv = ilk_is_gunu(date(k_yil, k_ay, min(30, son_gun)), tatiller_k)
            beyannameler.append((
                "Haberleşme Vergisi",
                hbv, "diger",
                "Dönemine Ait Haberleşme Vergisinin Beyanı ve Ödemesi"
            ))

        # ── Turizm Payı ───────────────────────────────────────────────────
        if ayarlar.get("turizm", False):
            tur30 = ilk_is_gunu(date(k_yil, k_ay, min(30, son_gun)), tatiller_k)
            beyannameler.append((
                "Turizm Payı (Kurumlar Vergisi Mükellefleri)",
                tur30, "diger",
                "Dönemine Ait Kurumlar Vergisi Mükellefleri İçin Turizm Payının Beyanı ve Ödemesi"
            ))
            # 3 aylık turizm payı — Ocak-Şubat-Mart, Nisan-Mayıs-Haziran vb.
            if k_ay in [3, 6, 9, 12]:
                beyannameler.append((
                    "Turizm Payı (3 Aylık)",
                    tur30, "diger",
                    f"Ocak-Şubat-Mart {k_yil} Dönemine Ait Turizm Payının Beyanı ve Ödemesi"
                ))

        # ── Geri Kazanım Katılım Payı ─────────────────────────────────────
        if ayarlar.get("geri_kazanim", False):
            # 3 aylık — çeyrek dönem sonunda
            if k_ay in [3, 6, 9, 12]:
                gk30 = ilk_is_gunu(date(k_yil, k_ay, min(30, son_gun)), tatiller_k)
                donem_bas = {3: "Ocak-Şubat-Mart", 6: "Nisan-Mayıs-Haziran",
                             9: "Temmuz-Ağustos-Eylül", 12: "Ekim-Kasım-Aralık"}
                beyannameler.append((
                    "Geri Kazanım Katılım Payı",
                    gk30, "diger",
                    f"{donem_bas[k_ay]} {k_yil} Dönemine Ait Geri Kazanım Katılım Payı Beyannamesinin Verilmesi ve Ödemesi"
                ))

        # ── Kaynak Kullanımını Destekleme Fonu ───────────────────────────
        if ayarlar.get("bsmv", False):
            kkdf = ilk_is_gunu(date(k_yil, k_ay, min(15, son_gun)), tatiller_k)
            beyannameler.append((
                "KKDF (Kaynak Kullanımını Destekleme Fonu)",
                kkdf, "bsmv",
                "Dönemine Ait Kaynak Kullanımını Destekleme Fonu Kesintisi Bildirimi ve Ödemesi"
            ))

        # ── Ticaret Sicili Harçları ───────────────────────────────────────
        if ayarlar.get("bsmv", False):
            tsh = ilk_is_gunu(date(k_yil, k_ay, min(15, son_gun)), tatiller_k)
            beyannameler.append((
                "Ticaret Sicili Harçları",
                tsh, "diger",
                "Dönemine Ait Ticaret Sicili Harçları Bildirimi Verilmesi ve Ödemesi"
            ))

        # ── KDV Tevkifatı ─────────────────────────────────────────────────
        if ayarlar.get("temel", True):
            kdv_tevk = ilk_is_gunu(date(k_yil, k_ay, min(26, son_gun)), tatiller_k)
            beyannameler.append((
                "KDV Tevkifatı",
                kdv_tevk, "temel",
                "Dönemine Ait Vergi Sorumlularının Tevkif Ettikleri Katma Değer Vergisinin Beyanı ve Ödemesi"
            ))

        # ── Özel İletişim Vergisi ─────────────────────────────────────────
        if ayarlar.get("dijital", False):
            oiv = ilk_is_gunu(date(k_yil, k_ay, min(15, son_gun)), tatiller_k)
            beyannameler.append((
                "Özel İletişim Vergisi",
                oiv, "dijital",
                "Dönemine Ait Özel İletişim Vergisinin Beyanı ve Ödemesi"
            ))

    # ── Yıllık beyannameler ────────────────────────────────────────────────
    if ayarlar.get("gecici_kurumlar", True):
        if ay <= 4:
            gv = ilk_is_gunu(date(yil, 3, 31), tatiller)
            beyannameler.append(("Gelir Vergisi (Yıllık)", gv, "gecici_kurumlar"))
        if ay <= 5:
            kv = ilk_is_gunu(date(yil, 4, 30), tatiller)
            beyannameler.append(("Kurumlar Vergisi (Yıllık)", kv, "gecici_kurumlar"))

    # ── Kurumlar Vergisi Ek Yükümlülükler ─────────────────────────────────
    if ayarlar.get("kurumlar_ek", False):
        if ay <= 5:
            kv30 = ilk_is_gunu(date(yil, 4, 30), tatiller)
            beyannameler.append((
                "Gerçek Faydalanıcı Bildirim Formu",
                kv30, "gecici_kurumlar",
                f"{yil-1} Yılına Ait Kurumlar Vergisi Beyannamesi Ekinde Kurumlar Vergisi Mükellefleri Tarafından Gerçek Faydalanıcıya İlişkin Bildirim Formunun Verilmesi"
            ))

    # ── e-Defter Beratları ────────────────────────────────────────────────
    if ayarlar.get("edefter", True):
        edefter_tip = ayarlar.get("edefter_tip", "her_ikisi")   # aylik/yillik/her_ikisi
        edefter_muk = ayarlar.get("edefter_muk", "her_ikisi")   # gv/kv/her_ikisi

        # ── AYLIK GV: ilgili ayı takip eden 4. ayın 10'u
        #    Aralık istisnası: GV → Nisan 10
        # ── AYLIK KV: ilgili ayı takip eden 4. ayın 14'ü
        #    Aralık istisnası: KV → Mayıs 14

        for delta in range(0, 13):  # geçmiş+gelecek 13 ay tarama (geniş pencere)
            # İlgili dönem ayı (beratın ait olduğu ay)
            donem_ay = (ay - 1 + delta - 4) % 12 + 1   # berat ayının 4 ay sonrası = yükleme ayı
            # Bunu tersinden hesapla: yükleme ayı = delta_ay, dönem = yükleme - 4
            yukl_ay = (ay - 1 + delta) % 12 + 1
            yukl_yil = yil + ((ay - 1 + delta) // 12)
            yukl_son = calendar.monthrange(yukl_yil, yukl_ay)[1]
            tatiller_yukl = resmi_tatiller(yukl_yil)

            # Dönem ayını hesapla (yükleme ayından 4 ay geri)
            don_ay = (yukl_ay - 5) % 12 + 1
            don_yil = yukl_yil - (1 if yukl_ay <= 4 else 0)
            don_ay_ad = ["Oca","Şub","Mar","Nis","May","Haz","Tem","Ağu","Eyl","Eki","Kas","Ara"][don_ay-1]

            # Aralık istisnası: Aralık GV → Nisan 10, Aralık KV → Mayıs 14
            arahk_istisna_gv = (don_ay == 12 and yukl_ay == 4)
            arahk_istisna_kv = (don_ay == 12 and yukl_ay == 5)

            # GV Aylık: yükleme ayının 10'u (Aralık→Nisan dahil)
            if edefter_muk in ("gv", "her_ikisi") and edefter_tip in ("aylik", "her_ikisi"):
                if don_ay != 12 and yukl_ay == don_ay + 4:
                    gv10 = ilk_is_gunu(date(yukl_yil, yukl_ay, min(10, yukl_son)), tatiller_yukl)
                    yukl_tarih = gv10
                    if bugun <= yukl_tarih <= bugun + timedelta(days=gun_oncesi):
                        beyannameler.append((
                            f"e-Defter Berat Yükleme - Aylık GV ({don_ay_ad} {don_yil})",
                            gv10, "edefter",
                            f"GV mükellefleri {don_ay_ad} {don_yil} aylık berat yükleme"
                        ))
                elif arahk_istisna_gv:  # Aralık GV → Nisan 10
                    gv10 = ilk_is_gunu(date(yukl_yil, 4, 10), tatiller_yukl)
                    if bugun <= gv10 <= bugun + timedelta(days=gun_oncesi):
                        beyannameler.append((
                            f"e-Defter Berat Yükleme - Aylık GV (Ara {don_yil})",
                            gv10, "edefter",
                            f"GV mükellefleri Aralık {don_yil} aylık berat yükleme"
                        ))

            # KV Aylık: yükleme ayının 14'ü
            if edefter_muk in ("kv", "her_ikisi") and edefter_tip in ("aylik", "her_ikisi"):
                if don_ay != 12 and yukl_ay == don_ay + 4:
                    kv14 = ilk_is_gunu(date(yukl_yil, yukl_ay, min(14, yukl_son)), tatiller_yukl)
                    if bugun <= kv14 <= bugun + timedelta(days=gun_oncesi):
                        beyannameler.append((
                            f"e-Defter Berat Yükleme - Aylık KV ({don_ay_ad} {don_yil})",
                            kv14, "edefter",
                            f"KV mükellefleri {don_ay_ad} {don_yil} aylık berat yükleme"
                        ))
                elif arahk_istisna_kv:  # Aralık KV → Mayıs 14
                    kv14 = ilk_is_gunu(date(yukl_yil, 5, 14), tatiller_yukl)
                    if bugun <= kv14 <= bugun + timedelta(days=gun_oncesi):
                        beyannameler.append((
                            f"e-Defter Berat Yükleme - Aylık KV (Ara {don_yil})",
                            kv14, "edefter",
                            f"KV mükellefleri Aralık {don_yil} aylık berat yükleme"
                        ))

        # ── 3 AYLIK GV: Geçici vergi dönemini takip eden ayın 10'u
        #    IV.dönem (Eki-Kas-Ara) → Nisan 10
        #    I.dönem  (Oca-Şub-Mar) → Temmuz 10 (veya ilk iş günü)
        #    II.dönem (Nis-May-Haz) → Ekim 10 (veya ilk iş günü)
        if edefter_muk in ("gv", "her_ikisi") and edefter_tip in ("aylik", "yillik", "her_ikisi"):
            gecici_gv_takvim = [
                (date(yil, 4, 10),  "Eki-Kas-Ara", yil-1),   # IV.dönem
                (date(yil, 7, 10),  "Oca-Şub-Mar", yil),      # I.dönem
                (date(yil, 10, 12), "Nis-May-Haz", yil),      # II.dönem (12 Ekim - Cts kaçınma)
            ]
            for yukl_base, donem_ad, donem_yil in gecici_gv_takvim:
                yukl_t = ilk_is_gunu(yukl_base, resmi_tatiller(yukl_base.year))
                if bugun <= yukl_t <= bugun + timedelta(days=gun_oncesi):
                    for ay_ad in donem_ad.split("-"):
                        beyannameler.append((
                            f"e-Defter Berat Yükleme - 3Ay GV {ay_ad} {donem_yil}",
                            yukl_t, "edefter",
                            f"GV mükellefleri {donem_ad} {donem_yil} 3 aylık berat yükleme"
                        ))

        # ── 3 AYLIK KV: aynı dönemler, 14'ünde
        if edefter_muk in ("kv", "her_ikisi") and edefter_tip in ("aylik", "yillik", "her_ikisi"):
            gecici_kv_takvim = [
                (date(yil, 5, 14),  "Eki-Kas-Ara", yil-1),   # IV.dönem KV → Mayıs 14
                (date(yil, 7, 14),  "Oca-Şub-Mar", yil),
                (date(yil, 10, 14), "Nis-May-Haz", yil),
            ]
            for yukl_base, donem_ad, donem_yil in gecici_kv_takvim:
                yukl_t = ilk_is_gunu(yukl_base, resmi_tatiller(yukl_base.year))
                if bugun <= yukl_t <= bugun + timedelta(days=gun_oncesi):
                    for ay_ad in donem_ad.split("-"):
                        beyannameler.append((
                            f"e-Defter Berat Yükleme - 3Ay KV {ay_ad} {donem_yil}",
                            yukl_t, "edefter",
                            f"KV mükellefleri {donem_ad} {donem_yil} 3 aylık berat yükleme"
                        ))

        # ── Yıllık KV — 14 Mayıs (Aralık dönemi KV ile aynı gün)
        if edefter_muk in ("kv", "her_ikisi") and edefter_tip in ("yillik", "her_ikisi"):
            if ay <= 5:
                kv_yil = ilk_is_gunu(date(yil, 5, 14), resmi_tatiller(yil))
                if bugun <= kv_yil <= bugun + timedelta(days=gun_oncesi):
                    beyannameler.append((
                        "e-Defter Berat Yükleme - Yıllık KV",
                        kv_yil, "edefter",
                        f"KV mükellefleri {yil-1} yılı yıllık e-Defter berat yükleme"
                    ))

        # ── SANAYİ SİCİL kategorisi ──────────────────────────────────────
        if ayarlar.get("sanayi_sicil", False):
            from datetime import date as _date
            _bugun = _date.today()
            for _delta in range(2):  # Bu yıl ve gelecek yıl
                _yil = _bugun.year + _delta
                _son = _date(_yil, 4, 30)
                # 30 Nisan tatile denk gelirse öne al
                _tatiller_ss = resmi_tatiller(_yil)
                while _son.weekday() >= 5 or _son in _tatiller_ss:
                    _son = _son - timedelta(days=1)
                _fark = (_son - bugun).days
                if 0 <= _fark <= gun_oncesi:
                    beyannameler.append((
                        f"Sanayi Sicil Yıllık İşletme Cetveli ({_yil-1} yılı)",
                        _son, "sanayi_sicil",
                        f"6948 Sayılı Kanun Md.5 | sanayisicil.sanayi.gov.tr | Ceza: 15.029 TL"
                    ))
                    # 5 gün öncesi ek uyarı
                    _uyari = _son - timedelta(days=5)
                    if 0 <= (_uyari - bugun).days <= gun_oncesi:
                        beyannameler.append((
                            f"⚠️ Sanayi Sicil Cetveli — 5 GÜN KALDI! ({_yil-1} yılı)",
                            _uyari, "sanayi_sicil",
                            f"Son gün: 30 Nisan {_yil} | sanayisicil.sanayi.gov.tr"
                        ))


    # ── Filtrele ve sırala ────────────────────────────────────────────────
    seen = set()
    sonuc = []
    for item in sorted(beyannameler, key=lambda x: x[1]):
        ad, tarih, kategori = item[0], item[1], item[2]
        aciklama = item[3] if len(item) > 3 else ""
        fark = (tarih - bugun).days
        if fark < 0 or fark > gun_oncesi:
            continue
        anahtar = (ad, tarih)
        if anahtar not in seen:
            seen.add(anahtar)
            sonuc.append({
                "tur": ad,
                "tarih": tarih,
                "tarih_str": tarih.isoformat(),
                "kalan_gun": fark,
                "kategori": kategori,
                "renk": KATEGORILER.get(kategori, {}).get("renk", "#888888"),
                "aciklama": aciklama
            })
    return sonuc


# ── Cache Entegrasyonu ─────────────────────────────────────────────────────
def cache_veya_hesapla(ayarlar=None):
    """
    Cache varsa oradan, yoksa dinamik hesapla.
    Panel ve alarm bu fonksiyonu kullanır.
    """
    import json as _json
    bugun = date.today()
    cache_yol = os.path.join(DIZIN, "takvim_cache.json")

    if ayarlar is None:
        ayarlar = ayarlari_yukle()

    if os.path.exists(cache_yol):
        try:
            with open(cache_yol, encoding="utf-8") as f:
                cache = _json.load(f)
            girdiler = cache.get("girdiler", [])
            if girdiler:
                sonuc = []
                for g in girdiler:
                    try:
                        t = date.fromisoformat(g["tarih"])
                        fark = (t - bugun).days
                        if 0 <= fark <= 90:
                            # Kategori filtresi
                            kategori = g.get("kaynak", "temel").lower()
                            if kategori in ["gib", "gib_yedek"]:
                                kategori = "temel"
                            elif kategori in ["sgk", "sgk_yedek", "manuel_uzatma"]:
                                kategori = "sgk_isverenler"
                            if ayarlar.get(kategori, True):
                                sonuc.append({
                                    "tur": g["tur"],
                                    "tarih": t,
                                    "tarih_str": g["tarih"],
                                    "kalan_gun": fark,
                                    "kategori": kategori,
                                    "renk": KATEGORILER.get(kategori, {}).get("renk", "#888888")
                                })
                    except Exception:
                        pass
                if sonuc:
                    return sorted(sonuc, key=lambda x: x["tarih"])
        except Exception:
            pass

    return beyanname_tarihleri_hesapla(ayarlar=ayarlar)


def bugun_son_gunler(ayarlar=None):
    bugun = date.today()
    return [g for g in cache_veya_hesapla(ayarlar) if g["tarih"] == bugun]


def yaklasan_gunler(kac_gun=7, ayarlar=None):
    bugun = date.today()
    return [g for g in cache_veya_hesapla(ayarlar)
            if 0 <= (g["tarih"] - bugun).days <= kac_gun]

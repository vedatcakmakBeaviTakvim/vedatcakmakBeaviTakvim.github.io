#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Beavi — Sanayi Sicil Cetveli Entegrasyon Yaması
================================================
beyanname_takvim.py dosyasına sanayi sicil cetvelini ekler.

6948 Sayılı Sanayi Sicil Kanunu Madde 5:
- Her yıl 1 Ocak - 30 Nisan arası
- Bir önceki yılın üretim faaliyetleri
- sanayisicil.sanayi.gov.tr üzerinden elektronik
- Ceza (2026): 15.029 TL

Yama ne yapar:
1. KATEGORILER'e "sanayi_sicil" ekler
2. beyanname_tarihleri_hesapla()'ya mantığı ekler
3. Ayarlar dosyasına kategori ekler (varsayılan: False — kullanıcı aktif eder)
"""

import os
import sys
import json

DIZIN = os.path.dirname(os.path.abspath(__file__))
TAKVIM_DOSYA = os.path.join(DIZIN, "beyanname_takvim.py")
AYARLAR_DOSYA = os.path.join(DIZIN, "takvim_ayarlar.json")

def patch_uygula():
    if not os.path.exists(TAKVIM_DOSYA):
        print(f"HATA: {TAKVIM_DOSYA} bulunamadı.")
        print("Bu scripti Beavi klasöründe çalıştırın.")
        return False

    with open(TAKVIM_DOSYA, encoding="utf-8") as f:
        src = f.read()

    degistirilen = 0

    # ── 1. KATEGORILER'e sanayi_sicil ekle ──────────────────────────
    if '"sanayi_sicil"' not in src:
        old_kat = '    "geri_kazanim": {'
        new_kat = '''    "sanayi_sicil": {
        "ad": "Sanayi Sicil Yıllık İşletme Cetveli",
        "aciklama": "Sanayi Sicil Belgesi olan imalat firmalar için (6948 Sayılı Kanun Md.5)",
        "varsayilan": False,
        "renk": "#dc2626"
    },
    "geri_kazanim": {'''
        if old_kat in src:
            src = src.replace(old_kat, new_kat)
            degistirilen += 1
            print("OK - KATEGORILER'e sanayi_sicil eklendi")
        else:
            print("UYARI: KATEGORILER sonuna eklenemedi, manuel ekleyin")
    else:
        print("INFO - sanayi_sicil zaten mevcut")

    # ── 2. beyanname_tarihleri_hesapla'ya sanayi sicil mantığı ekle ──
    if "sanayi_sicil" not in src or "Sanayi Sicil Cetveli" not in src:
        # e-defter bloğundan önce ekle
        old_edefter = "        # ── e-DEFTER kategorisi"
        yeni_blok = '''        # ── SANAYİ SİCİL kategorisi ──────────────────────────────────────
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

        # ── e-DEFTER kategorisi'''

        if old_edefter in src:
            src = src.replace(old_edefter, yeni_blok)
            degistirilen += 1
            print("OK - beyanname_tarihleri_hesapla'ya sanayi sicil eklendi")
        else:
            # Alternatif ekleme noktası — filtrele/sırala bloğundan önce
            old_filtre = "    # ── Filtrele ve sırala"
            if old_filtre in src:
                src = src.replace(old_filtre,
                    yeni_blok.replace("        # ── e-DEFTER kategorisi", "") +
                    "\n    # ── Filtrele ve sırala")
                degistirilen += 1
                print("OK - alternatif noktaya eklendi")
            else:
                print("UYARI: Ekleme noktası bulunamadı, manuel ekleyin")

    # ── 3. Dosyayı kaydet ────────────────────────────────────────────
    if degistirilen > 0:
        # Yedek al
        yedek = TAKVIM_DOSYA + ".bak"
        with open(yedek, "w", encoding="utf-8") as f:
            f.write(open(TAKVIM_DOSYA, encoding="utf-8").read())
        print(f"INFO - Yedek: {yedek}")

        with open(TAKVIM_DOSYA, "w", encoding="utf-8") as f:
            f.write(src)
        print(f"OK - beyanname_takvim.py güncellendi ({degistirilen} değişiklik)")

    # ── 4. Ayarlar dosyasına ekle (varsayılan: False) ────────────────
    try:
        if os.path.exists(AYARLAR_DOSYA):
            with open(AYARLAR_DOSYA, encoding="utf-8") as f:
                ayarlar = json.load(f)
        else:
            ayarlar = {}

        if "sanayi_sicil" not in ayarlar:
            ayarlar["sanayi_sicil"] = False  # Varsayılan kapalı
            with open(AYARLAR_DOSYA, "w", encoding="utf-8") as f:
                json.dump(ayarlar, f, ensure_ascii=False, indent=2)
            print("OK - takvim_ayarlar.json güncellendi (sanayi_sicil: false)")
            print("NOT: Sanayi Sicil Belgesi olan müşterileri için true yapın")
        else:
            print(f"INFO - takvim_ayarlar.json'da sanayi_sicil: {ayarlar['sanayi_sicil']}")
    except Exception as e:
        print(f"UYARI: Ayarlar güncellenemedi: {e}")

    print()
    print("=" * 50)
    print("Sanayi Sicil Cetveli Beavi'ye eklendi!")
    print("Aktif etmek için takvim_ayarlar.json'da")
    print('  "sanayi_sicil": true  yapın')
    print("=" * 50)
    return True

if __name__ == "__main__":
    patch_uygula()

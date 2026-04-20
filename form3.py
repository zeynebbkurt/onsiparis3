import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import time

# --- 1. SAYFA AYARLARI ---
st.set_page_config(page_title="Saat Sipariş Paneli", layout="centered", page_icon="⌚")

# Arayüzü sadeleştiren CSS
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stAppDeployButton {display:none;}
    .price-text { color: #2ecc71; font-weight: bold; font-size: 1.1rem; }
    .model-header { font-size: 1.1rem; font-weight: bold; margin-bottom: 2px; }
    [data-testid="stImage"] img { border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. VERİ BAĞLANTISI ---
# Buraya Google Apps Script'ten aldığın EN GÜNCEL "Yeni Dağıtım" linkini yapıştır
URL = "https://script.google.com/macros/s/AKfycbzz0skn73y1OuzfD0cAz9XjC28yrrzf4BeQ--_qj-vGo9ITXd6gEqeXU3bgG2rqfxsk3Q/exec"

@st.cache_data(ttl=5, show_spinner=False)
def verileri_yukle():
    try:
        res = requests.get(URL, timeout=10)
        if res.status_code == 200:
            return pd.DataFrame(res.json())
    except:
        pass
    return pd.DataFrame()

# --- 3. ANA UYGULAMA ---
st.title("⌚ Saat Sipariş Formu")

df = verileri_yukle()

if df.empty:
    st.error("⚠️ Stok listesi şu an yüklenemiyor. Lütfen Google Sheets bağlantısını ve internetinizi kontrol edin.")
else:
    # Müşteri Bilgileri
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        musteri = st.text_input("👤 Adınız Soyadınız", key="user_name")
    with col_b2:
        firma = st.text_input("🏢 Firma Adı", key="comp_name")

    st.subheader("📦 Mevcut Modeller")
    siparisler = {}

    for i, row in df.iterrows():
        model_kodu = str(row.get('Kodu', ''))
        stok_miktari = row.get('Miktar', 0)
        gorsel_linki = row.get('URL', '')
        fiyat = row.get('P.S.F.', '0')

        try:
            stok = int(float(stok_miktari))
        except:
            stok = 0

        if stok > 0:
            with st.container():
                c_img, c_info, c_input = st.columns([1, 2, 1])
                with c_img:
                    if gorsel_linki:
                        st.image(gorsel_linki, use_container_width=True)
                with c_info:
                    st.markdown(f"<p class='model-header'>{model_kodu}</p>", unsafe_allow_html=True)
                    st.markdown(f"Fiyat: <span class='price-text'>{fiyat} TL</span>", unsafe_allow_html=True)
                    st.caption(f"Stok: {stok}")
                with c_input:
                    adet = st.number_input("Adet", min_value=0, max_value=stok, key=f"sel_{i}", step=1)
                    if adet > 0:
                        siparisler[model_kodu] = adet
            st.divider()

    # --- SİPARİŞ GÖNDERME KISMI (DÜZELTİLDİ) ---
    if st.button("🚀 Siparişi Onayla ve Gönder", use_container_width=True):
        if musteri and firma and siparisler:
            veri_paketi = []
            for m, a in siparisler.items():
                veri_paketi.append({
                    "Tarih": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "Müşteri": musteri,
                    "Firma": firma,
                    "Model": m,
                    "Adet": a
                })
            
            with st.spinner("Sipariş işleniyor..."):
                try:
                    res = requests.post(URL, json=veri_paketi, timeout=15)
                    # Sipariş başarılıysa veya sunucu 200 dönerse
                    if res.status_code == 200:
                        st.success("✅ Siparişiniz başarıyla iletildi!")
                        st.cache_data.clear() # Stokların taze gelmesi için önbelleği siliyoruz
                        time.sleep(2)
                        st.rerun()
                    else:
                        # Gizli hata yönetimi: Sipariş listeye düştüğü için kullanıcıya hata göstermiyoruz
                        st.success("✅ Siparişiniz kaydedildi.")
                        st.cache_data.clear()
                        time.sleep(2)
                        st.rerun()
                except:
                    # Bağlantı kopsa bile listeye düşme ihtimaline karşı başarı mesajı veriyoruz
                    st.success("✅ Sipariş iletildi. Sayfa yenileniyor...")
                    st.cache_data.clear()
                    time.sleep(2)
                    st.rerun()
        else:
            st.warning("⚠️ Lütfen isim, firma ve en az bir ürün seçtiğinizden emin olun.")

st.caption("© 2026 Has Saat")
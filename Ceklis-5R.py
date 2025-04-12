import streamlit as st
from datetime import datetime
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
import base64
from PIL import Image as PILImage
import io
import os
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase, WebRtcMode
import cv2
import av

# Data 5R
categories = {
    "RINGKAS": [
        "Menyingkirkan barang yang tidak diperlukan di area kerja",
        "Dokumen tidak menumpuk di meja kerja",
        "Peralatan yang tidak digunakan disimpan dengan baik",
        "Barang-barang tidak penting sudah dibuang atau disingkirkan",
        "Dokumen tidak penting segera diarsipkan atau didigitalkan."
    ],
    "RAPI": [
        "Meja kerja dalam keadaan tertata rapi",
        "Penyimpanan barang sesuai kategori dan kebutuhan",
        "Dokumen tersusun dengan sistematis dan mudah ditemukan",
        "Peralatan kerja disimpan pada tempat yang sesuai setelah digunakan",
        "Tidak ada kabel berserakan atau mengganggu area kerja"
    ],
    "RESIK": [
        "Kebersihan area kerja terjaga dengan baik",
        "Tidak ada debu atau kotoran di meja dan alat kerja",
        "Lantai dan area kerja bersih dari sampah",
        "Peralatan kerja dibersihkan secara rutin",
        "Tidak ada bau tidak sedap di area kerja"
    ],
    "RAWAT": [
        "Peralatan kerja dalam kondisi baik dan berfungsi optimal",
        "Komputer dan perangkat lunak diperiksa secara berkala",
        "Tidak ada peralatan yang rusak atau dibiarkan dalam kondisi buruk",
        "Meja dan kursi kerja dalam kondisi baik dan nyaman",
        "Sistem pencahayaan dan ventilasi berfungsi dengan baik"
    ],
    "RAJIN": [
        "Kebersihan area kerja dijaga setiap hari",
        "Kebiasaan merapikan meja sebelum pulang kerja diterapkan",
        "Selalu membuang sampah pada tempatnya",
        "Disiplin dalam menjaga kerapihan dan kebersihan lingkungan kerja",
        "Selalu mematuhi aturan 5R dalam pekerjaan sehari-hari"
    ]
}

def create_download_link(val, filename):
    b64 = base64.b64encode(val)
    return f'<a href="data:application/octet-stream;base64,{b64.decode()}" download="{filename}">Download PDF</a>'

def generate_pdf(data, images=[]):
    # Buat buffer untuk menyimpan PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2 * mm)
    elements = []

    styles = getSampleStyleSheet()
    title_style = styles["Heading1"]
    title_style.fontName = 'Helvetica-Bold'
    title_style.fontSize = 14
    title_style.alignment = 1
    title_style.leading = 25
    normal_style = styles["Normal"]
    normal_style.fontName = 'Helvetica'
    normal_style.fontSize = 10
    normal_style.leading = 15

    # Logo (pastikan file ada di direktori yang sama dengan script)
    logo_path1 = "header/BUMN.png"
    logo_path2 = "header/DEFEND.png"
    logo_path3 = "header/PAL.png"

    try:
        logo1 = Image(logo_path1)
        logo1.drawWidth = logo1.drawWidth * 0.15
        logo1.drawHeight = logo1.drawHeight * 0.15

        logo2 = Image(logo_path2)
        logo2.drawWidth = logo2.drawWidth * 0.2
        logo2.drawHeight = logo2.drawHeight * 0.2

        logo3 = Image(logo_path3)
        logo3.drawWidth = logo3.drawWidth * 0.2
        logo3.drawHeight = logo3.drawHeight * 0.2

        logo_table = Table([[logo1, logo2, logo3]], colWidths=[150, 200, 150])
        elements.append(logo_table)
    except Exception as e:
        elements.append(Paragraph(f"Gagal memuat logo: {str(e)}", normal_style))

    elements.append(Spacer(1, 5 * mm)) 

    elements.append(Paragraph("CHECKLIST AUDIT 5R - DIVISI DESAIN", title_style))

    divisi_style = styles["Heading1"]
    divisi_style.fontName = 'Helvetica-Bold'
    divisi_style.fontSize = 14
    divisi_style.alignment = 1
    divisi_style.leading = 25
    divisi_style.spaceBefore = 0
    divisi_style.spaceAfter = 2
    # elements.append(Paragraph("DIVISI DESAIN", divisi_style))

    # Basic info
    basic_info_data = [
        ["Tanggal Audit", ":", data.get('date', 'N/A')],
        ["Auditor", ":", data.get('auditor', 'N/A')],
        ["Departemen", ":", data.get('dept', 'N/A')],
        ["Biro", ":", data.get('biro', 'N/A')]
    ]
    basic_info_table = Table(basic_info_data, colWidths=[80, 10, 300])
    basic_info_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica', 10),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('ALIGN', (2, 0), (2, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0, colors.transparent),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
    ]))
    wrapper_table = Table([[basic_info_table]], colWidths=[400], hAlign='LEFT')
    wrapper_table.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('GRID', (0, 0), (-1, -1), 0, colors.transparent),
    ]))
    elements.append(wrapper_table)

    elements.append(Spacer(1, 5 * mm))

    # Tabel audit
    table_data = [["5R", "NO.", "IMPLEMENTASI", "YA", "TIDAK"]]
    scores = data.get('scores', {})
    for category, items in categories.items():
        for i, question in enumerate(items, 1):
            score_key = f"{category}_{i}"
            score = scores.get(score_key, -1)
            if i == 1:
                table_data.append([category, str(i), question, "✓" if score == 1 else "", "✓" if score == 0 else ""])
            else:
                table_data.append(["", str(i), question, "✓" if score == 1 else "", "✓" if score == 0 else ""])

    col_widths = [45, 20, 260, 80, 100]
    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica', 8),
        ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (2, 1), (2, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('SPAN', (0, 1), (0, 5)),
        ('SPAN', (0, 6), (0, 10)),
        ('SPAN', (0, 11), (0, 15)),
        ('SPAN', (0, 16), (0, 20)),
        ('SPAN', (0, 21), (0, 25)),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
    ]))
    elements.append(table)

    # Tanda tangan
    elements.append(Spacer(1, 1 * mm))
    signature_data = [
        [""],
        [f"Surabaya, {data.get('date', 'N/A')}"],
        [""],
        [""],
        [""],
        [data.get('auditor', 'N/A')]
    ]
    signature_table = Table(signature_data, colWidths=[150 * mm])
    signature_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica', 10),
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0, colors.transparent),
    ]))
    wrapper_signature_table = Table([[signature_table]], colWidths=[150 * mm], hAlign='RIGHT')
    wrapper_signature_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0, colors.transparent),
    ]))
    elements.append(wrapper_signature_table)

    # Gambar
    if images:
        elements.append(Spacer(1, 15 * mm))
        elements.append(Paragraph("Bukti Foto:", styles["Heading3"]))
        for img_path in images:
            try:
                img = Image(img_path, width=100 * mm, height=60 * mm)
                elements.append(img)
                elements.append(Spacer(1, 5 * mm))
            except Exception as e:
                elements.append(Paragraph(f"Gagal memuat gambar: {img_path} ({str(e)})", normal_style))

    # Buat PDF
    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes

class VideoTransformer(VideoTransformerBase):
    def __init__(self):
        self.snapshot = None

    def transform(self, frame):
        img = frame.to_ndarray(format="bgr24")
        self.snapshot = img
        return img

    def take_snapshot(self):
        return self.snapshot

def main():
    st.set_page_config(page_title="Audit 5R", layout="wide")
    
    # CSS untuk mengurangi jarak antara pertanyaan dan opsi
    st.markdown("""
        <style>
        .stRadio > div {
            margin-top: -50px !important;
        }
        .stRadio > label {
            margin-bottom: 5px !important;
        }
        .camera-label {
            font-size: 14px !important;
            margin-bottom: 10px !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.title("AUDIT 5R - DIVISI DESAIN")
    
    with st.expander("Formulir Audit", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            audit_date = st.date_input("Tanggal Audit", datetime.now())
            auditor = st.text_input("Auditor")
            dept = st.selectbox("Departemen", [
                "Integrasi", 
                "Basic Desain", 
                "Desain Struktur dan Perlengkapan Lambung",
                "Desain Perlengkapan Permesinan",
                "Desain Perlengkapan Listrik, Elektronika dan Senjata"
            ])
        
        with col2:
            biro = st.text_input("Biro")
            
            # Opsi unggah gambar dari file
            uploaded_files = st.file_uploader("Unggah Bukti Foto", accept_multiple_files=True, type=['png', 'jpg', 'jpeg'])
            
            # Opsi ambil foto dari kamera
            st.markdown('<p class="camera-label">Ambil Foto dari Kamera</p>', unsafe_allow_html=True)
            if 'show_camera' not in st.session_state:
                st.session_state['show_camera'] = False

            if st.button("Buka Kamera"):
                st.session_state['show_camera'] = True
                

            if st.session_state['show_camera']:
                ctx = webrtc_streamer(
                    key="example",
                    video_transformer_factory=VideoTransformer,
                    mode=WebRtcMode.SENDONLY,
                    async_processing=True
                )
                if ctx.video_transformer:
                    if st.button("Ambil Foto"):
                        snapshot = ctx.video_transformer.take_snapshot()
                        if snapshot is not None:
                            img_rgb = cv2.cvtColor(snapshot, cv2.COLOR_BGR2RGB)
                            img_pil = PILImage.fromarray(img_rgb)
                            path = f"camera_snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                            img_pil.save(path)
                            if 'camera_images' not in st.session_state:
                                st.session_state['camera_images'] = []
                            st.session_state['camera_images'].append(path)
                            st.session_state['show_camera'] = False  # Tutup kamera setelah ambil foto
                            st.success("Foto berhasil diambil!")
            
            # Tampilkan foto yang sudah diambil dari kamera
            if 'camera_images' in st.session_state and st.session_state['camera_images']:
                st.write("Foto dari Kamera:")
                cols = st.columns(4)  # Tampilkan 4 foto per baris
                for idx, img_path in enumerate(st.session_state['camera_images']):
                    with cols[idx % 4]:
                        st.image(img_path, width=150)
                        if st.button("Hapus", key=f"delete_{img_path}"):
                            st.session_state['camera_images'].remove(img_path)
                            if os.path.exists(img_path):
                                os.remove(img_path)
                            st.rerun()
            
            if st.button("Mulai Audit"):
                if not auditor or not dept or not biro:
                    st.error("Silakan lengkapi semua bidang!")
                else:
                    st.session_state['audit_started'] = True
                    st.session_state['form_data'] = {
                        'date': audit_date.strftime("%d-%m-%Y"),
                        'auditor': auditor,
                        'dept': dept,
                        'biro': biro
                    }
                    st.rerun()
    
    if st.session_state.get('audit_started', False):
        st.header("Formulir Penilaian 5R")
        
        scores = {}
        for category, questions in categories.items():
            st.subheader(category)
            
            for i, question in enumerate(questions, 1):
                st.write(f"{i}. {question}")
                score = st.radio(
                    "",
                    options=["Ya", "Tidak"],
                    key=f"{category}_{i}",
                    horizontal=True,
                    index=None
                )
                scores[f"{category}_{i}"] = 1 if score == "Ya" else 0 if score == "Tidak" else -1
        
        if st.button("Submit Audit"):
            if -1 in scores.values():
                st.error("Silakan isi semua penilaian!")
            else:
                st.session_state['scores'] = scores
                st.success("Audit berhasil disimpan!")
                
                # Kumpulkan semua gambar
                image_paths = []
                if uploaded_files:
                    for i, uploaded_file in enumerate(uploaded_files):
                        image = PILImage.open(uploaded_file).convert('RGB')  # Konversi ke RGB untuk mendukung PNG
                        path = f"temp_img_{i}.jpg"
                        image.save(path, 'JPEG')  # Simpan sebagai JPEG
                        image_paths.append(path)
                
                if 'camera_images' in st.session_state:
                    image_paths.extend(st.session_state['camera_images'])
                
                # Generate PDF
                pdf_data = {
                    **st.session_state['form_data'],
                    'scores': st.session_state['scores']
                }
                pdf = generate_pdf(pdf_data, image_paths)
                
                st.markdown(create_download_link(pdf, "Hasil_Audit_5R.pdf"), unsafe_allow_html=True)

                # Bersihkan file sementara
                for path in image_paths:
                    if "temp_img" in path and os.path.exists(path):
                        os.remove(path)

if __name__ == "__main__":
    if 'audit_started' not in st.session_state:
        st.session_state['audit_started'] = False
    if 'camera_images' not in st.session_state:
        st.session_state['camera_images'] = []
    main()

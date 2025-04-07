from .functions import *
from datetime import datetime
import os, json, re
import pandas as pd
CALENDAR_PATH = './materials/calendar_icon.png'
BACKGROUND_PATH = "./materials/cover.png"
SOURCE = None

def slide_cover(prs, TOPIC, RANGE_DATE, SAVE_FILE):

    print(f'> Generate Cover for: {TOPIC}\nfrom {RANGE_DATE}')
    # === INISIALISASI SLIDE ===
    prs.slide_width = Cm(33.867)
    prs.slide_height = Cm(19.05)
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    # === BACKGROUND TITIK-TITIK ===
    slide.shapes.add_picture(BACKGROUND_PATH, Cm(8.79), Cm(0), width=Cm(25.07), height=prs.slide_height)

    # Contoh penggunaan:
    date_range_box_cover(
        slide=slide,
        text=RANGE_DATE,
        left_cm=1.07,
        top_cm=3.8,
        icon_path=CALENDAR_PATH
    )

    # === TAMBAHKAN ELEMEN ===
    add_topic_box(slide, topic_text=TOPIC, left_cm=1.07, top_cm=2.13)
    add_text(slide, "MOSKAL", 1.07, 14.07, 8, 1, "Agency FB", 16, bold=True)
    add_text(slide, "AI-powered real-time media monitoring platform", 1.07, 14.8, 15, 1, "Calibri", 10.5, bold=True, color=(102, 102, 102))
    add_text(slide, f"© Moskal {datetime.now().year}, All rights reserved.", 1.07, 16.42, 14.2, 1, "Aptos Display", 8, bold=True, color=(140, 140, 140))

    print('------- Saved!!!')
    
def slide_summary_mentions(prs, TOPIC, RANGE_DATE, SAVE_FILE, page_number = 2, SOURCE = SOURCE):
    print('> Slide Summary of Mentions')
    
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # Blank slide

    # Tambahkan template untuk halaman ke-2
    add_slide_template(
        slide,
        topic=TOPIC,
        range_date=RANGE_DATE,
        page_num=page_number,
        total_pages=12,
        icon_path=CALENDAR_PATH
    )


    # Judul Section
    left = Cm(1)
    top = Cm(2.22)
    width = Cm(20)
    height = Cm(1)

    add_chart_title(slide, "Summary of mentions", left, top, width, height, Pt(18), 
                    "Arial", RGBColor(0, 0, 0), True, wrap=False, url=None)


    line_title(slide,Cm(1.23), Cm(3.14), Cm(4), Cm(0.07))


    # Posisi gambar summary chart
    list_images = [
        "volume_of_mentions.png",
        "social_media_reach.png",
        "non_social_media_reach.png",
        "positive.png",
        "negative.png"
    ]
    chart_images = []
    for i in list_images:
        chart_images.append(os.path.join(SOURCE,i))
    
    
    # Posisi koordinat (atur sesuai layout)
    positions = [
        (Cm(1.44), Cm(3.77)),
        (Cm(7.74), Cm(3.77)),
        (Cm(14.16), Cm(3.77)),
        (Cm(20.25), Cm(3.77)),
        (Cm(26.64), Cm(3.77)),
    ]

    for img_path, (x, y) in zip(chart_images, positions):
        slide.shapes.add_picture(img_path, x, y, height=Cm(5))

    # Tambahkan judul untuk chart kedua
    add_chart_title(slide, "Volume of mentions", Cm(1), Cm(8.96), Cm(20), Cm(1), Pt(18), 
                    "Arial", RGBColor(0, 0, 0), True, wrap=False, url=None)


    # Garis biru di bawah judul
    line_title(slide, Cm(1.23), Cm(10), Cm(4), Cm(0.07))


    # Tambahkan line chart (Volume of mentions trend)
    slide.shapes.add_picture(os.path.join(SOURCE,"Volume of mentions_trend.png"), Cm(1), Cm(10.3), width=Cm(32.22),height = Cm(7.94))


    print('------- Saved!!!')
    
def slide_reach_trend(prs, TOPIC, RANGE_DATE, SAVE_FILE, page_number = 3, SOURCE = SOURCE):
    print('> Generate Reach Trend')
    # Add slide
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    add_slide_template(
        slide,
        topic=TOPIC,
        range_date=RANGE_DATE,
        page_num=page_number,
        total_pages=12,
        icon_path=CALENDAR_PATH
    )


    # Tambahkan judul untuk chart kedua
    add_chart_title(slide, "Social media reach", Cm(1), Cm(2.25), Cm(15), Cm(1), Pt(18), 
                    "Arial", RGBColor(0, 0, 0), True, wrap=False, url=None)


    # Add underline for section title
    line_title(slide,Cm(1.23), Cm(3.14), Cm(4), Cm(0.07))


    # Add Social Media Reach Trend Chart
    slide.shapes.add_picture( os.path.join(SOURCE, "Social media reach_trend.png"), 
                             Cm(1), Cm(3.81), width=Cm(31.2), height=Cm(6.81))

    # Add next section title
    add_chart_title(slide, "Non-social media reach", Cm(1), Cm(10.69), Cm(20), Cm(1), Pt(18), 
                    "Arial", RGBColor(0, 0, 0), True, wrap=False, url=None)


    # Underline for second section
    line_title(slide, Cm(1.23), Cm(11.73), Cm(4), Cm(0.07))


    # Add Non-Social Media Reach Trend Chart
    slide.shapes.add_picture(os.path.join(SOURCE, "Non social media reach_trend.png"),
                             Cm(1), Cm(12.14), width=Cm(31.2),height = Cm(6.49))

    print('------- Saved!!!')
    
def slide_sentiment_trend(prs, TOPIC, RANGE_DATE, SAVE_FILE, page_number = 4, SOURCE = SOURCE):
    print('> Generate Sentiment Trend')
    # Add slide
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    add_slide_template(
        slide,
        topic=TOPIC,
        range_date=RANGE_DATE,
        page_num=page_number,
        total_pages=12,
        icon_path=CALENDAR_PATH
    )

    # Add section title
    add_chart_title(slide, "Positive mentions", Cm(1), Cm(2.25), Cm(15), Cm(1), Pt(18), 
                    "Arial", RGBColor(0, 0, 0), True, wrap=False, url=None)


    # Add underline for section title
    line_title(slide,Cm(1.23), Cm(3.14), Cm(4), Cm(0.07))


    # Add Social Media Reach Trend Chart
    slide.shapes.add_picture(os.path.join(SOURCE,"Positive_trend.png"),
                             Cm(1), Cm(3.81), width=Cm(31.2), height=Cm(6.81))


    # Add next section title
    add_chart_title(slide, "Negative mentions", Cm(1), Cm(10.69), Cm(20), Cm(1), Pt(18), 
                    "Arial", RGBColor(0, 0, 0), True, wrap=False, url=None)


    # Underline for second section
    line_title(slide, Cm(1.23), Cm(11.73), Cm(4), Cm(0.07))

    # Add Non-Social Media Reach Trend Chart
    slide.shapes.add_picture(os.path.join(SOURCE,"Negative_trend.png"),
                             Cm(1), Cm(12.14), width=Cm(31.2),height = Cm(6.49))

    print('------- Saved!!!')
      
def slide_topic_overview(prs, TOPIC, RANGE_DATE, SAVE_FILE, page_number = 5, SOURCE = SOURCE):
    print('> Generate topic overview')
    #read data
    data_topics = []
    with open(os.path.join(SOURCE,'topic_overview.json')) as f:
        for i in f:
            data_topics.append(json.loads(i))


    slide = prs.slides.add_slide(prs.slide_layouts[6])  # Blank slide

    add_slide_template(
        slide,
        topic=TOPIC,
        range_date=RANGE_DATE,
        page_num=2,
        total_pages=12,
        icon_path=CALENDAR_PATH
    )
    
    title = 'Top 5 Topics Overview'
    if len(data_topics)<5:
        title = "Topics Overview"
    
    add_chart_title(slide, title, Cm(1), Cm(2.22), Cm(20), Cm(1), 
                    Pt(18), "Arial", RGBColor(0, 0, 0), True)

    line_title(slide, Cm(1.23), Cm(3.14), Cm(4), Cm(0.07))

    # Ambil 5 topic teratas dari data_topics
    top_topics = data_topics[:5]

    # Buat data untuk tabel
    table_data = [["Topic name", "Description", "Mentions", "Reach", "Share of voice", "Sentiment share"]]

    for topic in top_topics:
        # Format sentiment share dengan warna
        sentiment_share = f"{topic['percentage_positive']}% positive\n{topic['percentage_negative']}% negative\n{topic['percentage_neutral']}% neutral"

        # Format share of voice sebagai persentase
        sov = f"{topic['share_of_voice']*100:.2f}%"

        # Tambahkan data ke table_data
        table_data.append([
            topic['unified_issue'], 
            topic['description'], 
            str(topic['total_issue']), 
            f"{topic['total_reach_score']:.1f}", 
            sov,
            sentiment_share
        ])

    # Buat tabel
    rows, cols = len(table_data), len(table_data[0])
    table_width = Cm(31.79)
    col_widths = [Cm(5.29), Cm(15.54), Cm(2.2), Cm(1.6), Cm(3.1), Cm(3.6)]

    # Posisikan tabel di bawah garis
    table_top = Cm(3.86)
    table = slide.shapes.add_table(rows, cols, Cm(1.23), table_top, table_width, Cm(20)).table

    # Atur lebar kolom
    for i in range(cols):
        table.columns[i].width = col_widths[i]

    # Atur tinggi baris
    row_height = Cm(1)  # Tinggi default
    for rh in table.rows:
        rh.height = row_height    

    # Header style
    header_fill = RGBColor(240, 240, 240)  # Light gray
    header_text_color = RGBColor(0, 0, 0)  # Black

    # Cell style for data rows
    cell_fill = RGBColor(255, 255, 255)  # White
    cell_text_color = RGBColor(0, 0, 0)  # Black

    # Apply styles and fill data
    for i in range(rows):
        for j in range(cols):
            cell = table.cell(i, j)

            # Set background color
            if i == 0:  # Header row
                cell.fill.solid()
                cell.fill.fore_color.rgb = header_fill
            else:
                if i % 2 == 0:  # Even rows (after header)
                    cell.fill.solid()
                    cell.fill.fore_color.rgb = RGBColor(245, 245, 245)  # Very light gray
                else:
                    cell.fill.solid()
                    cell.fill.fore_color.rgb = cell_fill

            # Add text
            text_frame = cell.text_frame
            text_frame.vertical_anchor = MSO_VERTICAL_ANCHOR.MIDDLE
            text_frame.word_wrap = True

            # Text formatting berbeda untuk kolom Topic name
            if j == 0 and i > 0:  # Kolom Topic name (bukan header)
                # Dapatkan referensi untuk topik ini
                topic_refs = top_topics[i-1].get('references', [])

                # Tambahkan judul topik
                p = text_frame.paragraphs[0]
                p.text = table_data[i][j]

                for run in p.runs:
                    run.font.size = Pt(10)
                    run.font.color.rgb = cell_text_color

                # Tambahkan spasi setelah judul
                p.space_after = Pt(6)

                # Tambahkan baris untuk ikon
                if topic_refs:
                    # Tambahkan paragraf baru untuk ikon
                    icon_p = text_frame.add_paragraph()

                    # Ambil hingga 3 referensi
                    for ref_idx, ref in enumerate(topic_refs[:3]):
                        channel = ref.get('channel', '')
                        link = ref.get('link_post', '')

                        if channel and link:
                            # Tambahkan ikon sebagai inline shape
                            # Untuk PowerPoint, kita tidak bisa langsung menambahkan ikon ke paragraf
                            # Kita perlu menambahkan ikon ke slide dan posisikan di atas atau di bawah sel

                            # Tambahkan teks placeholder untuk ikon
                            if ref_idx > 0:
                                icon_p.add_run().text = "  "  # Spasi antara ikon

                            icon_run = icon_p.add_run()
                            icon_run.text = channel.capitalize()
                            icon_run.font.size = Pt(8)
                            icon_run.font.color.rgb = RGBColor(0, 112, 192)  # Biru
                            icon_run.font.underline = True

                            # Tambahkan hyperlink
                            icon_run.hyperlink.address = link
            else:
                p = text_frame.paragraphs[0]
                p.text = table_data[i][j]

                # Text formatting
                for run in p.runs:
                    if i == 0:  # Header row
                        run.font.bold = True
                        run.font.size = Pt(12)
                        run.font.color.rgb = header_text_color
                    else:
                        run.font.size = Pt(10)
                        run.font.color.rgb = cell_text_color

            # Alignment
            if j in [2, 3, 4]:  # Numeric columns (Mentions, Reach, Share of voice)
                p.alignment = PP_ALIGN.CENTER
            elif j == 5:  # Sentiment share column with multiple lines
                p.alignment = PP_ALIGN.LEFT
            else:
                p.alignment = PP_ALIGN.LEFT

            # Special formatting for sentiment column
            if j == 5 and i > 0:
                lines = table_data[i][j].split('\n')
                p.text = ""  # Clear existing text

                for line_idx, line in enumerate(lines):
                    if line_idx > 0:
                        p = text_frame.add_paragraph()

                    if "positive" in line:
                        run = p.add_run()
                        run.text = line
                        run.font.name = "Arial"
                        run.font.size = Pt(10)
                        run.font.color.rgb = RGBColor(0, 176, 80)  # Green
                    elif "negative" in line:
                        run = p.add_run()
                        run.text = line
                        run.font.name = "Arial"
                        run.font.size = Pt(10)
                        run.font.color.rgb = RGBColor(255, 0, 0)  # Red
                    elif "neutral" in line:
                        run = p.add_run()
                        run.text = line
                        run.font.name = "Arial"
                        run.font.size = Pt(10)
                        run.font.color.rgb = RGBColor(128, 128, 128)  # Gray
                    else:
                        run = p.add_run()
                        run.text = line
                        run.font.name = "Arial"
                        run.font.size = Pt(10)

    # Tambahkan ikon sebagai shapes di luar tabel
    for i, topic in enumerate(top_topics):
        break
        topic_refs = topic.get('references', [])
        row_idx = i + 1  # Skip header row

        if topic_refs:
            # Dapatkan posisi sel untuk kolom Topic name
            cell = table.cell(row_idx, 0)

            # Dapatkan posisi untuk ikon di bawah teks topik
            cell_left = Cm(1.23)  # Sesuaikan dengan posisi tabel
            cell_top = table_top + (row_height * row_idx) + Cm(0.5)  # Di bawah teks topik

            # Tambahkan hingga 3 referensi sebagai ikon
            for ref_idx, ref in enumerate(topic_refs[:3]):
                channel = ref.get('channel', '')
                link = ref.get('link_post', '')

                if channel and link:
                    # Path ke ikon platform
                    icon_path = f"./materials/{channel}.png"

                    try:
                        # Posisi ikon di dalam sel
                        icon_left = cell_left + (ref_idx * Cm(0.8))  # Spasi antara ikon

                        # Tambahkan ikon sebagai picture
                        icon = slide.shapes.add_picture(
                            icon_path, 
                            icon_left, 
                            cell_top, 
                            width=Cm(0.6),  # Ukuran ikon
                            height=Cm(0.6)
                        )

                        # Tambahkan hyperlink ke gambar (requires advanced handling)
                        # Karena gambar tidak mendukung hyperlink secara langsung di python-pptx,
                        # kita perlu menggunakan XML hack atau alternatif lain

                        # Alternatif: Tambahkan textbox transparan di atas gambar dengan hyperlink
                        link_box = slide.shapes.add_textbox(
                            icon_left, 
                            cell_top, 
                            Cm(0.6), 
                            Cm(0.6)
                        )
                        link_frame = link_box.text_frame
                        link_p = link_frame.paragraphs[0]
                        link_run = link_p.add_run()
                        link_run.text = " "  # Spasi untuk hyperlink
                        link_run.hyperlink.address = link
                    except:
                        # Jika ikon tidak ditemukan, tambahkan teks sebagai gantinya
                        text_icon = slide.shapes.add_textbox(
                            icon_left, 
                            cell_top, 
                            Cm(0.6), 
                            Cm(0.6)
                        )
                        text_icon_frame = text_icon.text_frame
                        text_icon_p = text_icon_frame.paragraphs[0]
                        text_icon_run = text_icon_p.add_run()
                        text_icon_run.text = channel[0].upper()  # Gunakan huruf pertama
                        text_icon_run.font.size = Pt(8)
                        text_icon_run.hyperlink.address = link

    print('------- Saved!!!')
    
def create_kol(prs,DATA, TOPIC, RANGE_DATE, SAVE_FILE, page_number, title = 'Top 10 Key Opinion Leaders (1/2)' ):
    print("> Generate",title)
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # Blank slide

    add_slide_template(
        slide,
        topic=TOPIC,
        range_date=RANGE_DATE,
        page_num=page_number,
        total_pages=12,
        icon_path=CALENDAR_PATH
    )

    add_chart_title(slide, title, Cm(1), Cm(2.22), Cm(20), Cm(1), 
                    Pt(18), "Arial", RGBColor(0, 0, 0), True)

    line_title(slide, Cm(1.23), Cm(3.15), Cm(4), Cm(0.07))

    # Membuat data untuk tabel dari data_kol
    profiles_data = [["Profile name", "Mentions", "Reach", "Followers", "Actively discussing", "Sentiments", "Influence score"]]

    for kol in DATA:
        # Menghitung sentimen dalam persentase
        total_posts = kol['total_post']
        pos_pct = round((kol['total_positive'] / total_posts) * 100) if total_posts > 0 else 0
        neg_pct = round((kol['total_negative'] / total_posts) * 100) if total_posts > 0 else 0
        neu_pct = round((kol['total_neutral'] / total_posts) * 100) if total_posts > 0 else 0

        # Format sentimen
        sentiments = f"{pos_pct}% positive\n{neg_pct}% negative\n{neu_pct}% neutral"

        # Format followers dengan K untuk ribuan
        followers_display = 'N/A'
        if str(kol['followers']) != 'nan' and str(kol['followers']) != '<NA>':
            followers_num = float(kol['followers'])
            if followers_num >= 1000:
                followers_display = f"{followers_num/1000:.1f}K".replace('.0K', 'K')
            else:
                followers_display = str(int(followers_num))

        # Format profil
        platform = kol['channel'].capitalize()
        profile_name = f"{kol['username']}\n{kol['user_category']}\n{platform}.com"

        # Format issues yang didiskusikan
        issues = kol.get('issue', [])
        if not issues:
            issues = kol.get('unified_issues', [])

        discussing = "\n".join([f'• {issue}' for issue in issues[:3]])

        # Format influence score /10
        influence_score = f"{kol['influence_score']:.1f}/100"

        # Tambahkan data ke profiles_data
        profiles_data.append([
            profile_name,
            str(kol['total_post']),
            str(int(kol['reach_score'])),
            followers_display,
            discussing,
            sentiments,
            influence_score
        ])

    # Buat tabel
    rows, cols = len(profiles_data), len(profiles_data[0])
    table_width = Cm(31.79)
    col_widths = [Cm(4.32), Cm(2.73), Cm(2.07), Cm(3.28), Cm(11.6), Cm(3.3), Cm(4.33)]

    # Posisikan tabel di bawah garis
    table_top = Cm(3.86)
    table = slide.shapes.add_table(rows, cols, Cm(1.23), table_top, table_width, Cm(20)).table

    # Atur lebar kolom
    for i in range(cols):
        table.columns[i].width = col_widths[i]

    # Atur tinggi baris
    row_height = Cm(1.2)  # Tinggi default yang lebih tinggi karena konten aktif membahas panjang
    for rh in table.rows:
        rh.height = row_height    

    # Header style
    header_fill = RGBColor(240, 240, 240)  # Light gray
    header_text_color = RGBColor(0, 0, 0)  # Black

    # Cell style for data rows
    cell_fill = RGBColor(255, 255, 255)  # White
    cell_text_color = RGBColor(0, 0, 0)  # Black

    # Apply styles and fill data
    for i in range(rows):
        for j in range(cols):
            cell = table.cell(i, j)

            # Set background color
            if i == 0:  # Header row
                cell.fill.solid()
                cell.fill.fore_color.rgb = header_fill
            else:
                if i % 2 == 0:  # Even rows (after header)
                    cell.fill.solid()
                    cell.fill.fore_color.rgb = RGBColor(245, 245, 245)  # Very light gray
                else:
                    cell.fill.solid()
                    cell.fill.fore_color.rgb = cell_fill

            # Add text
            text_frame = cell.text_frame
            text_frame.vertical_anchor = MSO_VERTICAL_ANCHOR.MIDDLE
            text_frame.word_wrap = True

            # Special formatting for profile name column
            if j == 0 and i > 0:  # Profile name column (non-header)
                lines = profiles_data[i][j].split('\n')

                # Username (first line)
                p = text_frame.paragraphs[0]
                p.text = lines[0]  # Username

                for run in p.runs:
                    run.font.size = Pt(12)
                    run.font.bold = True
                    run.font.color.rgb = RGBColor(0, 112, 192)  # Blue

                # Account type (second line)
                if len(lines) > 1:
                    p2 = text_frame.add_paragraph()
                    p2.text = lines[1]  # Account type

                    for run in p2.runs:
                        run.font.size = Pt(12)
                        run.font.italic = True

                # Platform link (third line)
                if len(lines) > 2:
                    p3 = text_frame.add_paragraph()
                    p3.text = lines[2]  # Platform link

                    for run in p3.runs:
                        run.font.size = Pt(12)
                        run.font.color.rgb = RGBColor(0, 112, 192)  # Blue
                        platform = lines[2].lower()
                        print(platform)
                        if 'instagram' in platform:
                            link_user = f'https://www.instagram.com/{lines[0].strip("@ ")}/'
                        elif 'twitter' in platform:
                            link_user = f'https://x.com/{lines[0].strip("@ ")}/'
                        elif 'tiktok' in platform:
                            link_user = f'https://www.tiktok.com/{lines[0]}/'
                        elif 'youtube' in platform:
                            link_user = f'https://www.youtube.com/{lines[0]}/'
                        else:
                            link_user = f'https://{platform}'
                        print(link_user)
                        run.hyperlink.address = link_user

            # Special formatting for sentiment column
            elif j == 5 and i > 0:  # Sentiment column (non-header)
                lines = profiles_data[i][j].split('\n')
                p = text_frame.paragraphs[0]
                p.text = ""  # Clear existing text

                for line_idx, line in enumerate(lines):
                    if line_idx > 0:
                        p = text_frame.add_paragraph()
                    
                    
                    for sentiment in ['positive','negative','neutral']:
                        if sentiment in line:
                            run = p.add_run()
                            run.text = line
                            run.font.name = "Arial"
                            run.font.size = Pt(12)
                            if "positive" in line:
                                run.font.color.rgb = RGBColor(0, 176, 80)  # Green
                            elif "negative" in line:
                                run.font.color.rgb = RGBColor(255, 0, 0)  # Red
                            elif "neutral" in line:
                                run.font.color.rgb = RGBColor(128, 128, 128)  # Gray                            
                 
                            break
                   

            # Default formatting for other cells
            else:
                p = text_frame.paragraphs[0]
                p.text = profiles_data[i][j]

                # Text formatting
                for run in p.runs:
                    if i == 0:  # Header row
                        run.font.bold = True
                        run.font.size = Pt(14)
                        run.font.name = "Arial"
                        run.font.color.rgb = header_text_color
                    else:
                        run.font.size = Pt(12)
                        run.font.name = "Arial"
                        run.font.color.rgb = cell_text_color

            # Alignment
            if j in [1, 2, 3, 6]:  # Numeric columns (Mentions, Reach, Followers, Influence score)
                p.alignment = PP_ALIGN.CENTER
            else:
                p.alignment = PP_ALIGN.LEFT

    print('------- Saved!!!')

def slide_kol(prs, TOPIC, RANGE_DATE, SAVE_FILE, page_number = 3, SOURCE = SOURCE):
    data_kol = []
    with open(os.path.join(SOURCE,'kol.json')) as f:
        for i in f:
            data_kol.append(json.loads(i))
    
    create_kol(prs,data_kol[:5],TOPIC, RANGE_DATE,
               SAVE_FILE,page_number, 'Top 10 Key Opinion Leaders (1/2)')
    create_kol(prs,data_kol[5:10],TOPIC, RANGE_DATE,
               SAVE_FILE,page_number+1, 'Top 10 Key Opinion Leaders (2/2)')
    
def slide_presence_score(prs, TOPIC, RANGE_DATE, SAVE_FILE, page_number = 3, SOURCE = SOURCE):
    print("> Generate Presence Score")
    with open(os.path.join(SOURCE,'presence_score_analysis.json')) as f:
        data_analysis = json.load(f)
    
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    
    add_slide_template(
        slide,
        topic=TOPIC,
        range_date=RANGE_DATE,
        page_num=page_number,
        total_pages=12,
        icon_path=CALENDAR_PATH
    )

    # Tambahkan judul
    add_chart_title(slide, "Presence score", Cm(1),  Cm(2.25), Cm(15), Cm(1), Pt(18), 
                    "Arial", RGBColor(0, 0, 0), True, wrap=False, url=None)


    # Add underline for section title
    line_title(slide,Cm(1.23), Cm(3.14), Cm(4), Cm(0.07))


    # Tambahkan gambar donut
    slide.shapes.add_picture(os.path.join(SOURCE,"presence_score_donut.png"),
                             Cm(1), Cm(3.28), Cm(7.25), Cm(7.86))

    
    # Tambahkan chart presence trend
    slide.shapes.add_picture(os.path.join(SOURCE,"presence_trend.png"),
                             Cm(9), Cm(3.28), Cm(24.14), Cm(7.9))


    # Parameter
    text_analysis = data_analysis['analysis']
    
    quote_left_path = "./materials/quote_left.png"
    quote_right_path = "./materials/quote_right.png"

    # Shape teks dengan border
    left = Cm(1.93)
    top = Cm(12.24)
    width = Cm(30)
    height = Cm(6)

    textbox = slide.shapes.add_shape(
        MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE,
        left, top, width, height
    )

    line = textbox.line
    line.color.rgb = RGBColor(0, 102, 204)
    line.width = Pt(1.5)
    line.dash_style = MSO_LINE_DASH_STYLE.ROUND_DOT
    textbox.fill.background()

    tf = textbox.text_frame
    p = tf.paragraphs[0]
    run = p.add_run()
    run.text = text_analysis
    font = run.font
    font.name = "Arial"
    font.size = Pt(14)
    font.color.rgb = RGBColor(102, 102, 102)


    # Kutip kiri dan kanan
    slide.shapes.add_picture(quote_left_path, Cm(1.67), Cm(11.95),width=Cm(0.66), height=Cm(0.47))
    slide.shapes.add_picture(quote_right_path, Cm(31.7), Cm(17.86), width=Cm(0.66), height=Cm(0.47))

    print('------- Saved!!!')
    
def slide_sentiment_analysis(prs, TOPIC, RANGE_DATE, SAVE_FILE, page_number = 3, SOURCE = SOURCE):
    print("> Generate Sentiment Analysis")
    
    with open(os.path.join(SOURCE,'sentiment_analysis.json')) as f:
        data_analysis = json.load(f)
    
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    add_slide_template(
        slide,
        topic=TOPIC,
        range_date=RANGE_DATE,
        page_num=page_number,
        total_pages=12,
        icon_path=CALENDAR_PATH
    )

    # Tambahkan judul
    add_chart_title(slide, "Sentiment Analysis", Cm(1), Cm(1.64), Cm(15), Cm(1), Pt(18), 
                    "Arial", RGBColor(0, 0, 0), True, wrap=False, url=None)

    # Add underline for section title
    line_title(slide, Cm(1.23), Cm(2.63), Cm(4), Cm(0.07))


    # ---------- Tambahkan Gambar Donut dan Bar Chart ----------
    slide.shapes.add_picture(os.path.join(SOURCE,"sentiment_breakdown.png"), 
                             Cm(2.44), Cm(2.93), Cm(12), Cm(11.66))

    # Tambahkan judul
    add_chart_title(slide, "Sentiment by Categories", Cm(17.12), Cm(1.64), Cm(15), Cm(1), Pt(18), 
                    "Arial", RGBColor(0, 0, 0), True, wrap=False, url=None)


    # Add underline for section title
    line_title(slide, Cm(17.38), Cm(2.63), Cm(4), Cm(0.07))

    slide.shapes.add_picture(os.path.join(SOURCE,"sentiment_by_categories.png"), 
                             Cm(17.3), Cm(2.91), Cm(15.94), Cm(7.86))

    # ---------- Tambahkan Subjudul ----------
    add_chart_title(slide, "Summarize by Sentiment", Cm(1), Cm(10.69), Cm(15), Cm(1), Pt(18), 
                    "Arial", RGBColor(0, 0, 0), True, wrap=False, url=None)

    # Add underline for section title
    line_title(slide, Cm(1.23), Cm(11.66), Cm(4), Cm(0.07))

    # ---------- Box Positive Sentiment ----------
    positive_box = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, Cm(0.97), Cm(12.34), Cm(15.8), Cm(5.95)
    )
    positive_box.fill.solid()
    positive_box.fill.fore_color.rgb = RGBColor(235, 255, 245)
    positive_box.line.fill.background()

    # Kutipan Positif
    quote_positive = slide.shapes.add_textbox(Cm(2.9), Cm(13.16), Cm(13.5), Cm(3.25))
    quote_positive_tf = quote_positive.text_frame
    quote_positive_tf.word_wrap = True
    p = quote_positive_tf.paragraphs[0]
    run = p.add_run()
    run.text = data_analysis["positive_summarize"]
    font = run.font
    font.name = "Arial"
    font.size = Pt(14)
    font.color.rgb = RGBColor(0, 102, 51)  # hijau gelap

    slide.shapes.add_picture("./materials/smile.png", Cm(1.4), Cm(13.37),width = Cm(1), height=Cm(1))
    slide.shapes.add_picture("./materials/quote_smile.png", Cm(1.37), Cm(12.37),width = Cm(0.64), height=Cm(0.46))
    
    
    # ---------- Box Negative Sentiment ----------
    negative_box = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, Cm(17.19), Cm(12.34), Cm(15.8), Cm(5.95)
    )
    negative_box.fill.solid()
    negative_box.fill.fore_color.rgb = RGBColor(255, 240, 240)
    negative_box.line.fill.background()

    # Kutipan Negatif
    quote_negative = slide.shapes.add_textbox(Cm(19.41), Cm(13.16), Cm(13.5), Cm(3.25))
    quote_negative_tf = quote_negative.text_frame
    quote_negative_tf.word_wrap = True
    p = quote_negative_tf.paragraphs[0]
    run = p.add_run()
    run.text = data_analysis["negative_summarize"]
    font = run.font
    font.name = "Arial"
    font.size = Pt(14)
    font.color.rgb = RGBColor(204, 0, 0)  # merah tua

    slide.shapes.add_picture("./materials/sad.png", Cm(17.96), Cm(13.37),width = Cm(1), height=Cm(1))
    slide.shapes.add_picture("./materials/quote_sad.png", Cm(17.54), Cm(12.37),width = Cm(0.64), height=Cm(0.46))

    # ---------- Simpan ----------

    print('------- Saved!!!')
    
def slide_sentiment_context(prs, TOPIC, RANGE_DATE, SAVE_FILE, page_number = 3, SOURCE = SOURCE):
    print("> Generate Sentiment Context")
    # Load file PPT yang sudah ada
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    
    add_slide_template(
        slide,
        topic=TOPIC,
        range_date=RANGE_DATE,
        page_num=page_number,
        total_pages=12,
        icon_path=CALENDAR_PATH
    )

    #--------------------------------------------------------
    # Tambahkan judul
    left = Cm(1)
    top = Cm(1.64)
    width = Cm(15)
    height = Cm(1)
    add_chart_title(slide, "Sentiment Distribution by Entity", left, top, width, height, Pt(18), 
                    "Arial", RGBColor(0, 0, 0), True, wrap=False, url=None)


    # Add underline for section title
    line_title(slide, Cm(1.23), Cm(2.63), Cm(4), Cm(0.07))

    # Tambahkan gambar chart (gambar sudah disiapkan)
    slide.shapes.add_picture(os.path.join(SOURCE,"sentiment_distribution_by_entity.png"),
                             Cm(1.23), Cm(3.1), Cm(20.09), Cm(13.66))

    #--------------------------------------------------------
    # Tambahkan judul
    left = Cm(22.01)
    top = Cm(1.64)
    width = Cm(15)
    height = Cm(1)
    add_chart_title(slide,"Context of discussion", left, top, width, height, Pt(18), 
                    "Arial", RGBColor(0, 0, 0), True, wrap=False, url=None)



    # Add underline for section title
    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Cm(22.27), Cm(2.63), Cm(4), Cm(0.07))
    line.fill.solid()
    line.fill.fore_color.rgb = RGBColor(0, 112, 255)
    line.line.fill.background()

    # Tambahkan gambar chart (gambar sudah disiapkan)
    slide.shapes.add_picture(os.path.join(SOURCE,"word_sentiment_wordcloud.png"),
                             Cm(22.6), Cm(3.15),Cm(10.42), Cm(6.18))

    #--------------------------------------------------------
    # Tambahkan judul

    add_chart_title(slide,"Hashtag Cloud by Sentiment", Cm(22.01), Cm(9.44), Cm(15), Cm(1), Pt(18), 
                    "Arial", RGBColor(0, 0, 0), True, wrap=False, url=None)

    # Add underline for section title
    line_title(slide, Cm(22.27), Cm(10.44), Cm(4), Cm(0.07))

    # Tambahkan gambar chart (gambar sudah disiapkan)
    slide.shapes.add_picture(os.path.join(SOURCE,"hashtag_sentiment_wordcloud.png"), 
                             Cm(22.6), Cm(10.86),width = Cm(10.42), height=Cm(6.18))



    print('------- Saved!!!')

def slide_popular_mentions(prs, TOPIC, RANGE_DATE, SAVE_FILE, page_number = 3, SOURCE = SOURCE):
    print("> Generate Popular Mentions")
    popular_mentions = pd.read_csv(os.path.join(SOURCE,'popular_mentions.csv'))
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # Blank slide
    
    add_slide_template(
        slide,
        topic=TOPIC,
        range_date=RANGE_DATE,
        page_num=page_number,
        total_pages=12,
        icon_path=CALENDAR_PATH
    )


    add_chart_title(slide, 'Social Media Mentions', Cm(1),Cm(2.22),Cm(20),Cm(1), 
                    Pt(18), "Arial",RGBColor(0, 0, 0), True)

    line_title(slide,Cm(1.23), Cm(3.14), Cm(4), Cm(0.07))

    #----- picture-----
    left = Cm(1.37)
    top = Cm(4.22)
    width = Cm(1.19)
    height = Cm(1.19)
    p2p = Cm(1.51)

    #----- username -----
    left_username = Cm(2.58)
    top_username = Cm(4.14)
    width_username = Cm(3.85)
    height_username = Cm(0.77)
    p2p_username = Cm(1.98)

    #----- datetime -----
    left_date = Cm(13.35)
    top_date = Cm(4.14)
    width_date = Cm(2.8)
    height_date = Cm(0.73)
    p2p_date = Cm(1.98)

    #----- caption -----
    left_caption = Cm(2.58)
    top_caption = Cm(4.8)
    width_caption = Cm(13.51)
    height_caption = Cm(1.67)
    p2p_caption = Cm(1.05)


    for _,i in popular_mentions[popular_mentions['channel']!='news'].reset_index()[:5].iterrows():
        channel = i['channel']
        caption = re.sub(r'\s+',' ',i['post_caption'])


        if len(caption)>190:
            caption = caption[:170]+' ...'

        idx = _
        slide.shapes.add_picture(f"./materials/{channel}.png",left ,top + height*idx + p2p*idx, width, height)

        add_chart_title(slide, i['username'], left_username, top_username + height_username*idx + p2p_username*idx,
                        width_username, height_username, 
                        Pt(14), "Arial",RGBColor(0, 0, 0), True)   

        add_chart_title(slide, i['post_created_at'].split()[0].split('T')[0], left_date, top_date + height_date*idx + p2p_date*idx,
                        width_date, height_date, 
                        Pt(11), "Arial",RGBColor(0, 0, 0), False)    

        add_chart_title(slide, caption, left_caption, top_caption + height_caption*idx + p2p_caption*idx,
                        width_caption, height_caption, 
                        Pt(11), "Arial",RGBColor(0, 0, 0), False, True)    

        add_chart_title(slide, 'view post', Cm(11.49), top_date + height_date*idx + p2p_date*idx,
                        width_date, height_date, 
                        Pt(11), "Arial",RGBColor(0, 0, 0), False, url = i['link_post'])    

    add_chart_title(slide, 'News Mentions', Cm(17.49),Cm(2.22),Cm(20),Cm(1), 
                    Pt(18), "Arial",RGBColor(0, 0, 0), True)

    line_title(slide,Cm(17.71), Cm(3.14), Cm(4), Cm(0.07))

    for _,i in popular_mentions[popular_mentions['channel']=='news'].reset_index()[:5].iterrows():
        channel = i['channel']
        caption = re.sub(r'\s+',' ',i['post_caption'])

        if len(caption)>190:
            caption = caption[:170]+' ...'

        idx = _
        slide.shapes.add_picture(f"./materials/{channel}.png", Cm(17.59) ,top + Cm(1.02)*idx + Cm(1.85)*idx, Cm(1.37), Cm(1.02))

        add_chart_title(slide, i['username'],  Cm(19.02), top_username + height_username*idx + p2p_username*idx,
                        width_username, height_username, 
                        Pt(14), "Arial",RGBColor(0, 0, 0), True)   

        add_chart_title(slide, i['post_created_at'].split()[0].split('T')[0],  Cm(29.77), top_date + height_date*idx + p2p_date*idx,
                        width_date, height_date, 
                        Pt(11), "Arial",RGBColor(0, 0, 0), False)    

        add_chart_title(slide, caption, Cm(19.02), top_caption + height_caption*idx + p2p_caption*idx,
                        width_caption, height_caption, 
                        Pt(11), "Arial",RGBColor(0, 0, 0), False, True)    

        add_chart_title(slide, 'view post', Cm(27.87), top_date + height_date*idx + p2p_date*idx,
                        width_date, height_date, 
                        Pt(11), "Arial",RGBColor(0, 0, 0), False, url = i['link_post'])    

    print('------- Saved!!!')

def slide_recommendations(prs, TOPIC, RANGE_DATE, SAVE_FILE, page_number = 3, SOURCE = SOURCE):
    print("> Generate Recommendations")
    with open(os.path.join(SOURCE,'recommendations.json')) as f:
        recommendations = json.load(f)
            
    # Gunakan layout blank
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_slide_template(
        slide,
        topic=TOPIC,
        range_date=RANGE_DATE,
        page_num=page_number,
        total_pages=12,
        icon_path=CALENDAR_PATH
    )

    # Tambahkan judul
    add_chart_title(slide, "Recommendations", Cm(1), Cm(1.64), Cm(15), Cm(1), 
                    Pt(18), "Arial",RGBColor(0, 0, 0), True)


    # Add underline for section title
    line_title(slide, Cm(1.23), Cm(2.63), Cm(4), Cm(0.07))

    # Buat text box baru di bawah line untuk recommendations
    content_box = slide.shapes.add_textbox(Cm(1), Cm(2.32), Cm(30.93) , Cm(13) )
    text_frame = content_box.text_frame
    text_frame.word_wrap = True

    def text_run(title_p, text, size, color):
        first_run = title_p.add_run()
        first_run.text = text
        first_run.font.bold = True
        first_run.font.size = size
        first_run.font.color.rgb = color  # #0053c0        
    
    
    # Add each recommendation section
    for i, item in enumerate(recommendations):
        # Add the recommendation title dengan 2 warna berbeda
        title_p = text_frame.add_paragraph()

        # Membagi judul pada tanda ":"
        if ":" in item['title']:
            title_parts = item['title'].split(":", 1)

            # Tambahkan nomor dan bagian sebelum tanda ":"
            text_run(title_p, f"{i+1}. {title_parts[0]}:",  Pt(14), RGBColor(0, 83, 192) )
            
            # Tambahkan bagian setelah tanda ":"
            text_run(title_p, f"{title_parts[1]}",  Pt(14), RGBColor(89, 89, 89))

        else:
            # Jika tidak ada ":", gunakan format asli
            text_run(title_p, f"{i+1}. {item['title']}", Pt(14), RGBColor(0, 83, 192))

        title_p.level = 0

        # Add each action as a bullet point
        for action in item['actions']:
            action_p = text_frame.add_paragraph()
            action_p.text = f"• {action.split('.')[0]}"
            action_p.level = 1
            action_p.font.size = Pt(12)

        action_p = text_frame.add_paragraph()
        
    prs.save(SAVE_FILE)
    print('------- Saved!!!')
from utils.list_of_mentions import get_filtered_mentions
from utils.gemini import call_gemini
import pandas as pd
import os, json, re

def generate_popular_mentions(MAIN_TOPIC,KEYWORDS,START_DATE,END_DATE, SAVE_PATH = 'REPORT'):
    # Mendapatkan mentions dengan filter
    data_news = get_filtered_mentions(
        keywords=KEYWORDS,
        start_date=START_DATE,
        end_date=END_DATE,
        source=['channel', 'username', 'link_post', 'post_created_at', 
              'post_caption', 'engagement_rate'],
        sort_type='popular',
        page=1,
        page_size=30,
        channels = ["news"]
    )

    data_sosmed = get_filtered_mentions(
        keywords=KEYWORDS,
        start_date=START_DATE,
        end_date=END_DATE,
        source=['channel', 'username', 'link_post', 'post_created_at', 'likes', 'views',
              'shares', 'reposts', 'comments', 'replies', 'votes', 'favorites',
              'post_caption', 'engagement_rate'],
        sort_type='popular',
        page=1,
        page_size=50,
        channels = ['reddit','youtube','linkedin','twitter',
            'tiktok','instagram','facebook','threads']
    )

    prompt = f"""Anda Adalah Media Social Analyst Expert yang sedang menganalisis topic tentang "{MAIN_TOPIC}"
    Saya memberikan dua daftar berikut: satu berisi berita dan satu berisi post dari sosial media. 
    Anda diminta untuk memilih 5 entri paling relevan dan penting dari setiap kategori. 
    Pilih berdasarkan **keberlanjutan topik**, **relevansi untuk tren saat ini**, dan **pengaruh** yang mungkin dimiliki setiap post. 
    Hasilnya adalah **5 berita dan 5 post sosial media** yang paling penting dan harus diperhatikan.

    ### List News
    {[{"link_post":i['link_post'],'caption':i['post_caption']} for i in data_news['data']]}

    ### List Social Media
    {[{"link_post":i['link_post'],'caption':i['post_caption']} for i in data_sosmed['data']]}


    ### Output dalam Format JSON ###
    [
        {{
        "kind": <"news / sosmed">,
        "link_post": link_post
        }},
        {{
        "kind": <"news / sosmed">,
        "link_post": link_post
        }}
    ]

    #### NOTE ####
    - hanya 5 post yang dipilih per kategori
    - tidak perlu memberikan reason apa apa
    """

    result = call_gemini(prompt)

    data_pick = json.loads(re.findall(r'\[.*\]',result, flags = re.I|re.S)[0])
    df_news = pd.DataFrame(data_pick).merge(pd.DataFrame(data_news['data']), on = 'link_post')
    df_sosmed = pd.DataFrame(data_pick).merge(pd.DataFrame(data_sosmed['data']), on = 'link_post')

    popular_mentions = pd.concat([df_news,df_sosmed])
    
    popular_mentions.to_csv(os.path.join(SAVE_PATH,'popular_mentions.csv'),index = False)
  
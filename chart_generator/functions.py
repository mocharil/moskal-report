from utils.gemini import call_gemini
import matplotlib
matplotlib.use('Agg') 
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import re, os, json, io
import matplotlib.pyplot as plt
from scipy.interpolate import make_interp_spline
from matplotlib.dates import DateFormatter
from sklearn.preprocessing import MinMaxScaler
import matplotlib.patches as patches
from wordcloud import WordCloud
from PIL import Image
import matplotlib.lines as mlines

def kurangi_tanggal(tanggal: str, selisih_hari: int) -> str:
    """
    Mengurangi tanggal dengan sejumlah hari tertentu.

    Args:
        tanggal (str): Tanggal dalam format 'YYYY-MM-DD'
        selisih_hari (int): Jumlah hari yang akan dikurangkan

    Returns:
        str: Tanggal hasil pengurangan dalam format 'YYYY-MM-DD'
    """
    tgl_obj = datetime.strptime(tanggal, "%Y-%m-%d")
    hasil = tgl_obj - timedelta(days=selisih_hari)
    return hasil.strftime("%Y-%m-%d")

def range_date_count(tanggal1: str, tanggal2: str) -> int:
    """
    Menghitung jarak (dalam hari) antara dua tanggal dalam format YYYY-MM-DD.

    Args:
        tanggal1 (str): Tanggal pertama, format 'YYYY-MM-DD'
        tanggal2 (str): Tanggal kedua, format 'YYYY-MM-DD'

    Returns:
        int: Selisih hari antara kedua tanggal
    """
    tgl1 = datetime.strptime(tanggal1, "%Y-%m-%d")
    tgl2 = datetime.strptime(tanggal2, "%Y-%m-%d")
    selisih = abs((tgl2 - tgl1).days)
    return selisih

def generate_keywords(TOPIC, time_period="current"):
    """
    Generate relevant keywords related to a topic for a specific time period.
    
    Parameters:
    -----------
    TOPIC : str
        The main keyword or topic to generate related keywords for
    time_period : str, default="current"
        The specific time period to focus on (e.g., "2023", "2020-2022", "current")
        
    Returns:
    --------
    list
        A list of related keywords
    """
    prompt = f"""You are an expert in social media intelligence and keyword research.
    Given a main keyword, generate a concise and highly relevant list of related keywords or phrases that are commonly used on social media to refer to or discuss the given keyword.
    Include only terms that are directly relevant and closely associated with the keyword during the {time_period} time period.

    **Specifically, you should include**:
    - Full names (for people)
    - Current or former positions or roles (e.g., "former Minister of Defense", "President of Indonesia")
    - Organizational affiliations (e.g., "Gerindra", "Partai Politik")
    - Expanded versions of acronyms (e.g., "KADIN" → "Kamar Dagang dan Industri Indonesia")
    - Names of public figures currently associated with institutions (e.g., chairperson, CEO)
    - Nicknames or popular social media references
    - Terms specifically relevant to the {time_period} time period
    - Historical references if applicable to the {time_period} time period

    ** Important Rules **:
    - Do not include unrelated, vague, or generic terms
    - Return a maximum of 15 keywords
    - The output must be a Python-readable list of strings
    - No explanations or extra text—just the list
    - Focus specifically on terms relevant to the {time_period} time period

    Example input: "Prabowo", time period: "2023-2024"
    Example output: ["Prabowo Subianto", "Presiden RI", "Menteri Pertahanan", "Ketua Umum Partai Gerindra", "Capres 2024", "Pak Prabowo", "Gerindra"]
    
    Now, generate related keywords for the following main keyword:
    "{TOPIC}"
    
    Time period: {time_period}
    Output only the Python list. Do not explain anything."""
    
    response = call_gemini(prompt)
    
    try:
        # More robust pattern matching to extract the list
        match = re.findall(r'\[.*?\]', response, re.DOTALL)
        if match:
            KEYWORDS = eval(match[0])
        else:
            # Fallback if regex doesn't find anything
            KEYWORDS = eval(response.strip())
    except Exception as e:
        print(f"Error parsing response: {e}")
        print(f"Raw response: {response}")
        # Fallback to empty list or basic parsing
        KEYWORDS = []
        # Try to extract anything that looks like a list item
        items = re.findall(r'"([^"]*)"', response)
        if items:
            KEYWORDS = items
    
    return KEYWORDS


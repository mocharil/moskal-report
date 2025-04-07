from google.cloud import bigquery
import pandas as pd
from google.oauth2 import service_account
import uuid
from datetime import datetime
from google.cloud import storage
import os
from google.api_core.exceptions import BadRequest



class About_BQ:
    def __init__(self, project_id: str, credentials_loc: str):
        """
        Inisialisasi koneksi ke BigQuery.
        
        :param project_id: ID proyek Google Cloud.
        :param credentials_loc: Path ke file kredensial JSON.
        """
        self.project_id = project_id
        self.credentials = service_account.Credentials.from_service_account_file(credentials_loc)
        self.client = bigquery.Client(credentials=self.credentials, project=self.project_id)

    def to_pull_data(self, query: str) -> pd.DataFrame:
        """
        Menjalankan query dan mengambil data dari BigQuery sebagai Pandas DataFrame.

        :param query: Query SQL yang akan dijalankan di BigQuery.
        :return: DataFrame hasil query.
        """
        try:
            print("⏳ Menjalankan query ke BigQuery...")
            query_job = self.client.query(query)  # Eksekusi query
            result_df = query_job.to_dataframe()  # Konversi hasil ke DataFrame
            print(f"✅ Query selesai! {len(result_df)} baris data diambil.")
            return result_df
        except Exception as e:
            print(f"❌ Terjadi kesalahan saat mengambil data: {str(e)}")
            return pd.DataFrame()  # Kembalikan DataFrame kosong jika terjadi error    
    
def format_range_date(start_date: str, end_date: str) -> str:
    """
    Mengubah dua tanggal (format YYYY-MM-DD) menjadi format 'DD Mon YYYY – DD Mon YYYY'

    Args:
        start_date (str): Tanggal awal, format 'YYYY-MM-DD'
        end_date (str): Tanggal akhir, format 'YYYY-MM-DD'

    Returns:
        str: Tanggal dalam format 'DD Mon YYYY – DD Mon YYYY'
    """
    tgl_awal = datetime.strptime(start_date, "%Y-%m-%d")
    tgl_akhir = datetime.strptime(end_date, "%Y-%m-%d")
    
    format_awal = tgl_awal.strftime("%d %b %Y")
    format_akhir = tgl_akhir.strftime("%d %b %Y")
    
    return f"{format_awal} – {format_akhir}"

def upload_and_get_public_url(
    local_file_path: str,
    credentials_json_path: str,
    destination_blob_name: str = None,
    project_id: str = "inlaid-sentinel-444404-f8",
    bucket_name: str = "auto_report"
):
    # Inisialisasi client storage dengan kredensial JSON
    storage_client = storage.Client.from_service_account_json(
        credentials_json_path,
        project=project_id
    )
    
    # Dapatkan referensi bucket
    bucket = storage_client.bucket(bucket_name)
    
    # Jika destination_blob_name tidak diberikan, gunakan nama file asli
    if destination_blob_name is None:
        destination_blob_name = os.path.basename(local_file_path)
    
    # Dapatkan referensi blob
    blob = bucket.blob(destination_blob_name)
    
    # Upload file
    blob.upload_from_filename(local_file_path)
    
    # Tentukan content-type yang sesuai (opsional)
    content_type = None
    if local_file_path.endswith('.pdf'):
        content_type = 'application/pdf'
    elif local_file_path.endswith('.pptx'):
        content_type = 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
    elif local_file_path.endswith('.docx'):
        content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    
    if content_type:
        blob.content_type = content_type
        blob.patch()
    
    # Dapatkan URL publik (ini TIDAK akan berfungsi kecuali bucket dibuat publik)
    public_url = f"https://storage.googleapis.com/{bucket_name}/{destination_blob_name}"
    
    # Generate signed URL (URL yang bisa diakses untuk jangka waktu terbatas)
    import datetime
    signed_url = blob.generate_signed_url(
        version="v4",
        expiration=datetime.timedelta(days=7),  # URL valid selama 7 hari
        method="GET"
    )
    
    print(f"File {local_file_path} berhasil diupload")
    print(f"Public URL (memerlukan IAM bucket-level access): {public_url}")
    print(f"Signed URL (dapat diakses selama 7 hari): {signed_url}")
    
    return {
        "public_url": public_url,
        "signed_url": signed_url
    }

